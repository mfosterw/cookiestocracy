***************************
Contributing to Democrasite
***************************


What to contribute
==================

Obviously this project doesn't work without people adding contributions, preferably
many people adding lots of little contributions frequently. The project is oriented
towards contributions which add new apps or features, with the constitution mechanic
aimed at making it harder to significantly alter existing code than to add new things.
The constitution is also aimed at protecting the core purpose and philosophy of the
site, *not* its functionality. There are innumerable ways to just break the deployment
or delivery of the website and I humbly ask that you refrain from intentionally doing
so. If I see a pull request which breaks the site, I will close it. Use this website as
a playground for whatever project you have that you want to see hosted as long as
Django can serve it; I'd love for this to serve people's random creations. That being
said, there are plenty of contributions and additions you could make to the site
itself, including this document. Regardless of how you choose contribute, as long as it
is in good faith, I appreciate it.

Some ideas for contributions include:
- Adding a new django app
- Adding a new feature to an existing app
- Adding a new page to the front end
- Improving Documentation
- User Interface Enhancements
- Adding tests for existing code
- Providing translations


.. Adapted from https://cookiecutter-django.readthedocs.io/en/latest/developing-locally-docker.html

Getting Up and Running Locally With Docker
==========================================

Prerequisites
-------------

* Docker; if you don't have it yet, follow the `installation instructions`_.

.. warning::
    If you are using an Intel Mac, you may experience crashes when trying to launch the
    ``node`` service. To fix it, see the `Intel Mac Segmentation Fault`_ section below.

* Docker Compose; refer to the official documentation for the `installation guide`_.
* Pre-commit; refer to the official documentation for the `pre-commit`_.

.. _`installation instructions`: https://docs.docker.com/install/#supported-platforms
.. _`installation guide`: https://docs.docker.com/compose/install/
.. _`pre-commit`: https://pre-commit.com/#install


Configuring the Environment
---------------------------

Environment files are expected by Docker, but are not kept in source control. There is
a sample directory with the required structure and variables for local development
located in ``.envs.sample/``. Copy this directory to ``.envs/`` and set any variables
you need (e.g. OAuth application credentials for social authentication)


Build the Stack
---------------

This can take a while, especially the first time you run this particular command on your development system::

    $ docker compose -f docker-compose.local.yml build

Before doing any git commit, `pre-commit`_ should be installed globally on your local machine, and then::

    $ pre-commit install


Run the Stack
-------------

The first time it is run it might take a while to get started, but subsequent runs should occur quickly.

Open a terminal at the project root and run the following for to activate all services::

    $ docker compose -f docker-compose.local.yml up

You can also set the environment variable ``COMPOSE_FILE`` pointing to ``docker-compose.local.yml`` like this::

    $ export COMPOSE_FILE=docker-compose.local.yml

And then run::

    $ docker compose up

To run a specific service and its dependencies, run::

    $ docker compose up <service_name>

To start a full stack with nothing extra, start ``node``::

    $ docker compose up node

To run in a detached (background) mode, just::

    $ docker compose up -d

These commands don't run the docs service. In order to run docs service you can run::

    $ docker compose -f docker-compose.docs.yml up

To run the docs with local services just use::

    $ docker compose -f docker-compose.local.yml -f docker-compose.docs.yml up

The site should start and be accessible at http://localhost:3000, with the api visible at http://localhost:8000/api.


Execute Management Commands
---------------------------

This is done using the ``docker compose -f docker-compose.local.yml run --rm`` command: ::

    $ docker compose -f docker-compose.local.yml run --rm django python manage.py migrate
    $ docker compose -f docker-compose.local.yml run --rm django python manage.py createsuperuser

Here, ``django`` is the target service we are executing the commands against.
Also, please note that the ``docker exec`` does not work for running management commands.


Troubleshooting
---------------

.. _Intel Mac Segmentation Fault:

If you are developing on a Mac with an Intel core, you will get a segmentation fault
when trying to launch the ``node`` service due to a `bug`_ in ``docker-compose``.
To fix it, disable the ``Virtualization Framework`` in `Docker Desktop settings`_.

For other problems, you can open an `issue`_ in the repository.

.. _bug: https://github.com/docker/for-mac/issues/6824
.. _`Docker Desktop settings`: https://docs.docker.com/desktop/settings/mac/
.. _`issue`: https://github.com/mfosterw/cookiestocracy/issues


Creating a Webhook
------------------

:obj:`democrasite.webiscite` needs `webhooks`_ to find out about events on
Github. `Create a webhook`_ in your fork of the repository, then generate a
secret key for your hook and store it in your environment (either through your
terminal or ``.env`` file) as ``GITHUB_SECRET_KEY``.

To test your webhook, follow these `instructions`_. (If you have a preferred
tool for exposing your local server, feel free to replace smee with it.) If you
are using smee, be sure to run::

   $ smee --url WEBHOOK_PROXY_URL --path /webhooks/github --port 8000

to set the correct port and path.

.. _webhooks: https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks
.. _create a webhook: https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks
.. _instructions: https://docs.github.com/en/webhooks/using-webhooks/handling-webhook-deliveries


Automating the Repository
-------------------------

When a :class:`~democrasite.webiscite.models.Bill` passes, the corresponding pull
request is automatically merged into the master branch, and if code blocks from the
Constitution are moved, their locations are automatically updated in the remote
``constitution.json``. In order to test this functionality in your fork of the
repository, you will need to `create a Github personal access token`_ and include it in
your django environment file as ``GITHUB_TOKEN``. Make sure it at least has write
access to your fork of the repository.

.. _create a Github personal access token: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
