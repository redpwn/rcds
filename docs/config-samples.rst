Sample Configs
==============

Multi-Container Web Challenge
-----------------------------

This challenge uses Redis and NGINX containers in addition to the main ``app``
container. The containers communicate with each other by host name. Adapted from
`Viper`_ from `redpwnCTF 2020`_.

.. code-block:: yaml

    name: viper
    author: Jim
    description: |-
      Don't you want your own ascii viper? No? Well here is Viper as a Service.
      If you experience any issues, send it
      [here](https://admin-bot.redpwnc.tf/submit?challenge=viper)

      Site: {{link}}

    flag:
      file: ./app/flag.txt

    provide:
      - ./viper.tar.gz

    containers:
      app:
        build: ./app
        resources:
          limits:
            cpu: 100m
            memory: 100M
        ports: [31337]
      nginx:
        build: ./nginx
        resources:
          limits:
            cpu: 100m
            memory: 100M
        ports: [80]
      redis:
        image: redis
        resources:
          limits:
            cpu: 100m
            memory: 100M
        ports: [6379]

    expose:
      nginx:
        - target: 80
          http: viper

.. _config-samples#gke-rctf-gitlab:

GKE and rCTF on GitLab CI
-------------------------

This is the configuration used for `redpwnCTF 2020`_.

.. code-block:: yaml

    # rcds.yaml
    docker:
      image:
        prefix: gcr.io/project/ctf/2020

    flagFormat: flag\{[a-zA-Z0-9_,.'?!@$<>*:-]*\}

    defaults:
      containers:
        resources:
          limits:
            cpu: 100m
            memory: 150Mi
          requests:
            cpu: 10m
            memory: 30Mi

    backends:
    - resolve: k8s
      options:
        kubeContext: gke_project_zone_cluster
        domain: challs.2020.example.com
        annotations:
          ingress:
            traefik.ingress.kubernetes.io/router.tls: "true"
            traefik.ingress.kubernetes.io/router.middlewares: "ingress-nocontenttype@kubernetescrd"
    - resolve: rctf
      options:
        scoring:
          minPoints: 100
          maxPoints: 500

.. code-block:: yaml

    # .gitlab-ci.yml
    image: google/cloud-sdk:slim

    services:
      - docker:dind

    stages:
      - deploy

    variables:
      DOCKER_HOST: tcp://docker:2375
      RCDS_RCTF_URL: https://2020.example.com/

    before_script:
      - pip3 install rcds
      - gcloud auth activate-service-account service-account@project.iam.gserviceaccount.com --key-file=$GCLOUD_SA_TOKEN
      - gcloud config set project project
      - gcloud auth configure-docker gcr.io --quiet
      - gcloud container clusters get-credentials cluster --zone=zone

    deploy:
      stage: deploy
      when: manual
      environment:
        name: production
      script:
        - rcds deploy

The config creates Kubernetes Ingress objects compatible with Traefik, and
references the following middleware CRD exists to disable Traefik's
Content-Type auto-detection (change the name and namespace, both in the CRD and
the ingress annotation, to suit your setup):

.. code-block:: yaml

    apiVersion: traefik.containo.us/v1alpha1
    kind: Middleware
    metadata:
      name: nocontenttype
      namespace: ingress
    spec:
      contentType:
        autoDetect: false

.. _Viper: https://github.com/redpwn/redpwnctf-2020-challenges/blob/master/web/viper/challenge.yaml
.. _redpwnCTF 2020: https://2020.redpwn.net/
