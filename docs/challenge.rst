``challenge.yaml`` --- Challenge Config
=======================================

The file ``challenge.yaml`` defines the configuration for a challenge within an
rCDS project. ``.yml`` and ``.json`` files are also supported.

Basics
------

``id`` --- the identifier for this challenge. Must be unique project wide. This
key is set automatically from the name of the directory the challenge is in;
unless you have a very good reason to, don't set this in ``challenge.yaml``.

``author`` -- a string or list of strings containing the authors for this
challenge.

``description`` -- self-explanatory. It is in Markdown format and will be
processed with Jinja_. See :ref:`challenge#templating` for more details.

``category`` -- self-explanatory. If the challenge directory is exactly two
directories deep (for example, ``/pwn/chall``, where ``/`` is the project root),
this is set from the parent directory of the challenge's directory ("pwn" in the
previous example). We recommend organizing your challenges in a
:samp:`{category}/{chall}` structure.

``flag`` --- the flag for the challenge. If it is a string, then the flag is set
to the string verbatim. Otherwise, if ``flag.file`` is set, the flag is loaded
from the specified file (relative to the challenge root), and stripped of
leading and trailing whitespace. If ``flag.regex`` is set, the flag is anything
matching the given regex. A warning is emitted if the flag contains multiple
lines (usually this is from an improperly configured flag file).

``provide`` --- an array of files to provide to competitors as downloads. The
files can either be a string, in which case they are interpreted as the path to
the file, or an object with the ``file`` and ``as`` properties; these properties
define the path and the displayed name of the file, respectively.

``value`` --- point value of this challenge. Meaning is defined by the
scoreboard backend.

``visible`` --- if set to ``false``, the scoreboard backend will act as if this
challenge does not exist.

.. warning::

    Most scoreboard backends will delete any challenges that were created by
    rCDS but now no longer exist---switching ``visible`` to ``false`` after the
    challenge has already been deployed may cause solves to be lost.

Deployment
----------

In rCDS, you define first define all of the :ref:`containers
<challenge#containers>` that your challenge needs to run, and then declare how
you want them :ref:`exposed <challenge#expose>` to the world.

``deployed`` --- whether or not this challenge's containers should be deployed.
Defaults to ``true``.

.. _challenge#containers:

Containers
~~~~~~~~~~

The ``containers`` key is an object whose keys are the names of the containers
this challenge creates. These containers can either use an existing image, or
specify a path to a Dockerfile to build from. Each container must declare all
ports that need to be connected to, both from other containers and by
competitors; which ports are exposed to competitors are specified
:ref:`separately <challenge#expose>`. Containers from the same challenge can
connect to each other via a DNS lookup of their names; for example, if a
container ``app`` is defined, another container can connect to any of ``app``'s
declared ports by looking up the name ``app``.

Whether a container needs to be rebuilt is determined by looking at every file
in the Docker build context. Thus, it is very important that you include only
what is necessary in the build context by using a ``.dockerignore`` file; at
minimum, ``challenge.yaml`` should be excluded to prevent needing to rebuild the
container when the challenge's description is updated.

``image`` --- the tag of an existing image to run

``build`` --- settings for building this container. If it is a string, then it
is the path to the Docker build context (the directory where a Dockerfile is).
It can also be an object for advanced configuration:

``build.context`` --- path to the Docker build context.

``build.dockerfile`` --- path to the Dockerfile, relative to the build context
root.

``build.args`` --- Docker build args to set when building the container.
Key-value object.

``ports`` --- a list of integers of the port numbers this container listens on.
If anything needs to connect to a port on the container, list it here.

``replicas`` --- number of replicas of this container to run (on backends that
support it). Defaults to 1. Leave at 1 for stateful containers.

``environment`` --- key-value object of environment variables to set.

``resources`` --- resource limits on the container. See `Kubernetes's
documentation`__ on the format of this value (only ``cpu`` and ``memory`` are
implemented).

.. __: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/

.. _challenge#expose:

Expose
~~~~~~

The top-level ``expose`` key defines all of the ports on :ref:`containers
<challenge#containers>` that should be exposed to competitors. It is an object
whose keys correspond to the names of defined containers, and whose values are
arrays of port objects. These objects each describe how one port should be
exposed.

``target`` --- the port on the container that this rule is targeting.

``tcp`` --- if specified, this port should be treated as TCP. The value is the
port at which it is exposed on, on the challenge host.

``http`` --- if specified, this port should be treated as HTTP, and will be
reverse proxied with TLS termination. The value is a string, the subdomain name
on which the challenge will be hosted. Alternatively, it can be an object with a
``raw`` key, in which case ``http.raw`` contains the FQDN that the challenge
will be served on. When using ``http.raw``, rCDS will handle the virtual
hosting, however as a challenge author, you will need to coordinate with your
infrastructure admin on setting up TLS and DNS records.

.. _challenge#templating:

Templating
----------

Challenge descriptions are rendered using Jinja_. The contents of the
challenge's config is available on the ``challenge`` object in the Jinja
environment. Some fields are altered with more concrete versions of their
contents---for example, the ``http`` key on ``expose`` port objects will contain
the fully-qualified domain name, instead of just the prefix. Container backends
will also add a ``host`` key to a TCP ``expose`` port, which contains the host at
which that port will be accessible.

.. note::

    An example configuration:

    .. code-block:: yaml

        # challenge.yaml
        ...
        description: |
          1: {{ challenge.expose.main[0].http }}

          2: {{ challenge.expose.main[1].host }}:{{ challenge.expose.main[1].tcp }}
        containers:
          main:
            ports: [1337, 1338]
        expose:
          main:
          - target: 1337
            http: leet
          - target: 1338
            tcp: 31253

    Assuming the container backend is hosted on example.com, the description
    would render as:

    1: leet.example.com

    2: example.com:31253

There are also shortcuts available for the most common use-case: a single
exposed port. ``host`` is the hostname under which the port is accessible.
``link`` will automatically create a Markdown link to the exposed port, and
``url`` will create just the URL without the accompanying Markdown.  This works
for both HTTP and TCP ports, since you may want to expose a challenge which
breaks behind a reverse proxy as TCP. For TCP ports, there is also ``port``,
which is the exposed port number of the port, and ``nc``, which
will create a ``nc`` command to connect to the challenge---it is equivalent to
``nc {{ host }} {{ port }}``.

.. _Jinja: https://jinja.palletsprojects.com

Reference
---------

.. jsonschema:: ../rcds/challenge/challenge.schema.yaml

Raw schema:

.. literalinclude:: ../rcds/challenge/challenge.schema.yaml
    :language: yaml
