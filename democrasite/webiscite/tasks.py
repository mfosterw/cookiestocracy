"""All celery tasks should be defined in this module

This module contains all of the celery tasks used by the webiscite app.
Currently, the defined tasks are all related to processing pull requests
from :func:`democrasite.webiscite.webhooks`.
"""

from typing import Any, cast

import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from github import Auth, Github
from github.PullRequest import PullRequest as GithubPullRequest

from . import constitution
from .models import Bill

User = get_user_model()
# TODO (#58): Improve logging
logger = get_task_logger(__name__)


# TODO: Refactor
@shared_task
def submit_bill(bill_id: int) -> None:
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
    repo = Github(auth=Auth.Token(settings.WEBISCITE_GITHUB_TOKEN)).get_repo(settings.WEBISCITE_REPO)
    pull = repo.get_pull(bill.pull_request.number)

    log: tuple[Any, ...]
    # Bill was closed before voting period ended
    if bill.state != Bill.States.OPEN:
        log = ("PR %s: bill %s was not open", bill.pull_request.number, bill.id)
        # Mypy doesn't make the connection that bill.state is a States enum apparently
        bill.state = cast(Bill.States, bill.state)
        _reject_bill(bill, bill.state, pull, *log)
        return

    total_votes = bill.votes.count()
    # Bill failed to meet quorum
    if total_votes < settings.WEBISCITE_MINIMUM_QUORUM:
        log = ("PR %s: bill %s rejected with insufficient votes", bill.pull_request.number, bill.id)
        _reject_bill(bill, Bill.States.FAILED, pull, *log)
        return

    ayes = bill.yes_votes.count()
    approval = ayes / (total_votes)
    if bill.constitutional:
        approved = approval > settings.WEBISCITE_SUPERMAJORITY
    else:
        approved = approval > settings.WEBISCITE_NORMAL_MAJORITY

    # Bill failed to meet approval threshold
    if not approved:
        log = ("PR %s: bill %s rejected with %s%% of votes", bill.pull_request.number, bill.id, approval * 100)
        _reject_bill(bill, Bill.States.REJECTED, pull, *log)
        return

    # Bill passed
    bill.state = Bill.States.APPROVED
    bill.save()
    logger.info(
        "PR %s: Pull request passed with %s%% of votes",
        bill.pull_request.number,
        approval * 100,
    )
    merge = pull.merge(merge_method="squash", sha=bill.pull_request.sha)
    logger.info("PR %s: merged (%s)", bill.pull_request.number, merge.merged)

    # Automatically update constitution line numbers if necessary
    if not bill.constitutional:
        diff = requests.get(pull.diff_url, timeout=60).text
        con_update = constitution.update_constitution(diff)
        if con_update:
            con_sha = repo.get_contents("democrasite/webiscite/constitution.json").sha  # type: ignore [union-attr]
            repo.update_file(
                "democrasite/webiscite/constitution.json",
                message=f"Update Constitution for PR {bill.pull_request.number}",
                content=con_update,
                sha=con_sha,
            )
            logger.info("PR %s: constitution updated", bill.pull_request.number)


def _reject_bill(bill: Bill, state: Bill.States, pull: GithubPullRequest, msg: str, *args):
    """Rejects a bill and closes the associated pull request

    Args:
        bill: The bill to reject
        state: The state to set the bill to
        pull: The pull request to close
        msg: The message to log
        *args: Arguments for the log message
    """
    bill.state = state
    bill.save()
    pull.edit(state="closed")  # Close failed pull request
    logger.info(msg, *args)
