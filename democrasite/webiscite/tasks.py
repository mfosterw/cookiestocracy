from datetime import timedelta
from typing import Any

import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from github import Auth, Github

from . import constitution
from .models import Bill

User = get_user_model()
logger = get_task_logger(__name__)


@shared_task
def process_pull(action: str, pr: dict[str, Any]):
    """Calls a method to handle a pull request depending on the action

    Args:
        action: A string extracted from the request representing the action that occurred.
        pr: The parsed JSON object representing the pull request
    """
    if action in ("opened", "reopened"):
        pr_opened(pr)

    elif action == "closed":
        pr_closed(pr)

    else:
        logger.info("PR %s: Action not handled", pr["number"])


def pr_opened(pr: dict[str, Any]):
    """Creates a Bill for new pull request and schedules submit_bill

    Args:
        pr: The parsed JSON object representing the pull request
    """
    # Ensure open bill for this PR does not exist
    try:
        bill = Bill.objects.filter(pr_num=pr["number"]).get(state=Bill.OPEN)
    except Bill.DoesNotExist:
        pass
    else:
        raise ValueError("Open bill with this PR already exists")

    try:
        author = User.objects.filter(socialaccount__provider="github").get(
            socialaccount__uid=pr["user"]["id"]
        )
    except User.DoesNotExist:
        # If the creator of the pull request does not have a linked account,
        # a Bill cannot be created and the pr is ignored.
        logger.info("PR %s: No bill created (user does not exist)", pr["number"])
        return

    diff = requests.get(pr["diff_url"], timeout=60).text
    constitutional = constitution.is_constitutional(diff)

    bill = Bill(
        name=pr["title"],
        description=pr["body"],
        pr_num=pr["number"],
        author=author,
        additions=pr["additions"],
        deletions=pr["deletions"],
        sha=pr["head"]["sha"],
        state=Bill.OPEN,
        constitutional=bool(constitutional),
    )
    bill.save()

    voting_ends = timezone.now() + timedelta(days=settings.WEBISCITE_VOTING_PERIOD)
    # Pass id rather than bill object to avoid potential issues with database refresh
    submit_bill.apply_async((bill.id,), eta=voting_ends)
    logger.info("PR %s: Bill %s created", pr["number"], bill.id)


def pr_closed(pr: dict[str, Any]):
    """Disables the open bill associated with the pull request

    Args:
        pr: The parsed JSON object representing the pull request
    """
    try:
        bill = Bill.objects.filter(pr_num=pr["number"]).get(state=Bill.OPEN)
    except Bill.DoesNotExist:
        logger.info("PR %s: No modification (no open bill)", pr["number"])
        return
    bill.state = Bill.CLOSED
    bill.save()
    logger.info("PR %s: Bill %s set to closed", pr["number"], bill.id)


@shared_task
def submit_bill(bill_id: int):
    """Handles the final processing and closing of a bill

    When the voting period of a bill ends, this method is called with the id of that
    bill. It verifies that the bill is still active and counts the votes. If the bill
    has enough votes to pass (which varies depending on whether or not it's
    constitutional), it is merged into the master branch of the repository.
    Finally, no regardless of the status of the bill, the pull request is closed.

    Args:
        bill_id: The id of the bill to submit
    """
    bill = Bill.objects.get(pk=bill_id)
    repo = Github(auth=Auth.Token(settings.WEBISCITE_GITHUB_TOKEN)).get_repo(
        settings.WEBISCITE_REPO
    )
    pull = repo.get_pull(bill.pr_num)

    # Bill was closed before voting period ended
    if bill.state != Bill.OPEN:
        pull.edit(state="closed")  # Close failed pull request
        logger.info("PR %s: bill %s was not open", bill.pr_num, bill.id)
        return

    ayes = bill.yes_votes.count()
    nays = bill.no_votes.count()
    total_votes = ayes + nays
    # Bill failed to meet quorum
    if total_votes < settings.WEBISCITE_MINIMUM_QUORUM:
        bill.state = Bill.FAILED
        bill.save()
        pull.edit(state="closed")  # Close failed pull request
        logger.info(
            "PR %s: bill %s rejected with insufficient votes",
            bill.pr_num,
            bill.id,
        )
        return

    approval = ayes / (total_votes)
    if bill.constitutional:
        approved = approval > settings.WEBISCITE_SUPERMAJORITY
    else:
        approved = approval > settings.WEBISCITE_NORMAL_MAJORITY

    # Bill failed to meet approval threshold
    if not approved:
        bill.state = Bill.REJECTED
        bill.save()
        pull.edit(state="closed")  # Close failed pull request
        logger.info(
            "PR %s: Pull request failed with %s%% of votes", bill.pr_num, approval
        )
        return

    # Bill passed
    bill.state = Bill.APPROVED
    bill.save()
    logger.info(
        "PR %s: Pull request passed with %s%% of votes",
        bill.pr_num,
        approval * 100,
    )
    merge = pull.merge(merge_method="squash", sha=bill.sha)
    logger.info("PR %s: merged (%s)", bill.pr_num, merge.merged)

    # Automatically update constitution line numbers if necessary
    if not bill.constitutional:
        diff = requests.get(pull.diff_url, timeout=60).text
        con_update = constitution.update_constitution(diff)
        if con_update:
            con_sha = repo.get_contents("democrasite/webiscite/constitution.json").sha  # type: ignore [union-attr]
            repo.update_file(
                "democrasite/webiscite/constitution.json",
                message=f"Update Constitution for PR {bill.pr_num}",
                content=con_update,
                sha=con_sha,
            )
            logger.info("PR %s: constitution updated", bill.pr_num)
