:mod:`rcds.challenge` - Challenges
==================================

.. module:: rcds.challenge

.. autoclass:: rcds.ChallengeLoader
    :members:

.. autoclass:: rcds.Challenge
    :members:

:mod:`rcds.challenge.docker` - Docker containers
------------------------------------------------

.. module:: rcds.challenge.docker

.. autofunction:: get_context_files
.. autofunction:: generate_sum

.. autoclass:: ContainerManager
    :members:

    .. automethod:: __init__

.. autoclass:: Container
    :members:

    .. autoattribute:: IS_BUILDABLE

.. autoclass:: BuildableContainer
    :members:

    .. autoattribute:: IS_BUILDABLE
