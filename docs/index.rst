.. rCDS documentation master file, created by
   sphinx-quickstart on Fri Apr 10 17:12:14 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

rCDS - A CTF Challenge Deployment Tool
======================================

.. A short version of this text is in README.rst

rCDS_ is redpwn_'s CTF challenge deployment tool. It is designed to automate the
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

If you are a challenge author for a CTF using rCDS, head over to the
:doc:`challenge config format docs <challenge>`.

rCDS's mode of operation is optimized for a CI environment. After validating
all challenges' configurations, rCDS runs in 4 stages:

1.  Build all challenge containers, as needed, and upload to a remote container
    registry
2.  Collect all files to upload to competitors
3.  Push the containers over to a :ref:`container runtime
    <backends#container-runtime>`
4.  Render descriptions and push all relevant data to a :ref:`scoreboard
    <backends#scoreboard>`

At its core, rCDS only handles building the Docker containers and preparing all
assets for a challenge (description, files, etc.)---everything else is handled
by a :doc:`backend <backends/index>`.

rCDS does not rely on any system dependencies other than its Python
dependencies. It does not shell out to system commands for performing any
operations, and thus does not need the Docker CLI installed; it just needs to be
able to connect to a Docker daemon.

GitLab CI
---------

rCDS recommends running CI/CD on `GitLab CI`_, because it allows for manual job
runs and tracking deployments in an "environment", which enables easy rollbacks
in case anything goes wrong. It also has well-documented support for performing
`Docker image builds <https://gitlab.com/gitlab-examples/docker>`_ on
Gitlab.com. On Gitlab.com's shared runners, Docker builds can be run by running
the ``docker:dind`` service and setting the ``DOCKER_HOST`` environment variable
to ``tcp://docker:2375``---with this variable set, rCDS does not need to run on
the ``docker`` image; you can use ``python`` or any other image with a working
``pip`` (e.g. ``google/cloud-sdk:slim``).

.. note::

    An example ``.gitlab-ci.yml``:

    .. code-block:: yaml

        image: python:3.8

        services:
          - docker:dind

        variables:
          DOCKER_HOST: tcp://docker:2375

        before_script:
          - pip3 install rcds

        deploy:
          when: manual
          environment:
            name: production
          script:
            - rcds deploy

    You may need additional options to run various deployment backends; see
    :ref:`an example using GKE and rCTF <config-samples#gke-rctf-gitlab>`.

.. _rCDS: https://github.com/redpwn/rcds
.. _redpwn: https://redpwn.net/
.. _GitLab CI: https://docs.gitlab.com/ee/ci


.. TOC Trees--------------------------------------------------------------------

.. toctree::
    :hidden:

    Introduction <self>

.. toctree::
    :maxdepth: 1
    :caption: Contents

    project
    challenge
    backends/index
    config-samples
    contributing

.. toctree::
    :maxdepth: 1
    :caption: Backends

    backends/rctf/index
    backends/k8s/index

.. toctree::
    :maxdepth: 2
    :caption: API Reference

    api/project
    api/challenge


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
