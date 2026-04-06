How To - Project Documentation
======================================================================

Get Started
----------------------------------------------------------------------

Documentation source files live in the ``docs/`` directory at the repository root.


To build and serve docs with live reload, start the local stack (including the ``docs``
service) from the project root::

    just up

The docs container serves Sphinx at http://localhost:9000/ (see ``docker-compose.local.yml``).

Changes to files under ``docs/`` and under ``democrasite/`` (watched by sphinx-autobuild)
will be picked up and reloaded automatically.

`Sphinx <https://www.sphinx-doc.org/>`_ is the tool used to build documentation.

Docstrings to Documentation
----------------------------------------------------------------------

The sphinx extension `apidoc <https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html/>`_
is used to automatically document code using signatures and docstrings.

Numpy or Google style docstrings will be picked up from project files and
available for documentation. See the
`Napoleon <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/>`_ extension for details.

For an in-use example, see the `page source <_sources/users.rst.txt>`_ for :ref:`users`.

To compile all docstrings automatically into documentation source files, use the command::

    make apidocs
