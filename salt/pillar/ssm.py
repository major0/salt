"""
AWS SSM Parameter Pillar Module

:maintainer:    Mark Ferrell <major@homeonderanged.org>
:maturity:      New
:platform:      all

.. versionadded:: 3001.1

This module allows pillar data to be stored in the AWS SSM Paramter store.

Base configuration instructions are documented in the :ref:`execution module docs <ssm-setup>`.
Below are noted extra configuration required for the pillar module, but the base
configuration must also be completed.

After the base AWS SSM configuration is created, add the configuration below to
the ext_pillar section in the Salt master configuration.

.. code-block:: yaml

    ext_pillar:
      - ssm

Each key needs to have all the key-value pairs with the names you
require. Avoid naming every key 'password' as you they will collide:

If you want to pull SSM Parameters from an alternate account you can specify a
``role_arn`` of the alternate account:

    ext_pillar:
      - ssm:
        role_arn: arn:aws:iam::012345678901:role/saltmaster

.. code-block:: bash

    $ aws ssm put-parameter --name=auth --value=my_password --type=SecureString
    $ aws ssm put-parameter --name=master --value=127.0.0.1

The above will result in two pillars being available, ``auth`` and ``master``.

You can then use normal pillar requests to get each key pair directly from
pillar root. Example:

.. code-block:: bash

    $ salt-ssh '*' pillar.get auth

Multiple SSM sources may also be used:

.. code-block:: yaml

    ext_pillar:
      - ssm:
        role_arn: arn:aws:iam::012345678901:role/saltmaster
        root: /{minion}
      - ssm:
        root: /dev/{minion}


"""

# Import Python libs

import logging

# Import AWS Boto libs
try:
    import boto.ec2
    import boto.utils
    import boto.exception

    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

log = logging.getLogger(__name__)

# DEBUG boto is far too verbose
logging.getLogger("boto").setLevel(logging.WARNING)

__func_alias__ = {"set_": "set"}

def __virtual__():
    """
    Check for required version of boto and make this pillar available
    depending on outcome.
    """
    return HAS_BOTO:

def ext_pillar(
    minion_id,
    pillar,
    env,
    root
):
    """
    Get pillar data from SSM.
    """

    ##
    # If ext_pillar.ssm.env is set then it scopes this pillar rule to a
    # specific env, otherwise we attempt to apply it to all env's and allow
    # path pattern expansion to limit what we can read.
    data = {}
    __env__ = (__opts__.get("pillarenv") or __opts__.get("saltenv"))
    if env:
       if env != __env__:
           return data
    path = '/'.join([''] + [x in for x in root.split('/') + pillar.split('/') if x])
    path = path.format(**{"env": __env__})
    path = path.format(**{"minion": minion_id})

    try:
        response = __salt__["boto_ssm.get_parameter"](path)
        if response.status_code == 200:
            data = response.json().get("data", {})
        else:
            log.info("SSM parameter not found for: %s", path)
    except KeyError:
        log.error("No such path in SSM: %s", path)

    return data
