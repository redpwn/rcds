``rcds.yaml`` --- Project Config
================================

The file ``rcds.yaml`` defines the configuration for the current project, and
its location also defines the root of the project. ``.yml`` and ``.json`` files
are also supported. Challenges will be searched for in subdirectories of the
project root. This file contains various global configuration options, including
for the :doc:`backends </backends/index>` and :ref:`Docker containers
<project#docker>`

.. _backends: ../backends/

.. _project#docker:

Docker
------

``docker.image.prefix`` *(required)* --- the prefix for generated Docker image
tags. This should contain the registry and "directory" --- e.g.
``gcr.io/redpwn/challs``.

``docker.image.template`` --- the Jinja template to create image tags with; it
is joined with ``docker.image.prefix``. Defaults to ``rcds-{{ challenge.id }}-{{
container.name }}``.

Misc
----

``defaults`` --- default options to set on challenges. This key takes an object of
the same shape as ``challenge.yaml``. Setting defaults on keys like ``expose``
and ``containers`` will apply the defaults to all exposed ports and containers,
respectively.

.. note::

    An example of setting default resource limits on all containers which don't
    otherwise specify limits:

    .. code-block:: yaml

        defaults:
          containers:
            resources:
              limits:
                cpu: 100m
                memory: 150Mi
              requests:
                cpu: 10m
                memory: 30Mi

``flagFormat`` --- a regex to test all (static) flags against.

Reference
---------

.. jsonschema:: ../rcds/project/rcds.schema.yaml

Raw schema:

.. literalinclude:: ../rcds/project/rcds.schema.yaml
    :language: yaml
