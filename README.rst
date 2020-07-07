#######
rCDS
#######

.. image:: https://github.com/redpwn/rCDS/workflows/CI/badge.svg
    :target: https://github.com/redpwn/rCDS/actions?query=workflow%3ACI+branch%3Amaster
    :alt: CI Status

.. image:: https://img.shields.io/codecov/c/gh/redpwn/rcds
    :target: https://codecov.io/gh/redpwn/rcds
    :alt: Coverage

.. image:: https://img.shields.io/readthedocs/rcds/latest
    :target: https://rcds.redpwn.net/
    :alt: Docs

.. image:: https://img.shields.io/pypi/v/rcds
    :target: https://pypi.org/project/rcds/
    :alt: PyPI

.. This text is copied from the first paragraphs of doc/index.rst

rCDS is redpwn_'s CTF challenge deployment tool. It is designed to automate the
entire challenge deployment process, taking sources from challenge authors and
provisioning the necessary resources to both make challenges available on the
competition scoreboard and to spin up Docker containers that the challenge needs
to run.

rCDS has an opinionated model for managing CTF challenges. It operates on a
centralized challenge repository and is designed to be run from a CI/CD system.
This repository is the single source of truth for all data about challenges, and
rCDS itself essentially acts as a tool to sync the state of various systems (the
scoreboard and the container runtime) to what is described by this repository.
Authors do not directly interface with any of these systems, and instead push
their changes and let a CI job apply them. Thus, the challenge repository can be
versioned, creating an audit log of all changes and allowing for point-in-time
rollbacks of everything regarding a challenge should something go wrong.

For more information, see `the documentation <https://rcds.redpwn.net/>`_.

.. _redpwn: https://redpwn.net/
