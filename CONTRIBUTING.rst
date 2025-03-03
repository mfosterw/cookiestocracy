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

- Adding a new page

- Improving Documentation

- User Interface Enhancements

- Adding tests for existing code

- Providing translations


.. Adapted from https://cookiecutter-django.readthedocs.io/en/latest/developing-locally-docker.html

Setting up your local environment
=================================

For larger changes, or changes to the dev or Docker containers, you should set up
`Docker`_ on your local machine. If you develop in a dev container, the ``.envs``
directory, which is required by Docker to create the container images, will be copied
from ``.envs.template`` automatically. If you do not create a dev container, then before
you run the Docker containers you MUST copy the ``.envs.template`` directory to
``.envs`` yourself. You can create the copy without overwriting any existing changes
you have made using this command::

    $ cp -rn .envs.template/ .envs/

Once ``.envs`` exists, you can personalize any environment variables you need, such as
saving OAuth application credentials in ``.django``. Remember to never
put sensitive information anywhere it might be added to source control!

.. _`Docker`: https://docs.docker.com/get-docker/

Prerequisites
-------------

* Docker; if you don't have it yet, follow the `installation instructions`_.
* Docker Compose; refer to the official documentation for the `installation guide`_.
* Pre-commit; refer to the official documentation for the `pre-commit`_.
* Just (optional); to simplify running commands, install `just`_.

The commands below assume you have ``just`` installed. If you don't, you can reference the
commands in the ``justfile`` directly.

.. _`installation instructions`: https://docs.docker.com/install/#supported-platforms
.. _`installation guide`: https://docs.docker.com/compose/install/
.. _`pre-commit`: https://pre-commit.com/#install
.. _`just`: https://github.com/casey/just?tab=readme-ov-file#packages


Build the stack
---------------

Building the stack can take a while, especially the first time you run this command on your system::

    $ just build

Before making a git commit, you must have installed `pre-commit`_ and then run::

    $ pre-commit install


Run the Stack
-------------

The first time the container is run it might take a while to get started, but subsequent runs should start quickly.

Open a terminal at the project root and run the following for to activate all services::

    $ just up

The site should start and be accessible at http://localhost:8000/ and the documentation at http://localhost:9000.

To run a specific service and its dependencies, run::

    $ just up <service_name>

To run a full stack without Celery, start ``django``::

    $ just up django


Execute Management Commands
---------------------------

Shortcuts for all the management commands mentioned in the ``README`` are available in the ``justfile``.
To see a list of all the available commands, run ``just`` without any arguments.


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


Automating Your Repository
--------------------------

When a :class:`~democrasite.webiscite.models.Bill` passes, the corresponding pull
request is automatically merged into the master branch, and if code blocks from the
Constitution are moved, their locations are automatically updated in the remote
``constitution.json``. In order to test this functionality in your fork of the
repository, you will need to `create a Github personal access token`_ and include it in
your django environment file as ``GITHUB_TOKEN``. Make sure it at least has write
access to your fork of the repository.

.. _create a Github personal access token: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens


Running Tests Locally
---------------------

The easiest way to run tests is by running ``just test``. This will run the tests from
the ``django`` Docker service so they have access to Postgres. To run the tests in the
local environment, for example using the VSCode test runner, you must have PostgreSQL_
installed on your computer. Django should automatically create a test database for you
when you run the tests.

.. _PostgreSQL: https://www.postgresql.org/download/
