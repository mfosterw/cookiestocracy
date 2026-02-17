import pytest
from django.conf import settings
from django.db import IntegrityError
from factory.faker import faker

from democrasite.users.models import User
from democrasite.users.tests.factories import UserFactory
from democrasite.webiscite.models import Bill
from democrasite.webiscite.models import ClosedBillVoteError
from democrasite.webiscite.models import PullRequest
from democrasite.webiscite.models import Vote

from .factories import BillFactory
from .factories import GithubPullRequestFactory
from .factories import PullRequestFactory

# Used to generate random data inline
FAKE = faker.Faker()


class TestPullRequestManager:
    def test_create_from_github_create(self, caplog):
        pr = GithubPullRequestFactory.create(number=FAKE.random_int())
        assert not PullRequest.objects.filter(title=pr["title"]).exists()

        pull_request: PullRequest = PullRequest.objects.create_from_github(pr)

        assert hasattr(pull_request, "created")
        assert PullRequest.objects.filter(title=pr["title"]).exists()

    def test_create_from_github_update(self, bill: Bill, caplog):
        # PullRequest is created during creation of bill fixture
        pr = GithubPullRequestFactory.create(bill=bill)
        assert PullRequest.objects.filter(title=bill.pull_request.title).exists()
        pr["title"] = "New Title"

        PullRequest.objects.create_from_github(pr)

        assert PullRequest.objects.filter(title="New Title").exists()


class TestPullRequest:
    def test_close(self, bill: Bill):
        pull_request = bill.pull_request

        pull_request.close()

        pull_request.refresh_from_db()
        assert pull_request.status == "closed"
        assert not pull_request.bill_set.filter(status=Bill.Status.OPEN).exists()

    def test_close_draft_bill(self):
        bill = BillFactory.create(status=Bill.Status.DRAFT)
        pull_request = bill.pull_request

        pull_request.close()

        pull_request.refresh_from_db()
        bill.refresh_from_db()
        assert pull_request.status == "closed"
        assert bill.status == Bill.Status.CLOSED

    def test_close_no_bill(self, caplog):
        pull_request = PullRequestFactory.create()
        assert pull_request.status == "open"

        bill = pull_request.close()

        pull_request.refresh_from_db()
        assert pull_request.status == "closed"
        assert bill is None


class TestVote:
    def test_vote_str(self, bill: Bill, user: User):
        bill.vote(user, support=True)
        assert str(Vote.objects.get(user=user, support=True)) == f"{user} for {bill}"

    def test_unique_user_bill_vote(self, bill: Bill, user: User):
        bill.vote(user, support=True)

        with pytest.raises(IntegrityError, match='"unique_user_bill_vote"'):
            Vote(user=user, bill=bill, support=False).save()


class TestBillManager:
    def test_get_queryset(self, bill, user: User):
        bill = Bill.objects.first()

        assert bill.yes_percent == 0
        assert bill.no_percent == 0

        bill.vote(user, support=True)
        bill = Bill.objects.first()

        assert bill.yes_percent == 100  # noqa: PLR2004
        assert bill.no_percent == 0

        bill.vote(user, support=False)
        bill = Bill.objects.first()

        assert bill.yes_percent == 0
        assert bill.no_percent == 100  # noqa: PLR2004

        user2 = UserFactory.create()
        user3 = UserFactory.create()
        bill.vote(user2, support=True)
        bill.vote(user3, support=False)
        bill = Bill.objects.first()

        assert bill.yes_percent == 100 / 3
        assert bill.no_percent == 200 / 3

        bill_queryset = Bill.objects.all()

        assert bill_queryset.ordered

    def test_annotate_user_vote(self, bill: Bill, user: User):
        bill.vote(user, support=True)
        assert Bill.objects.annotate_user_vote(user).first().user_vote is True

        bill.vote(user, support=False)
        assert Bill.objects.annotate_user_vote(user).first().user_vote is False

        bill.vote(user, support=False)
        assert Bill.objects.annotate_user_vote(user).first().user_vote is None

    def test_create_from_github(self, user: User):
        pr = PullRequestFactory.create()
        bill = Bill.objects.create_from_github(
            pr.title,
            FAKE.text(),
            user,
            FAKE.text(),
            pr,
        )

        assert bill.pk is not None
        assert bill._submit_task.enabled is True  # noqa: SLF001

    def test_create_from_github_draft(self, user: User):
        pr = PullRequestFactory.create(draft=True)
        bill = Bill.objects.create_from_github(
            pr.title,
            FAKE.text(),
            user,
            FAKE.text(),
            pr,
        )

        assert bill.pk is not None
        assert bill.status == Bill.Status.DRAFT
        assert bill._submit_task.enabled is False  # noqa: SLF001

    def test__create_submit_task(self):
        # just hit the error branch of finally clause
        with (
            pytest.raises(
                AttributeError,
                match=r"self._bill was not saved in the submit task context",
            ),
            Bill.objects._create_submit_task(),  # noqa: SLF001
        ):
            pass


class TestBill:
    def test_unique_active_pull_request(self, bill: Bill):
        bill.status = "closed"
        bill.save()

        BillFactory.create(pull_request=bill.pull_request)

        with pytest.raises(IntegrityError, match='"unique_active_pull_request"'):
            BillFactory.create(pull_request=bill.pull_request)

    def test_unique_active_pull_request_draft(self):
        bill = BillFactory.create(status=Bill.Status.DRAFT)

        with pytest.raises(IntegrityError, match='"unique_active_pull_request"'):
            BillFactory.create(pull_request=bill.pull_request, status=Bill.Status.DRAFT)

    def test_str(self):
        bill = BillFactory.create(name="The Test Act", pk=1, pull_request__number="-2")
        assert str(bill) == "Bill 1: The Test Act (PR #-2)"

    def test_get_absolute_url(self, bill: Bill):
        assert bill.get_absolute_url() == f"/bills/{bill.id}/"

    def test_get_update_url(self, bill: Bill):
        assert bill.get_update_url() == f"/bills/{bill.id}/update/"

    def test_get_vote_url(self, bill: Bill):
        assert bill.get_vote_url() == f"/bills/{bill.id}/vote/"

    def test_close(self, bill: Bill):
        assert bill._submit_task.enabled is True  # noqa: SLF001

        bill.close()

        bill.refresh_from_db()
        assert bill.status == Bill.Status.CLOSED
        assert bill._submit_task.enabled is False  # noqa: SLF001


class TestBillPublish:
    def test_publish(self):
        bill = BillFactory.create(status=Bill.Status.DRAFT)
        bill._submit_task.enabled = False  # noqa: SLF001
        bill._submit_task.save()  # noqa: SLF001

        bill.publish()

        bill.refresh_from_db()
        assert bill.status == Bill.Status.OPEN
        assert bill._submit_task.enabled is True  # noqa: SLF001
        assert bill._submit_task.last_run_at is not None  # noqa: SLF001

    def test_publish_not_draft(self, bill: Bill):
        with pytest.raises(ValueError, match="Only draft bills can be published"):
            bill.publish()


class TestBillVote:
    def test_bill_vote_yes_toggle(self, bill: Bill, user: User):
        bill.vote(user, support=True)
        assert bill.yes_votes.filter(pk=user.id).exists()
        bill.vote(user, support=True)
        assert not bill.yes_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_toggle(self, bill: Bill, user: User):
        bill.vote(user, support=False)
        assert bill.no_votes.filter(pk=user.id).exists()
        bill.vote(user, support=False)
        assert not bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_yes_to_no_switch(self, bill: Bill, user: User):
        bill.vote(user, support=True)
        bill.vote(user, support=False)
        assert not bill.yes_votes.filter(pk=user.id).exists()
        assert bill.no_votes.filter(pk=user.id).exists()

    def test_bill_vote_no_to_yes_switch(self, bill: Bill, user: User):
        bill.vote(user, support=False)
        bill.vote(user, support=True)
        assert not bill.no_votes.filter(pk=user.id).exists()
        assert bill.yes_votes.filter(pk=user.id).exists()

    def test_bill_not_open(self, user: User):
        bill = BillFactory.create(status=Bill.Status.CLOSED)

        with pytest.raises(ClosedBillVoteError, match="Bill is not open for voting"):
            bill.vote(user, support=True)

    def test_draft_bill_not_votable(self, user: User):
        bill = BillFactory.create(status=Bill.Status.DRAFT)

        with pytest.raises(ClosedBillVoteError, match="Bill is not open for voting"):
            bill.vote(user, support=True)


class TestBillSubmit:
    def test_draft_bill_not_submitted(self):
        bill: Bill = BillFactory.create(status=Bill.Status.DRAFT)

        bill.submit()

        assert bill.status == Bill.Status.DRAFT

    def test_bill_not_open(self):
        bill: Bill = BillFactory.create(status=Bill.Status.CLOSED)

        bill.submit()

        assert bill.status == Bill.Status.CLOSED

    def test_insufficient_votes(self, bill: Bill):
        bill.submit()

        assert bill.status == Bill.Status.FAILED

    def test_bill_rejected(self, bill: Bill):
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=False) for voter in voters]
        )

        bill.submit()

        assert bill.status == Bill.Status.REJECTED

    def test_constitutional_bill_rejected(self):
        bill = BillFactory.create(constitutional=True)
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=False) for voter in voters]
        )

        bill.submit()

        assert bill.status == Bill.Status.REJECTED

    def test_bill_passed(self, bill: Bill):
        voters = UserFactory.create_batch(settings.WEBISCITE_MINIMUM_QUORUM)
        Vote.objects.bulk_create(
            [Vote(bill=bill, user=voter, support=True) for voter in voters]
        )

        bill.submit()

        assert bill.status == Bill.Status.APPROVED
