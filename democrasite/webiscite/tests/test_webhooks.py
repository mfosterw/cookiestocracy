# pylint: disable=too-few-public-methods,no-self-use
import hmac
import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import RequestFactory
from django.utils.encoding import force_bytes

from ..tasks import process_pull
from ..webhooks import github_hook


class TestGithubHookView:
    test_data = {"payload": json.dumps({"action": "none", "pull_request": "-1"})}

    def test_no_signature(self, rf: RequestFactory):
        request = rf.post("/fake-url/")

        response = github_hook(request)

        assert response.status_code == 403
        assert response.content == b"Invalid signature"

    def test_invalid_signature(self, rf: RequestFactory):
        request = rf.post("/fake-url/", HTTP_X_HUB_SIGNATURE="test=test")

        response = github_hook(request)

        assert response.status_code == 403
        assert response.content == b"Invalid signature"

    def test_ping(self, rf: RequestFactory):
        request = rf.post("/fake-url/", data=self.test_data)

        request.META["HTTP_X_HUB_SIGNATURE"] = (
            "sha1="
            + hmac.new(
                force_bytes(settings.WEBISCITE_GITHUB_WEBHOOK_SECRET),
                msg=request.body,
                digestmod="sha1",
            ).hexdigest()
        )

        response = github_hook(request)

        assert response.status_code == 200
        assert response.content == b"ping received"

    @patch.object(process_pull, "delay")
    def test_pull_request(self, mock_delay: MagicMock, rf: RequestFactory):
        request = rf.post(
            "/fake-url/", data=self.test_data, HTTP_X_GITHUB_EVENT="pull_request"
        )

        request.META["HTTP_X_HUB_SIGNATURE"] = (
            "sha1="
            + hmac.new(
                force_bytes(settings.WEBISCITE_GITHUB_WEBHOOK_SECRET),
                msg=request.body,
                digestmod="sha1",
            ).hexdigest()
        )

        response = github_hook(request)

        mock_delay.assert_called_once_with("none", "-1")

        assert response.status_code == 200
        assert response.content == b"pull request acknowledged"

    def test_unknown_action(self, rf: RequestFactory):
        request = rf.post("/fake-url/", data=self.test_data, HTTP_X_GITHUB_EVENT="test")

        request.META["HTTP_X_HUB_SIGNATURE"] = (
            "sha1="
            + hmac.new(
                force_bytes(settings.WEBISCITE_GITHUB_WEBHOOK_SECRET),
                msg=request.body,
                digestmod="sha1",
            ).hexdigest()
        )

        response = github_hook(request)

        assert response.status_code == 204
