.. _webiscite:

Webiscite
======================================================================

"Webiscite" is an app which contains the core functionality of Democrasite:
Bills, voting, and interfacing with GitHub. The name is a portmanteau of "web"
and "plebiscite," which is a referendum on a proposed law.

Pull Request Process
----------------------------------------------------------------------

When a pull request is created on `GitHub <https://github.com/mfosterw/cookiestocracy>`_,
a `webhook <https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks>`_
makes a request to the GitHub webhook
:func:`view <democrasite.webiscite.webhooks.github_hook>`.

This method parses the data from the request and calls
:func:`process_pull <democrasite.webiscite.tasks.process_pull>`
which itself calls :func:`pr_opened <democrasite.webiscite.tasks.pr_opened>`
in the even a new pull request was created.

If the user who created the pull request has a democrasite account, a new
:class:`Bill <democrasite.webiscite.models.Bill>`
is created with the information from the pull request and made visible on the
homepage immediately.

A task is also queued up to execute once the voting period ends, at which point
:func:`submit_bill <democrasite.webiscite.tasks.submit_bill>` is called. The
function verifies that the pull request is open and unedited and then counts
the votes for and against that bill.

If it passes the threshold, the bill is merged into the master branch on
Github, officially making it part of Democrasite.
