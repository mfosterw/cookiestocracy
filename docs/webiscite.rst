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

When a pull request is created on `GitHub`_, a `webhook`_ makes a POST request
to the :class:`~democrasite.webiscite.webhooks.GithubWebhookView`, which
validates the request signature and dispatches to the appropriate handler.

For pull request events, the request is handled by
:class:`~democrasite.webiscite.webhooks.PullRequestHandler`. When a pull
request is opened or reopened, its
:meth:`~democrasite.webiscite.webhooks.PullRequestHandler.opened` method
creates a :class:`~democrasite.webiscite.models.PullRequest` instance.

If the user who created the pull request has a democrasite account, a new
:class:`~democrasite.webiscite.models.Bill`
is created with the information from the pull request and made visible on the
homepage immediately. A :class:`~django_celery_beat.models.PeriodicTask` is
also scheduled to execute :func:`~democrasite.webiscite.tasks.submit_bill`
once the voting period ends.

:func:`~democrasite.webiscite.tasks.submit_bill` verifies that the pull
request is still open and that its SHA has not changed since the bill was
created (i.e. the pull request has not been edited), then counts the votes for
and against that Bill.

If the votes for the Bill pass the threshold, the pull request is merged into
the master branch on Github and automatically deployed, officially making it
part of Democrasite.

.. _GitHub: https://github.com/mfosterw/cookiestocracy
.. _webhook: https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks
