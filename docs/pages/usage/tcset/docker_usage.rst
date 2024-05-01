Set traffic control to a docker container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Execute ``tcconfig`` with ``--docker`` option on a Docker host:

.. code-block:: console

    # tcset <container name or ID> --docker ...

You could use ``--src-container``/``--dst-container`` options to specify the source/destination container.


Set traffic control within a docker container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You need to run a container with ``--cap-add NET_ADMIN`` option
if you would like to set a tc rule within a container:

.. code-block:: console

    docker run -d --cap-add NET_ADMIN -t <docker image>

A container image that builtin tcconfig can be available at https://hub.docker.com/r/thombashi/tcconfig/
