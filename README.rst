Democrasite
===========

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style
.. image:: https://github.com/mfosterw/cookiestocracy/actions/workflows/ci.yml/badge.svg
     :target: https://github.com/mfosterw/cookiestocracy/actions/workflows/ci.yml
     :alt: Continuous integration
.. image:: https://codecov.io/gh/mfosterw/cookiestocracy/branch/master/graph/badge.svg?token=NPV1TLXZIW
     :target: https://codecov.io/gh/mfosterw/cookiestocracy
     :alt: Coverage report
.. image:: https://readthedocs.org/projects/cookiestocracy/badge/?version=latest
     :target: https://cookiestocracy.readthedocs.io/en/latest/?badge=latest
     :alt: Documentation status

:License: MIT

Democrasite is a website which automatically merges changes based on popular
approval. For more information on the nature and purpose of the project, visit
our `about page`_. This page is meant for people who want to clone the
repository and contribute to the project. This project is approximately in beta
development (hence the repository being named "cookiestocracy" - a reference
to cookiecutter and `kakistocracy`_). The alpha version is `here`_ and the
full version doesn't exist yet.

* Homepage:
  https://democrasite.herokuapp.com
* Source code:
  https://github.com/mfosterw/cookiestocracy
* Documentation:
  https://cookiestocracy.readthedocs.io/en/latest/

.. _`about page`: https://democrasite.herokuapp.com/about/
.. _`kakistocracy`: https://en.wikipedia.org/wiki/Kakistocracy
.. _`here`: https://github.com/mfosterw/democrasite-testing


Contributing
------------

Please read the `contribution guide`_ to get set up on a local
development environment with docker. See basic commands below, which can be run from
within a dev container or by following the relevant instructions in the aforementioned
guide.

.. _`contribution guide`: https://github.com/mfosterw/cookiestocracy/blob/docker/CONTRIBUTING.rst


Management Commands
-------------------

Getting Started
^^^^^^^^^^^^^^^

If running in a dev container, the server should be running automatically.

Loading initial data
^^^^^^^^^^^^^^^^^^^^

To load some initial sample data into the database, run::

    $ python manage.py loaddata initial.json

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

* To test logging in with a third party provider, you will need oauth keys from the
  provider you're using. See the information on `django-allauth`_ for `GitHub`_ and
  `Google`_ keys respectively, and once you have the keys set the environment variables
  ``<provider>-CLIENT-ID`` and ``<provider>-SECRET`` in ``.envs/.local/.django`` and
  ``.envs/.local/.node``. Once you have these set up, log in through your provider with
  the button on the homepage. For convenience, you can keep your normal user logged in
  on Chrome and your superuser logged in on Firefox (or your browsers of choice), so
  that you can see  how the site behaves for both kinds of users.

    .. note::
        Accounts created through the admin page do not have a normal way to
        sign in since there is no login page. To test working with
        non-superuser accounts, please login through a social provider.

.. _`django-allauth`: https://django-allauth.readthedocs.io/en/latest/overview.html
.. _`GitHub`: https://django-allauth.readthedocs.io/en/latest/providers.html#github
.. _`Google`: https://django-allauth.readthedocs.io/en/latest/providers.html#google

Type checks
^^^^^^^^^^^

Running type checks with mypy::

  $ mypy democrasite


Running tests with pytest
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html


Celery
^^^^^^

This app comes with Celery. To run a celery worker:

.. code-block:: bash

    $ docker compose -f docker-compose.local.yml up -d celeryworker

Please note: For Celery's import magic to work, it is important *where* the
celery commands are run. If you are in the same folder with *manage.py*, you
should be right.
