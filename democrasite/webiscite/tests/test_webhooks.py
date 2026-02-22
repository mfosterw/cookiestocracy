import hmac
import json
from http import HTTPStatus
from typing import cast
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from django.test import RequestFactory
from django.utils.encoding import force_bytes
from factory.faker import faker

from democrasite.users.models import User
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import PullRequest
from democrasite.webiscite.tests.factories import BillFactory
from democrasite.webiscite.tests.factories import GithubPullRequestFactory
from democrasite.webiscite.webhooks import GithubWebhookView
from democrasite.webiscite.webhooks import PullRequestHandler
from democrasite.webiscite.webhooks import github_webhook_view


class TestGithubHookView:
    def check_response(self, request, status, content):
        response = cast(HttpResponse, github_webhook_view(request))

        assert response.status_code == status
        assert response.content == content

    def test_no_signature(self, rf: RequestFactory):
        request = rf.post("/fake-url/")

        self.check_response(
            request, 400, b"Request does not contain X-HUB-SIGNATURE-256 header"
        )

    def test_no_event(self, rf: RequestFactory):
        request = rf.post("/fake-url/", HTTP_X_HUB_SIGNATURE_256="test")

        self.check_response(
            request, 400, b"Request does not contain X-GITHUB-EVENT header"
        )

    def test_invalid_signature_digest(self, rf: RequestFactory):
        request = rf.post(
            "/fake-url/",
            HTTP_X_HUB_SIGNATURE_256="test=test",
            HTTP_X_GITHUB_EVENT="test",
        )

        self.check_response(
            request, 400, b"Unsupported X-HUB-SIGNATURE-256 digest mode: test"
        )

    def test_invalid_signature(self, rf: RequestFactory):
        request = rf.post(
            "/fake-url/",
            HTTP_X_HUB_SIGNATURE_256="sha256=test",
            HTTP_X_GITHUB_EVENT="test",
        )

        self.check_response(request, 403, b"Invalid X-HUB-SIGNATURE-256 signature")

    @patch("requests.get")
    def test_validate_remote_addr(self, mock_get):
        mock_get().json.return_value = {"hooks": ["127.0.0.1"]}

        response = GithubWebhookView()._validate_remote_addr("127.0.0.1")  # noqa: SLF001

        assert response == ""

    @patch("requests.get")
    def test_validate_remote_addr_invalid(self, mock_get):
        mock_get().json.return_value = {"hooks": ["127.0.0.1"]}

        response = GithubWebhookView()._validate_remote_addr("127.0.0.2")  # noqa: SLF001

        assert response == "Invalid remote address for GitHub webhook request"

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
        self.check_response(
            signed_request, 400, b"Unsupported X-GITHUB-EVENT header found: test"
        )

    def test_valid_request(self, signed_request):
        signed_request.META["HTTP_X_GITHUB_EVENT"] = "ping"
        self.check_response(signed_request, 200, b"pong")

    def test_push(self):
        response = GithubWebhookView().push({})

        assert response.status_code == HTTPStatus.OK
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

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.content == b"Unsupported action: test"

    def test_pr_handler_get_response(self, pr_handler: PullRequestHandler, bill: Bill):
        response = pr_handler.get_response("test", bill.pull_request, bill)

        assert json.loads(response.content) == {
            "action": "test",
            "pull_request": bill.pull_request.number,
            "bill": bill.id,
        }

    @patch("requests.get")
    def test_opened(self, mock_get, user: User, pr_handler: PullRequestHandler):
        pr = GithubPullRequestFactory.create()
        pr["user"]["id"] = SocialAccount.objects.create(
            user=user,
            provider="github",
            uid=faker.Faker().random_int(),
        ).uid

        pull_request, bill = pr_handler.opened(pr)

        assert pull_request is not None
        assert bill is not None
        assert bill.author == user

    @patch("requests.get")
    def test_opened_draft(self, mock_get, user: User, pr_handler: PullRequestHandler):
        pr = GithubPullRequestFactory.create(draft=True)
        pr["user"]["id"] = SocialAccount.objects.create(
            user=user,
            provider="github",
            uid=faker.Faker().random_int(),
        ).uid

        pull_request, bill = pr_handler.opened(pr)

        assert pull_request is not None
        assert pull_request.draft is True
        assert bill is not None
        assert bill.status == Bill.Status.DRAFT
        assert bill._submit_task is None  # noqa: SLF001

    def test_ready_for_review(self, pr_handler: PullRequestHandler):
        bill = BillFactory.create(status=Bill.Status.DRAFT)
        bill.pull_request.draft = True
        bill.pull_request.save()

        pull_request, published_bill = pr_handler.ready_for_review(
            {"number": bill.pull_request.number}
        )

        assert pull_request is not None
        assert pull_request.draft is False
        assert published_bill is not None
        published_bill.refresh_from_db()
        assert published_bill.status == Bill.Status.OPEN
        assert published_bill._submit_task is not None  # noqa: SLF001
        assert published_bill._submit_task.enabled is True  # noqa: SLF001

    def test_ready_for_review_no_pr(self, pr_handler: PullRequestHandler):
        result = pr_handler.ready_for_review({"number": 1})
        assert result == (None, None)

    def test_ready_for_review_no_draft_bill(
        self, pr_handler: PullRequestHandler, bill: Bill
    ):
        pull_request, result_bill = pr_handler.ready_for_review(
            {"number": bill.pull_request.number}
        )

        assert pull_request is not None
        assert result_bill is None

    @patch.object(PullRequestHandler, "opened")
    def test_reopened(self, mock_opened, pr_handler: PullRequestHandler):
        # Basically just for 100% coverage
        response = pr_handler.reopened({})

        mock_opened.assert_called_once_with({})
        assert response == mock_opened.return_value

    def test_closed_no_pr(self, pr_handler: PullRequestHandler):
        response = pr_handler.closed({"number": 1})
        assert response == (None, None)

    @patch.object(PullRequest, "close")
    def test_closed(self, mock_close, pr_handler: PullRequestHandler, bill: Bill):
        response = pr_handler.closed({"number": bill.pull_request.number})

        assert response == (bill.pull_request, mock_close.return_value)
        mock_close.assert_called_once()
