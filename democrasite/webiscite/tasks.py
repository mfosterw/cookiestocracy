"""All celery tasks should be defined in this module

This module contains all of the celery tasks used by the webiscite app.
Currently, the defined tasks are all related to processing pull requests
from :func:`democrasite.webiscite.webhooks`.
"""


import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from github import Auth
from github import Github
from github.Repository import Repository

from . import constitution
from .models import Bill

# TODO (#58): Improve logging
logger = get_task_logger(__name__)


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
    bill.submit()

    repo = Github(auth=Auth.Token(settings.WEBISCITE_GITHUB_TOKEN)).get_repo(
        settings.WEBISCITE_REPO
    )
    pull = repo.get_pull(bill.pull_request.number)

    if bill.status != Bill.Status.APPROVED:
        pull.edit(state="closed")  # Close failed pull request
        return

    merge = pull.merge(merge_method="squash", sha=bill.pull_request.sha)
    logger.info(
        "PR %s: bill %s merged (%s)", bill.pull_request.number, bill.id, merge.merged
    )

    # Automatically update constitution line numbers if necessary
    _update_constitution(bill, repo)


def _update_constitution(bill: Bill, repo: Repository) -> None:
    """Updates the constitution if necessary

    Args:
        bill: The bill to update the constitution for
        repo: The repository to update the constitution in
    """
    if bill.constitutional:
        return  # Can't automatically update the constitution if it was changed manually

    diff = requests.get(bill.pull_request.diff_url, timeout=60).text
    con_update = constitution.update_constitution(diff)

    if con_update:
        con_sha = repo.get_contents("democrasite/webiscite/constitution.json").sha  # type: ignore[union-attr]
        repo.update_file(
            "democrasite/webiscite/constitution.json",
            message=f"Update Constitution for PR #{bill.pull_request.number}",
            content=con_update,
            sha=con_sha,
        )
        logger.info("PR %s: constitution updated", bill.pull_request.number)
