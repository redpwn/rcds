.. rCDS documentation master file, created by
   sphinx-quickstart on Fri Apr 10 17:12:14 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

rCDS - A CTF Challenge Deployment Tool
======================================

rCDS is redpwn_'s CTF challenge deployment tool. It is designed to automate the
entire challenge deployment process, taking sources from challenge authors and
provisioning the necessary resources to both make challenges available on the
competition scoreboard and to spin up Docker containers that the challenge needs
to run.

If you are a challenge author for a CTF using rCDS, head over to the
:doc:`challenge config format docs <challenge>`.

.. _redpwn: https://redpwn.net/

.. toctree::
    :hidden:

    Introduction <self>

.. toctree::
    :maxdepth: 1
    :caption: Contents

    project
    challenge
    backends/index
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
