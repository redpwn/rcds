Deployment Backends
===================

rCDS uses a pluggable backend model for the task of actually deploying
challenges to infrastructure. rCDS contains a few built-in backends, and
third-party backends may be loaded by specifying their module name.

Backends are specified in the top-level configuration :file:`rcds.yaml`:

.. code-block:: yaml

    backends:
    - resolve: name
      options:
        key: value

The top-level key ``backends`` is an array of backend objects, which consist of
their name (``resolve``) and the options for the backend (``options``).
``resolve`` first attempts to load a built-in backend of the corresponding name,
and, if it does not exist, then interprets the name as a package name and loads
from it.

Each backend may also modify the ``challenge.yaml`` schema---be sure to read
the docs for the backends you are using to understand challenge options specific
to that backend.

.. _backends#scoreboard:

Scoreboard Backends
-------------------

These are responsible for displaying the challenge to competitors; they handle
uploading the challenge's metadata (description, flags, point value, etc) and
any assets that are served to competitors.

- :doc:`rCTF <rctf/index>`

.. _backends#container-runtime:

Container Runtime Backends
--------------------------

These are responsible for running the built challenge containers. By design,
none of the built-in backends will start containers on the machine that rCDS is
being run from.

- :doc:`Kubernetes <k8s/index>`
