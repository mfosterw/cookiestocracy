Democrasite
===========

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style

:License: MIT

Democrasite is a website which automatically merges changes based on popular approval. For more information on the nature and purpose of the project, visit our `about page`_. This page is meant for people who want to clone the repository and contribute to the project. This project is approximately in beta development (hence the repository being named "cookiestocracy" – a reference to cookiecutter and `kakistocracy`_). The alpha version is `here`_ and the full version doesn't exist yet.

* Homepage:
  https://democrasite.herokuapp.com
* Source code:
  https://github.com/mfosterw/cookiestocracy
* Documentation:
  https://democrasite.readthedocs.io

.. _`about page`: https://democrasite.herokuapp.com/about/
.. _`kakistocracy`: https://en.wikipedia.org/wiki/Kakistocracy
.. _`here`: https://github.com/mfosterw/democrasite-testing

Contributing
------------

Please read the `contribution guide`_ and then see the basic commands below. It is also recommended that you rename ".env.sample" in the root of the repository to ".env" and set the environment variable ``DJANGO_READ_DOT_ENV_FILE=True`` so you can more easily keep track of your environment variables.

.. _`contribution guide`: https://github.com/mfosterw/cookiestocracy/blob/master/CONTRIBUTING.rst

Basic Commands
--------------

Getting Started
^^^^^^^^^^^^^^^

To start the server, run this command in the root of the repository:

::

  $ python manage.py runserver

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

* To create a normal account, it's easiest to use the admin site. For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

* To test logging in with a third party provider, you will need oauth keys from the provider you're using. See the information on `django-allauth`_ for `GitHub`_ and `Google`_ keys respectively, and once you have the keys create environment variables named `<provider>-CLIENT-ID` and `<provider>-SECRET`. Once you have these set up, log in normally with your provider. A folder will be created in the repository root called "app-messages" which contains the confirmation email. Open the link in that file and your account will be activated.

.. _`django-allauth`: https://django-allauth.readthedocs.io/en/latest/overview.html
.. _`GitHub`: https://django-allauth.readthedocs.io/en/latest/providers.html#github
.. _`Google`: https://django-allauth.readthedocs.io/en/latest/providers.html#google

Type checks
^^^^^^^^^^^

Running type checks with mypy:

::

  $ mypy democrasite

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest


Celery
^^^^^^

This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd democrasite
    celery -A config.celery_app worker -l info

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.
