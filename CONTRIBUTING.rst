.. _contributing:

***************************
Contributing to Democrasite
***************************

.. index:: pip, virtualenv, PostgreSQL


What to contribute
==================

Obviously this project doesn't work without people adding contributions,
preferably many people adding lots of little contributions frequently. The
project is oriented towards contributions which add new apps or features, with
the constitution mechanic aimed at making it harder to significantly alter
existing code than to add new things. The constitution is also aimed at
protecting the core purpose and philosophy of the site, *not* its
functionality. There are innumerable ways to just break the deployment or
delivery of the website and I humbly ask that you refrain from intentionally
doing so. If I see a pull request which breaks the site, I will close it. Use
this website as a playground for whatever project you have that you want to
see hosted as long as Django can serve it; I'd love for this to serve
people's random creations. That being said, there are plenty of contributions
and additions you could make to the site itself, such as to this document,
which tells people nothing about how to contribute at the moment. Regardless of
how you choose contribute, as long as it is in good faith, I appreciate it.


.. Adapted from https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html

Getting Up and Running
======================

Setting Up Development Environment
----------------------------------

Make sure to have the following on your host:

* Python 3.12
* PostgreSQL_
* Redis_
* Cookiecutter_

First things first.

#. Create a virtualenv::

    $ python3.12 -m venv <virtual env path>

#. Activate the virtualenv you have just created::

    $ source <virtual env path>/bin/activate

#. Install development requirements::

    $ cd <what you have entered as the project_slug at setup stage>
    $ pip install -r requirements/local.txt
    $ git init # A git repo is required for pre-commit to install
    $ pre-commit install

   .. note::

       the `pre-commit` hook exists in the generated project as default.
       For the details of `pre-commit`, follow the `pre-commit`_ site.

#. Create a new PostgreSQL database using createdb_::

    $ createdb --username=postgres <project_slug>

   ``project_slug`` is what you have entered as the project_slug at the setup stage.

   .. note::

       if this is the first time a database is created on your machine you might need an
       `initial PostgreSQL set up`_ to allow local connections & set a password for
       the ``postgres`` user. The `postgres documentation`_ explains the syntax of the config file
       that you need to change.


#. Set the environment variables for your database(s)::

    $ export DATABASE_URL=postgres://postgres:<password>@127.0.0.1:5432/<DB name given to createdb>
    # Optional: set broker URL if using Celery
    $ export CELERY_BROKER_URL=redis://localhost:6379/0

   .. seealso::

       To help setting up your environment variables, you have a few options:

       * create an ``.env`` file in the root of your project and define all the variables you need in it.
         There's a .env.sample in the root of the repository which you can rename to serve as a basis.
         Then you just need to have ``DJANGO_READ_DOT_ENV_FILE=True`` in your machine and all the variables
         will be read.
       * Use a local environment manager like `direnv`_

#. Apply migrations::

    $ python manage.py migrate

#. See the application being served through Django development server::

    $ python manage.py runserver 0.0.0.0:8000

.. _PostgreSQL: https://www.postgresql.org/download/
.. _Redis: https://redis.io/download
.. _CookieCutter: https://github.com/cookiecutter/cookiecutter
.. _createdb: https://www.postgresql.org/docs/current/static/app-createdb.html
.. _initial PostgreSQL set up: https://web.archive.org/web/20190303010033/http://suite.opengeo.org/docs/latest/dataadmin/pgGettingStarted/firstconnect.html
.. _postgres documentation: https://www.postgresql.org/docs/current/static/auth-pg-hba-conf.html
.. _pre-commit: https://pre-commit.com/
.. _direnv: https://direnv.net/


Celery
------

If the project is configured to use Celery as a task scheduler then, by default, tasks are set to run on the main thread when developing locally instead of getting sent to a broker. However, if you have Redis setup on your local machine, you can set the following in ``config/settings/local.py``::

    CELERY_TASK_ALWAYS_EAGER = False

Next, make sure `redis-server` is installed (per the `Getting started with
Redis guide`_) and run the server in one terminal::

    $ redis-server

Start the Celery worker by running the following command in another terminal::

    $ celery -A config.celery_app worker --loglevel=info

That Celery worker should be running whenever your app is running, typically as
a background process, so that it can pick up any tasks that get queued. Learn
more from the `Celery Workers Guide`_.

You can also use Django admin to queue up tasks, thanks to the
`django-celerybeat`_ package.

.. _Getting started with Redis guide: https://redis.io/docs/getting-started/
.. _Celery Workers Guide: https://docs.celeryq.dev/en/stable/userguide/workers.html
.. _django-celerybeat: https://django-celery-beat.readthedocs.io/en/latest/


Creating a webhook
------------------

:obj:`democrasite.webiscite` needs `webhooks`_ to find out about events on
Github. `Create a webhook`_ in your fork of the repository, then generate a
secret key for your hook and store it in your environment (either through your
terminal or ``.env`` file) as ``GITHUB_SECRET_KEY``.

To test your webhook, follow these `instructions`_. (If you have a preferred
tool for exposing your local server, feel free to replace smee with it.) If you
are using smee, be sure to run::

   smee --url WEBHOOK_PROXY_URL --path /webhooks/github --port 8000

to set the correct port and path.

.. _webhooks: https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks
.. _create a webhook: https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks
.. _instructions: https://docs.github.com/en/webhooks/using-webhooks/handling-webhook-deliveries


Automating the Repository
-------------------------

When a :class:`~democrasite.webiscite.models.Bill` passes, the corresponding
pull request is automatically merged into the master branch, and if code blocks
from the Constitution are moved, their locations are automatically updated in
the remote constitution.json. In order to test this functionality in your fork
of the repository, you will need to `create a Github personal access token`_
and store it in your environment as ``GITHUB_TOKEN``. Make sure it at least has
write access to your fork of the repository.

.. _create a Github personal access token: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
