# Table of Contents
1. [repo-policy-compliance](#introduction) 
2. [Get started](#get-started)
    1. [What you'll need](#what-youll-need) 
    2. [Set up](#set-up)
    3. [Deploy](#deploy)
    4. [Generate an authentication token and test](#token)
3. [Integrations](#integrations)
4. [Next steps](#next-steps)
    1. [Learn more](#learn-more)
    2. [Join the community](#join-the-community)
5. [License](#license)

------------------------------------------------------------------------------------------------

# repo-policy-compliance <a name="introduction"></a>

A Juju charm of a Flask application to check if a GitHub repository aligns with the policies for workflow runs. This charm consists of a Python package containing functions to check for compliance of various policies.

This charm works in the context of the `github-runner` charm and should be deployed and configured for the self-hosted runners' use in OpenStack mode. The self-hosted runners execute runs in an internal environmental and can execute arbitrary code; the `repo-policy-compliance` charm verifies that the GitHub repository is set up for compliance and that only authorised code is executed. For more information, read the [GitHub runner charm documentation](https://charmhub.io/github-runner). 

Like any Juju charm, this charm supports one-line deployment, configuration, integration, scaling, and more. For `repo-policy-compliance`, this includes:
* Customising enabled policies 
* Running in debug mode
* Choosing different GitHub authentication methods
* Modifying Flask-specific features like a secret key for security-related needs, the run environment (e.g., production) or where the application is mounted

See the [Actions](https://charmhub.io/repo-policy-compliance/actions) and [Configurations](https://charmhub.io/repo-policy-compliance/configurations) tabs to learn more about the actions and configurations supported by this charm.

## Get started <a name="get-started"></a>
### What you'll need <a name="what-youll-need"></a>
* A Kubernetes cloud.
* Juju 3 installed and a controller created.

### Set up <a name="set-up"></a>
Create a Juju model:
```
juju add-model prod-repo-policy-compliance
```

### Deploy <a name="deploy"></a>
Deploy the charms:

```
juju deploy postgresql-k8s --trust --channel 14/edge
juju deploy repo-policy-compliance repo-policy --config charm_token=abc --config github_token="github_pat_foobar" --channel latest/edge
```
	

> NOTE: For `repo-policy-compliance` to work, the `charm_token` and `github_token` configurations must be set. The `charm_token` is
> chosen by you and must be shared with the authenticating client to generate one-time token authentication. 
> The `github_token` is either a GitHub Personal Access Token (with repo scope) or a fine-grained token with read permission for Administration. 
> Read more about allowed GitHub authentication methods in the [Reference document](https://github.com/canonical/repo-policy-compliance/blob/main/charm/docs/reference/github-auth.md).

Integrate PostgreSQL and `repo-policy-compliance`:

```
juju integrate postgresql-k8s repo-policy
```

Wait for both charms to reach an active idle state by monitoring `juju status`. The output should look similar to the following:

```
Model        Controller  Cloud/Region        Version  SLA          Timestamp
repo-policy  microk8s    microk8s/localhost  3.1.8    unsupported  12:21:02+02:00

App             Version  Status  Scale  Charm                   Channel      Rev  Address         Exposed  Message
postgresql-k8s  14.12    active      1  postgresql-k8s          14/edge      272  10.152.183.64   no       Primary
repo-policy              active      1  repo-policy-compliance  latest/edge   66  10.152.183.139  no       

Unit               Workload  Agent  Address      Ports  Message
postgresql-k8s/0*  active    idle   10.1.72.161         Primary
repo-policy/0*     active    idle   10.1.72.167           
```

### Generate an authentication token and test <a name="token"></a>

Generate a one-time authentication token for `repo-policy-compliance` using `curl` and save it as the `ONE_TIME_TOKEN` environment variable. You will need the IP address of the Unit for the `repo-policy-compliance` charm; in the example output above, 10.1.72.167 is the necessary IP address. You will also need the token used for `charm_token` configuration (in this example, "abc"). 

```
ONE_TIME_TOKEN=$(curl http://10.1.72.167:8000/one-time-token -H"Authorization: Bearer abc" )
```

The variable should look similar to the following:
```
d156dda1f03df9d42fd788d93799c57b4275ca5facccce92ef9b91cf4fc13f6a%
```

Finally, use the `repo-policy-compliance` Unit IP address and the one-time token to check for compliance on a GitHub repository formatted as `OWNER/REPO`. 

```
curl -i http://10.1.72.167:8000/push/check-run -H"Authorization: Bearer $ONE_TIME_TOKEN" --data '{"repository_name": "OWNER/REPO"}' -H"Content-Type: application/json"
```

The output should look similar to the following:

```
HTTP/1.1 204 NO CONTENT
Server: gunicorn
Date: Wed, 11 Sep 2024 12:09:11 GMT
Connection: close
Content-Type: text/html; charset=utf-8
```

"NO CONTENT" indicates that the repository is compliant.

## Integrations <a name="integrations"></a>

The `repo-policy-compliance` charm requires a PostgreSQL integration over the [postgresql_client](https://charmhub.io/integrations/postgresql_client) interface. While it is optional, an integration with ingress (for instance, [`nginx-ingress-integrator`](https://charmhub.io/nginx-ingress-integrator)) makes the `repo-policy-compliance` charm accessible from outside the Kubernetes cluster.

The integration between `repo-policy-compliance` and `github-runner` is not handled through Juju. In the GitHub runner charm, you create the integration to `repo-policy-compliance` by setting the configuration options [`repo-policy-compliance-url`](https://charmhub.io/github-runner/configurations#repo-policy-compliance-url) and [`repo-policy-compliance-token`](https://charmhub.io/github-runner/configurations#repo-policy-compliance-token) for the URL and token respectively.

All other integrations are standard [COS](https://charmhub.io/topics/canonical-observability-stack) integrations and optional. See the [Integrations tab](https://charmhub.io/repo-policy-compliance/integrations) for more details.

## Next steps <a name="next-steps"></a>
### Learn more <a name="learn-more"></a>
* GitHub repository: [repo-policy-compliance](https://github.com/canonical/repo-policy-compliance)
* [GitHub runner charm documentation](https://charmhub.io/github-runner)

### Join the community <a name="join-the-community"></a>
The `repo-policy-compliance` charm is a member of the Ubuntu family. It’s an open-source project that warmly welcomes community projects, contributions, suggestions, fixes, and constructive feedback.

* [Code of conduct](https://ubuntu.com/community/code-of-conduct)
* [Get support](https://discourse.charmhub.io/)
* [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
* [Contribute](https://github.com/canonical/repo-policy-compliance/blob/main/CONTRIBUTING.md)


## License <a name="license"></a>
The `repo-policy-compliance` charm is free software, distributed under the Apache Software License, version 2.0. 
