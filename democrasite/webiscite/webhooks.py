"""Views for processing webhooks.

Each service that sends webhooks should have its own function-based view."""

import hmac
import json
from logging import getLogger
from typing import TYPE_CHECKING
from typing import Any

import requests
from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.http import request
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Bill
from .models import PullRequest

if TYPE_CHECKING:
    from collections.abc import Callable

logger = getLogger(__name__)


class PullRequestHandler:
    """Handle pull requests from GitHub webhooks"""

    def __call__(self, payload: dict) -> HttpResponse:
        """Handle a pull request from a GitHub webhook

        Args:
            payload: The parsed JSON object representing the pull request

        Returns:
            An object containing the primary keys of the pull request and bill affected,
            if applicable
        """
        handler: Callable[
            [dict[str, Any]], tuple[PullRequest | None, Bill | None]
        ] | None
        handler = getattr(self, payload["action"], None)
        if handler is None:
            return HttpResponseBadRequest(f"Unsupported action: {payload['action']}")
        pull_request, bill = handler(payload["pull_request"])
        return self.get_response(payload["action"], pull_request, bill)

    def get_response(
        self, action: str, pull_request: PullRequest | None, bill: Bill | None
    ) -> JsonResponse:
        body: dict[str, str | int] = {"action": action}
        if pull_request is not None:
            body["pull_request"] = pull_request.number
        if bill is not None:
            body["bill"] = bill.id

        return JsonResponse(body)

    def reopened(self, pr: dict[str, Any]) -> tuple[PullRequest, Bill | None]:
        return self.opened(pr)

    def opened(self, pr: dict[str, Any]) -> tuple[PullRequest, Bill | None]:
        """Create a :class:`~democrasite.webiscite.models.PullRequest` and, if the
        creator has an account,
        :class:`~democrasite.webiscite.models.Bill` instance from a pull request

        Args:
            pr: The parsed JSON object representing the pull request

        Returns:
            A tuple containing the pull request and bill, if applicable
        """
        return Bill.create_from_pr(pr)

    def closed(self, pr: dict[str, Any]) -> tuple[PullRequest | None, Bill | None]:
        """Disables the open bill associated with the pull request

        Args:
            pr: The parsed JSON object representing the pull request
        """
        try:
            pull_request = PullRequest.objects.get(number=pr["number"])
        except PullRequest.DoesNotExist:
            logger.warning("PR %s: Not closed (no pull request found)", pr["number"])
            return (None, None)

        bill = pull_request.close()
        return (pull_request, bill)


@method_decorator(csrf_exempt, name="dispatch")
class GithubWebhookView(View):
    """View for GitHub webhook alerts

    Verifies that the request is valid and, if so, creates a Celery task to process it
    """

    # This class is largely adapted from https://github.com/fladi/django-github-webhook
    @staticmethod
    def _validate_header(headers: request.HttpHeaders) -> HttpResponseBadRequest | None:
        """Validate the headers of a request from a webhook

        Args:
            headers (dict): The headers from the request to validate

        Returns:
            str: Error message if the headers are invalid, otherwise an empty string
        """
        header_signature = headers.get("x-hub-signature-256")
        if header_signature is None:
            return HttpResponseBadRequest(
                "Request does not contain X-HUB-SIGNATURE-256 header"
            )

        event = headers.get("x-github-event")
        if event is None:
            return HttpResponseBadRequest(
                "Request does not contain X-GITHUB-EVENT header"
            )

        return None

    @staticmethod
    def _validate_signature(
        header_signature: str, request_body: bytes
    ) -> HttpResponse | None:
        """Validate the signature of a request from a webhook

        Args:
            header_signature (str): The signature from the request to validate
            request_body (bytes): The body of the request to validate

        Returns:
            str: Error message if the signature is invalid, otherwise an empty string
        """
        digest_name, signature = header_signature.split("=")
        if digest_name != "sha256":
            return HttpResponseBadRequest(
                f"Unsupported X-HUB-SIGNATURE-256 digest mode: {digest_name}"
            )

        mac = hmac.new(
            settings.WEBISCITE_GITHUB_WEBHOOK_SECRET.encode("utf-8"),
            msg=request_body,
            digestmod="sha256",
        )
        if not hmac.compare_digest(mac.hexdigest(), signature):
            return HttpResponseForbidden("Invalid X-HUB-SIGNATURE-256 signature")

        return None

    # Unused because I'm worried it will take too long
    @staticmethod
    def _validate_remote_addr(remote_addr: str) -> str:
        """Validate the remote address of a request from a webhook

        Args:
            request: The request from the webhook

        Returns:
            str: Error message if the remote address is invalid, otherwise empty string
        """
        # Get the list of IP addresses that GitHub uses to send webhooks
        # This will slow the response but since it's not a frequent request,
        # it shoulnd't make a big difference
        webhook_allowed_hosts = requests.get(
            "https://api.github.com/meta", timeout=5
        ).json()["hooks"]
        if remote_addr not in webhook_allowed_hosts:
            return "Invalid remote address for GitHub webhook request"

        return ""

    def validate_request(
        self, headers: request.HttpHeaders, body: bytes
    ) -> HttpResponse | None:
        return self._validate_header(headers) or self._validate_signature(
            headers["x-hub-signature-256"], body
        )
        # or validate_remote_addr(headers["remote-addr"])

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        error = self.validate_request(request.headers, request.body)
        if error is not None:
            return error

        # Process the GitHub event
        # For info on the GitHub Webhook API, see
        # https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads
        event = request.headers.get(
            "x-github-event", "ping"
        )  # header was already validated
        handler = getattr(self, event, None)
        if handler is None:
            return HttpResponseBadRequest(
                f"Unsupported X-GITHUB-EVENT header found: {event}"
            )

        payload = json.loads(request.body.decode("utf-8"))
        return handler(payload)

    def ping(self, payload: dict) -> HttpResponse:
        return HttpResponse("pong")

    def push(self, payload: dict) -> HttpResponse:
        return HttpResponse("push received")

    pull_request = PullRequestHandler()


github_webhook_view = GithubWebhookView.as_view()
