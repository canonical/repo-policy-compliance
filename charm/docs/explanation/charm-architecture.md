# Charm architecture

The Repo Policy Compliance charm is a Juju charm deploying and managing a [custom Flask application](https://github.com/canonical/repo-policy-compliance/tree/main/repo_policy_compliance)
that checks if a GitHub repository aligns with a chosen set of policies for workflow runs.

It leverages the [12-factor app support](https://canonical-12-factor-app-support.readthedocs-hosted.com/en/latest/) to pack a [Flask](https://flask.palletsprojects.com/en/stable/)
application providing the functionality as defined by the standard.

For a complete view on the architecture of a 12-factor charm, refer to the [12-factor architecture documentation](https://canonical-12-factor-app-support.readthedocs-hosted.com/en/latest/explanation/charm-architecture/). 

## OCI images

We use [Rockcraft's Flask framework extension](https://documentation.ubuntu.com/rockcraft/en/stable/reference/extensions/flask-framework/) to build OCI Images for Repo Policy Compliance. 
The images are defined in the [Repo-policy-compliance rock](https://github.com/canonical/repo-policy-compliance/blob/main/rockcraft.yaml).
They are published to [Charmhub](https://charmhub.io/), the official repository of charms.

> See more: [How to publish your charm on Charmhub](https://juju.is/docs/sdk/publishing)

## Juju events

For this charm, no additional event handling is defined. The default event handling coming from the 12-factor toolchain is enough to manage the charm's lifecycle.

## Charm code overview

The `src/charm.py` is the default entry point for a charm and has the FlaskCharm Python class which inherits from paas_app_charmer.flask.Charm, the base class 
from which all Flask app charms are formed, defined by [the Flask framework extension for Charmcraft](https://documentation.ubuntu.com/rockcraft/en/stable/reference/extensions/flask-framework/).

> See more in the Charmcraft docs: [Flask framework extension](https://canonical-charmcraft.readthedocs-hosted.com/en/stable/reference/extensions/flask-framework-extension//)
