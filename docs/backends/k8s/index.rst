``k8s`` --- Kubernetes
======================

This backend deploys challenges to a Kubernetes cluster. Each challenge is
deployed under its own namespace, and exposed via either a NodePort service or
an Ingress object, depending on the protocol specified by the challenge.  No
accommodations are currently being made in case of NodePort conflicts---it is
recommended that challenges are deployed to an isolated cluster (you should be
doing this anyways since Kubernetes currently does not have hard multi-tenancy).
A NetworkPolicy is also created to prevent network traffic from outside a
challenge's namespace reaching any containers which are not explicitly exposed.

Like with rCDS's Docker integration, the Kubernetes backend does not have a
dependency on any system commands (e.g. ``kubectl``); having a kubeconfig in the
standard location is all that is necessary.

Configuration
-------------

The only required option is ``domain``---NodePort services must be reachable on
this domain, and the cluster's ingress controller must be reachable on its
subdomains. For example, if ``domain`` is set as ``example.com``, then
``example.com`` must accept incoming TCP connections to NodePort services, and
``chall.example.com`` must be routed through the cluster's ingress controller.
It is your responsibility to set up the ingress controller.

Additional annotations on ingress and service objects can be specified through
the ``annotations`` key, and affinity and tolerations on pods can be set through
``affinity`` and ``tolerations``, respectively.

See the :ref:`backends/k8s#reference` for more details.

Recommended Cluster Configuration
---------------------------------

RBAC
~~~~

As always, we recommend running rCDS from a CI service; thus, rCDS will need to
authorize with your Kubernetes cluster. We have provided a ClusterRole which
grants the minimum privileges required by the Kubernetes backend (also
accessible here__):

.. __: https://github.com/redpwn/rcds/blob/master/docs/content/backends/k8s/cluster-role.yaml

.. literalinclude:: ./cluster-role.yaml
    :language: yaml

Cluster Operator
~~~~~~~~~~~~~~~~

We recommend `Google Kubernetes Engine`_, because it supports restricting of the
metadata server by Kubernetes service account, a feature called `Workload
Identity`_. This prevents SSRF from escalating into takeover of compute
resources.

.. _Google Kubernetes Engine: https://cloud.google.com/kubernetes-engine
.. _Workload Identity: https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity

Ingress
~~~~~~~

Traefik_ is recommended as an ingress controller, since it is very configurable
and supports JSON access logging for easy visibility into your challenges with
your cluster operator's logging solution. Consider manually issuing a wildcard
LetsEncrypt certificate and setting it as the default. Then, set annotations on
ingresses to use TLS, and configure Traefik to upgrade HTTP to HTTPS for full
HTTPS on challenges.

.. note::

    By default, Traefik will attempt to auto-detect Content-Type; apply the
    ``contentType`` middleware to disable this behavior if it breaks your
    challenges.

.. _Traefik: https://traefik.io/

.. _backends/k8s#reference:

Options Reference
-----------------

.. jsonschema:: ../../../rcds/backends/k8s/options.schema.yaml

Raw schema:

.. literalinclude:: ../../../rcds/backends/k8s/options.schema.yaml
    :language: yaml
