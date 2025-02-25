Democrasite
===========

|Built with Cookiecutter Django| |Black code style| |Continuous integration| |Coverage report| |Documentation status|

.. |Built with Cookiecutter Django| image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter
     :target: https://github.com/pydanny/cookiecutter-django/

.. |Black code style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black

.. |Continuous integration| image:: https://github.com/mfosterw/cookiestocracy/actions/workflows/ci.yml/badge.svg
     :target: https://github.com/mfosterw/cookiestocracy/actions/workflows/ci.yml

.. |Coverage report| image:: https://codecov.io/gh/mfosterw/cookiestocracy/branch/master/graph/badge.svg?token=NPV1TLXZIW
     :target: https://codecov.io/gh/mfosterw/cookiestocracy

.. |Documentation status| image:: https://readthedocs.org/projects/cookiestocracy/badge/?version=latest
     :target: https://cookiestocracy.readthedocs.io/en/latest/?badge=latest


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

Getting Started
^^^^^^^^^^^^^^^

|Open in GitHub Codespaces|

.. |Open in GitHub Codespaces| image:: https://github.com/codespaces/badge.svg
    :target: https://codespaces.new/mfosterw/cookiestocracy?quickstart=1

The easiest way to explore the repository is to open it in GitHub Codespaces with the
button above. Once you've given the container some time to set up (it should take about
three minutes), navigate to the ports tab right above the terminal and hover over port
3000, then click on the browser icon that appears. You should see the development
version of the homepage! (With no data yet, see below).

Please read the `contribution guide`_ to set up a local development environment with
Docker. See basic commands below, which can be run from within a dev container or by
following the instructions in the guide.

.. _`contribution guide`: https://cookiestocracy.readthedocs.io/en/latest/CONTRIBUTING.html


Management Commands
-------------------

Viewing server logs
^^^^^^^^^^^^^^^^^^^

To view the logs from the runserver process run::

    $ docker logs -f democrasite-local-django

Loading initial data
^^^^^^^^^^^^^^^^^^^^

To load some initial sample data into the database, run::

    $ python manage.py loaddata initial.json

Setting up your users
^^^^^^^^^^^^^^^^^^^^^

* To create a **superuser account** to log into the admin at localhost:8000/admin, use
  this command::

    $ python manage.py createsuperuser

* To test logging in with a third party provider, you will need OAuth keys from the
  provider you're using. See the information on `django-allauth`_ for `GitHub`_ and
  `Google`_ keys respectively, and once you have the keys set the environment variables
  ``<provider>-CLIENT-ID`` and ``<provider>-SECRET`` in ``.envs/.local/.django`` and then
  rebuild the container. Once it is rebuilt, log in through your provider with the button
  on the homepage. For convenience, you can keep your normal user logged in on Chrome and
  your superuser logged in on Firefox (or your browsers of choice), so that you can see
  how the site behaves for both kinds of users.

.. _`django-allauth`: https://docs.allauth.org/en/latest/introduction/index.html
.. _`GitHub`: https://django-allauth.readthedocs.io/en/latest/providers.html#github
.. _`Google`: https://docs.allauth.org/en/latest/socialaccount/providers/github.html

Linting
^^^^^^^

To lint your staged changes, run::

    $ pre-commit run

To lint all files, run::

    $ pre-commit run --all

Type checks
^^^^^^^^^^^

Running type checks with mypy::

  $ mypy democrasite


Running tests
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html
