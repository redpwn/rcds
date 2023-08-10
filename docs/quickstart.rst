Quickstart Guide
================

This guide will help you get started with using rcds, and deploying to both kubernetes and rctf backends.

This guide assumes that you have already set up a working rctf instance. It also assumes that you will be using GKE (Google Kubernetes Engine) as your kubernetes backend, and cloudflare as your DNS provider.

Using at least python version 3.9, clone this repository, and run the following command to install rcds onto your system:

.. code-block:: bash

    git clone https://github.com/redpwn/rcds
    cd rcds
    pip3 install .

Furthermore, also make sure to install the following tools onto your system.

- **kubectl**: Kubernetes command-line tool for interacting with clusters: `kubectl Installation Guide <https://kubernetes.io/docs/tasks/tools/#kubectl/>`_

- **helm**: Package manager for Kubernetes: `helm Installation Guide <https://helm.sh/docs/intro/install/>`_

- **gcloud**: Command-line interface for Google Cloud Platform (GCP):  `gcloud Installation Guide <https://cloud.google.com/sdk/gcloud>`_

- **docker-engine**: Used for building docker containers on your system: `docker Installation Guide <https://docs.docker.com/engine/install/>`_

First, create a folder or repository where you will be storing your challenges to deploy.

The directory structure should look like something like this:

.. code-block:: bash

    .
    ├── category1
    │   ├── challenge1
    │   │   ├── Dockerfile
    │   │   ├── challenge1.file
    │   │   └── challenge.yml
    │   ├── challenge2
    │   │   ├── Dockerfile
    │   │   ├── challenge2.file
    │   │   └── challenge.yml
    │   └── challenge3
    │       ├── Dockerfile
    │       ├── challenge3.file
    │       └── challenge3.yml
    │
    ├── category2
    │   ├── chalenge1...
    │
    └── rcds.yaml


If you want an example, check out AmateursCTF's challenge repository here:  `AmateursCTF Challenge Repository <https://github.com/les-amateurs/AmateursCTF-Public/tree/main/2023>`_

Inside the folder, create a file called ``rcds.yaml``. This file will contain the configuration for your deployment. An example of this config can be found at `Sample Configs <./config-samples#gke-and-rctf-on-gitlab-ci>`_

Configure the ``rcds.yaml`` file to match your deployment. More information about the configuration options can be found at `Configuration <./project>`_

Additionally, create a ``.env`` file. It should look like the following:

.. code-block:: env

    RCDS_RCTF_URL=https://ctf.example.com
    RCDS_RCTF_TOKEN=999omGulJ8OUxy+NNMmfV4VbErhHf5HTxRU07FKFdDYQmEGworLsxl2G6Hdl6BgrkYvhfAZoR0IEdE0XXlurGB1szIjdIk1whr3iSP2ZIdAC7chSDlk9SL/iN68J

You can obtain the token by creating an admin account (`Instructions here <https://rctf.redpwn.net/management/admin/>`_), copying the token from the admin page, and then url decoding it.

From google cloud, create a standard kubernetes cluster. Make sure that it is NOT an autopilot cluster, which google cloud will try to default to. If doing this through the UI, there should be an option on the top right to switch to a standard cluster.

Enable Dataplane V2 if it is not already enabled by default. Additionally, under the network settings tab, create a new tag called ``open-nodeports``. We will be using this later to configure the firewall.

Once the kubernetes cluster is created, click the connect button on the top bar of the cluster page and connect to the cluster using the command provided. This will set up your local kubectl configuration to connect to the cluster.

Additionally, we will need to create a container registry to store our docker images. To do this, go to the container registry page, and create a new registry. Make sure to select the same region as your kubernetes cluster.

Once the registry is created, we will need to configure docker to be able to push to this registry. To do this, right click on the registry, and click setup instructions on google cloud. This will give you a command to run to configure docker to push to this registry. Run this command on your local machine.

Make sure to configure your ``rcds.yaml`` file to match the name of your container registry.

Once that's done, go to the VPC Network tab of google cloud, and assign a static IP address to one of the nodes in your cluster. This will be the IP address that your challenges will be hosted on, so configure DNS to point to this IP address.

Additionally, configure firewall rules in the VPC Network tab to allow traffic for the allow-nodeports rule that we created earlier.

Once done, install the following helm charts onto your cluster:

- **Traefik**: In order to install Traefik, follow the guide provided in the Traefik documentation on using Helm charts: `Install Traefik using Helm <https://doc.traefik.io/traefik/getting-started/install-traefik/#use-the-helm-chart>`_

- **Cert-Manager**: For installing Cert-Manager, ensure that you install CRDs using the second option: `Install Cert-Manager with CRDs using Helm <https://cert-manager.io/docs/installation/helm/#3-install-customresourcedefinitions>`_

Once done, go to the VPC Network IP addresses tab, and convert the traefik IP address to a static IP address. This will be the IP address that your web challenges will be hosted on, so add a wildcard DNS entry to point to this IP address. For example, add an A record pointing at  ``*.example.com``.

Finally, we're going to configure the automatic TLS certificate generation. To do this, fill out the following template and name it ``certs.yml``:

.. code-block:: yaml

    apiVersion: v1
    kind: Secret
    metadata:
    name: cloudflare-token
    type: Opaque
    stringData:
    api-token: "API_TOKEN_GOES_HERE"
    ---
    apiVersion: cert-manager.io/v1
    kind: Issuer
    metadata:
    name: letsencrypt-issuer
    spec:
    acme:
        email: "EMAIL@GOES-HERE"
        server: https://acme-v02.api.letsencrypt.org/directory
        privateKeySecretRef:
        name: letsencrypt-issuer-key
        solvers:
        - dns01:
            cloudflare:
                apiTokenSecretRef:
                name: cloudflare-token
                key: api-token
    ---
    apiVersion: cert-manager.io/v1
    kind: Certificate
    metadata:
    name: wildcard-domain
    spec:
    secretName: wildcard-domain
    issuerRef:
        name: letsencrypt-issuer
        kind: Issuer
        group: cert-manager.io
    commonName: "*.DOMAIN.GOES.HERE"
    dnsNames:
        - "DOMAIN.GOES.HERE"
        - "*.DOMAIN.GOES.HERE"
    ---
    apiVersion: traefik.containo.us/v1alpha1
    kind: TLSStore
    metadata:
    name: default
    spec:
    certificates:
        - secretName: wildcard-domain
    defaultCertificate:
        secretName: wildcard-domain

You'll need to create a cloudflare API key with permissions to Edit zone DNS. Once you've replaced all the values inside ``certs.yml`` (email, domain, api token), run the following command to create the resources:

.. code-block:: bash

    kubectl apply -f certs.yml

You should now be good to go!

To deploy your challenges, run the following command to load your environment variables and deploy your challenges:

.. code-block:: bash

    env $(cat .env) rcds deploy
