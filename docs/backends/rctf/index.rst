``rctf`` --- rCTF
=================

This backend deploys challenges to rCTF_. The options ``url`` and ``token``
specify the URL of the rCTF instance and the token of the admin account to use,
respectively. Both of these will be set from the environment variables
``RCDS_RCTF_URL`` and ``RCDS_RCTF_TOKEN`` respectively, if they exist.
Challenges with a ``value`` set are assumed to be statically-scored; all other
challenges are dynamically-scored according to the global ``scoring`` config
(between ``scoring.minPoints`` and ``scoring.maxPoints``). rCTF does not support
regex flags.

.. _rCTF: https://rctf.redpwn.net/

The ``sortOrder`` option allows you to automatically set the ``sortWeight``
fields on challenges based on an ordering provided in this key. Listed
challenges are assigned a ``sortWeight`` equal to its index in the array
multiplied by -1. This means that if all the challenges have the same score and
solve count, they will be displayed with the first element of the array at the
top.

Additional Challenge Properties
-------------------------------

``author`` and ``category`` are required.

``tiebreakEligible`` (bool): whether or not this challenge factors into time-based
tiebreakers. Defaults to ``true``.

``sortWeight`` (number): rCTF sort weight parameter. Ignored if the challenge is
listed in the global ``sortOrder`` option. Defaults to ``0``.

Options Reference
-----------------

.. jsonschema:: ../../../rcds/backends/rctf/options.schema.yaml

Raw schema:

.. literalinclude:: ../../../rcds/backends/rctf/options.schema.yaml
    :language: yaml
