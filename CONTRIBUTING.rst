Contributing to rCDS
====================

Workflow
--------

Dependency management is done through poetry_, and pre-commit linting hooks are
maanged with pre-commit_. To get started, run ``poetry install`` and ``poetry
run pre-commit install``.

Tests use pytest_, and a Makefile is set up with targets for common operations;
to run tests, use ``make test``; to run tests and get an HTML coverage report,
use ``make htmlcov``; to lint everything, use either ``make lint`` or ``poetry
run pre-commit run -a`` (``make lint`` will stop executing linters after one
failure, while pre-commit will not lint any untracked files).

.. note::

    This is subject to change; we may move the running of these jobs to use tox
    in the future, but for now ``make`` is used for running scripts.

This project uses isort_, black_, flake8_ with flake8-bugbear_, and mypy_ (see
the `pre-commit configuration`_); consider setting up editor integrations to
ease your development process (particularly with mypy).

If you want a live preview of the docs as you work, you can install
sphinx-autobuild_ into the Poetry virtualenv (``poetry run pip install
sphinx-autobuild``) and run it via ``poetry run make livebuild``.

Git
---

This project follows `Conventional Commits`_, and uses Angular's `commit types`__.

.. __: https://github.com/angular/angular/blob/master/CONTRIBUTING.md#types

Branches should be named prefixed with a type (the same types as used in the
commit message) and a short description of the purpose of the branch. Some
examples::

    feat/brief-description
    fix/bug-description


.. _poetry: https://python-poetry.org/
.. _pre-commit: https://pre-commit.com/
.. _pytest: https://docs.pytest.org/en/latest/
.. _isort: https://timothycrosley.github.io/isort/
.. _black: https://black.readthedocs.io/en/stable/
.. _flake8: https://flake8.pycqa.org/en/latest/
.. _flake8-bugbear: https://github.com/PyCQA/flake8-bugbear
.. _mypy: https://github.com/python/mypy
.. _sphinx-autobuild: https://github.com/GaretJax/sphinx-autobuild
.. _conventional commits: https://www.conventionalcommits.org/

.. _pre-commit configuration: https://github.com/redpwn/rCDS/blob/master/.pre-commit-config.yaml
