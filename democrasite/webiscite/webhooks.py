import hmac
import json
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .tasks import process_pull


# Code in this module is adapted from
# https://simpleisbetterthancomplex.com/tutorial/2016/10/31/how-to-handle-github-webhooks-using-django.html
@csrf_exempt
def _github_hook(request: HttpRequest) -> HttpResponse:
    """View for GitHub webhook alerts

    Verifies that the request is valid and, if so, creates a Celery task to process it

    Args:
        request: The request from GitHub containing the alert details

    Returns:
        HttpResponse: A response object to certify the request was received and
        processed or rejected
    """
    # Verify the request signature
    header_signature = request.META.get("HTTP_X_HUB_SIGNATURE")
    if header_signature is None:
        return HttpResponseForbidden("Invalid signature")

    sha_name, signature = header_signature.split("=")
    mac = hmac.new(
        settings.WEBISCITE_GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=request.body,
        digestmod="sha1",
    )
    sig_valid = hmac.compare_digest(mac.hexdigest(), signature)
    if not (sha_name == "sha1" and sig_valid):
        return HttpResponseForbidden("Invalid signature")

    # Process the GitHub event
    # For info on the GitHub Webhook API, see
    # https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads
    event = request.META.get("HTTP_X_GITHUB_EVENT", "ping")
    payload = json.loads(request.POST["payload"])

    if event == "ping":
        return HttpResponse("ping received")

    if event == "pull_request":
        process_pull.delay(payload["action"], payload["pull_request"])
        return HttpResponse("pull request acknowledged")

    # In case we receive an event that's not ping or pull
    return HttpResponse(status=204)


# mypy has trouble with decorators so I needed a workaround to annotate this
github_hook: Callable[[HttpRequest], HttpResponse] = require_POST(_github_hook)
