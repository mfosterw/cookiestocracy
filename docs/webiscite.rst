.. _webiscite:

*********
Webiscite
*********

"Webiscite" is an app which contains the core functionality of Democrasite:
Bills, voting, and interfacing with GitHub. The name is a portmanteau of "web"
and "plebiscite," which is a public referendum on a proposed law.


Pull Requests
=============

Pull Request Processing Pipeline
--------------------------------

When a pull request is created on `GitHub`_, a `webhook`_ makes a request to
the GitHub :func:`webhook view <democrasite.webiscite.webhooks.github_hook>`.

This method parses the data from the request and calls
:func:`~democrasite.webiscite.tasks.process_pull`
to handle the request. In the event a pull request was opened or reopened,
:func:`~democrasite.webiscite.tasks.pr_opened` is called.

If the user who created the pull request has a democrasite account, a new
:class:`~democrasite.webiscite.models.Bill`
is created with the information from the pull request and made visible on the
homepage immediately.

A task to execute :func:`~democrasite.webiscite.tasks.submit_bill`
is also put in the celery queue to execute once the voting period ends. The
function verifies that the pull request is open and unedited and then counts
the votes for and against that Bill.

If the votes for the Bill pass the threshold, the pull request is merged into
the master branch on Github and automatically deployed, officially making it
part of Democrasite.

.. _GitHub: https://github.com/mfosterw/cookiestocracy
.. _webhook: https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks
