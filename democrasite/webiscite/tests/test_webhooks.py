# pylint: disable=too-few-public-methods,no-self-use
import hmac
import json
from typing import cast
from unittest.mock import patch

import pytest
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory
from django.utils.encoding import force_bytes

from ..models import Bill, PullRequest
from ..webhooks import GithubWebhookView, PullRequestHandler, github_webhook_view


class TestGithubHookView:
    def check_response(self, request, status, content):
        response = cast(HttpResponse, github_webhook_view(request))

        assert response.status_code == status
        assert response.content == content

    def test_no_signature(self, rf: RequestFactory):
        request = rf.post("/fake-url/")

        self.check_response(request, 400, b"Request does not contain X-HUB-SIGNATURE-256 header")

    def test_no_event(self, rf: RequestFactory):
        request = rf.post("/fake-url/", HTTP_X_HUB_SIGNATURE_256="test")

        self.check_response(request, 400, b"Request does not contain X-GITHUB-EVENT header")

    def test_invalid_signature_digest(self, rf: RequestFactory):
        request = rf.post("/fake-url/", HTTP_X_HUB_SIGNATURE_256="test=test", HTTP_X_GITHUB_EVENT="test")

        self.check_response(request, 400, b"Unsupported X-HUB-SIGNATURE-256 digest mode: test")

    def test_invalid_signature(self, rf: RequestFactory):
        request = rf.post("/fake-url/", HTTP_X_HUB_SIGNATURE_256="sha256=test", HTTP_X_GITHUB_EVENT="test")

        self.check_response(request, 403, b"Invalid X-HUB-SIGNATURE-256 signature")

    @pytest.fixture
    def signed_request(self, rf: RequestFactory):
        request = rf.post(
            "/fake-url/",
            data=json.dumps({"action": "none", "pull_request": "-1"}),
            content_type="application/json",
            HTTP_X_GITHUB_EVENT="test",
        )

        request.META["HTTP_X_HUB_SIGNATURE_256"] = (
            "sha256="
            + hmac.new(
                force_bytes(settings.WEBISCITE_GITHUB_WEBHOOK_SECRET),
                msg=request.body,
                digestmod="sha256",
            ).hexdigest()
        )

        return request

    def test_unsupported_event(self, signed_request):
        self.check_response(signed_request, 400, b"Unsupported X-GITHUB-EVENT header found: test")

    def test_valid_request(self, signed_request):
        signed_request.META["HTTP_X_GITHUB_EVENT"] = "ping"
        self.check_response(signed_request, 200, b"pong")

    def test_push(self):
        response = GithubWebhookView().push({})

        assert response.status_code == 200
        assert response.content == b"push received"


class TestPullRequestHandler:
    @pytest.fixture
    def pr_handler(self):
        return GithubWebhookView().pull_request

    @patch.object(PullRequestHandler, "opened")
    def test_pr_handler_dispatch(self, mock_opened, bill, pr_handler):
        mock_opened.return_value = (bill.pull_request, bill)

        response = pr_handler({"action": "opened", "pull_request": {"number": 1}})

        mock_opened.assert_called_once_with({"number": 1})
        assert isinstance(response, JsonResponse)

    def test_pr_handler_dispatch_invalid(self, pr_handler: PullRequestHandler):
        response = pr_handler({"action": "test", "pull_request": {"number": 1}})

        assert response.status_code == 400
        assert response.content == b"Unsupported action: test"

    def test_pr_handler_get_response(self, pr_handler: PullRequestHandler, bill: Bill):
        response = pr_handler.get_response("test", bill.pull_request, bill)

        assert json.loads(response.content) == {
            "action": "test",
            "pull_request": bill.pull_request.number,
            "bill": bill.id,
        }

    @patch.object(Bill, "create_from_pr")
    def test_opened(self, mock_create, pr_handler: PullRequestHandler):
        # This just calls the create_from_pr method
        response = pr_handler.opened({})

        mock_create.assert_called_once_with({})
        assert response == mock_create.return_value

    @patch.object(Bill, "create_from_pr")
    def test_reopened(self, mock_create, pr_handler: PullRequestHandler):
        # This does the exact same thing
        response = pr_handler.reopened({})

        mock_create.assert_called_once_with({})
        assert response == mock_create.return_value

    def test_closed_no_pr(self, pr_handler: PullRequestHandler):
        response = pr_handler.closed({"number": 1})
        assert response == (None, None)

    @patch.object(PullRequest, "close")
    def test_closed(self, mock_close, pr_handler: PullRequestHandler, bill: Bill):
        response = pr_handler.closed({"number": bill.pull_request.number})

        assert response == (bill.pull_request, mock_close.return_value)
        mock_close.assert_called_once()
