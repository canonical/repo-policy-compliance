A [Kubernetes charm](https://canonical-juju.readthedocs-hosted.com/en/latest/user/reference/charm/charm-taxonomy/#kubernetes)
that checks if a GitHub repository aligns with a chosen set of policies for workflow runs.

When using the `github-runner` charm to deploy and manage your self-hosted runners in OpenStack mode,
the self-hosted runners can execute arbitrary code. This may hurt compliance. Deploying the
`repo-policy-compliance`charm and exposing it to the `github-runner` charm ensures that only authorized
code is executed, and so your GitHub repository remains compliant.
For more information, read the [GitHub runner charm documentation](https://charmhub.io/github-runner). 

Like any Juju charm, this charm supports one-line deployment, configuration, integration, scaling, and
more. For the `repo-policy-compliance` charm, this includes the ability to:
* Customize enabled policies.
* Run in debug mode.
* Choose different GitHub authentication methods.
* Modify Flask-specific features like a secret key for security-related needs, the run environment
  (e.g., production) or where the application is mounted.

See the [Actions](https://charmhub.io/repo-policy-compliance/actions) and
[Configurations](https://charmhub.io/repo-policy-compliance/configurations) tabs to learn more about the
actions and configurations supported by this charm.

**Contents**
1. [Policies](#policies)
2. [Get started](#get-started)
    1. [Requirements](#requirements) 
    2. [Set up](#set-up)
    3. [Deploy](#deploy)
    4. [Generate an authentication token and test](#token)
3. [Integrations](#integrations)
4. [Learn more](#learn-more)
5. [Project and community](#project-and-community)
6. [License](#license)


------------------------------------------------------------------------------------------------

## Policies 

The charm exposes several functions to check for compliance with the following
policies:

* `target_branch_protection`: That the branch targeted by a pull request has
  protection enabled and that rules cannot be bypassed. The requirement for
  reviews is relaxed for non-default branches where both the source and target
  branch are on the repository.
* `collaborators`: That all outside collaborators of the project have at
  most `read` permissions.
* `execute_job`: That a user with write permission or above has left the comment
  `/canonical/self-hosted-runners/run-workflows <commit SHA>` approving a
  workflow run for a specific commit SHA. Only applicable to forked source
  branches.
* `disallow_fork`: That the fork is external. If set to `false`, the check will fail.
  Can be enabled by [a configuration option](https://github.com/canonical/repo-policy-compliance/blob/main/charm/charmcraft.yaml#L52).


Furthermore, Repo Policy Compliance provides the following endpoints to check the above policies 
for GitHub events:

* `pull_request`: If enabled, runs `disallow_fork`. Otherwise runs
  `target_branch_protection`, `collaborators` and `execute_job`. 
* `workflow_dispatch`: Runs `collaborators`.
* `push`: Runs `collaborators`.
* `schedule`: Runs `collaborators`.

## Get started 
This section provides a brief overview on deploying, configuring and integrating the
`repo-policy-compliance` charm for basic usage.

### Requirements 
* [A Kubernetes cloud](https://canonical-juju.readthedocs-hosted.com/en/3.6/user/reference/cloud/#machine-clouds-vs-kubernetes-clouds).
* Juju 3 installed and a controller created. You can accomplish this process by using a Multipass VM as outlined in this guide: [Juju | Manage your deployment environment](https://canonical-juju.readthedocs-hosted.com/en/latest/user/howto/manage-your-deployment/manage-your-deployment-environment/#set-things-up).
* A GitHub repository (formatted as `OWNER/REPO`) for which you want to check compliance.
* A GitHub Personal Access Token with repo scope.

### Set up 
Create a Juju model:
```
juju add-model prod-repo-policy-compliance
```

### Deploy
Deploy the `repo-policy-compliance` charm as the `repo-policy` application, configuring at the same time its charm token and GitHub token:
```
juju deploy repo-policy-compliance repo-policy --config charm_token=abc --config github_token="github_pat_foobar" --channel latest/stable
```

PostgreSQL is required in order to use Repo Policy Compliance. Deploy the `postgresql-k8s` charm:
```
juju deploy postgresql-k8s --trust 
```

> NOTE: For `repo-policy-compliance` to work, you must set the `charm_token` and `github_token` configurations. The `charm_token` is
> chosen by you and must be shared with the authenticating client to generate one-time token authentication. 
> The `github_token` is either a GitHub Personal Access Token (with repo scope) or a fine-grained token with read permission for Administration. 
> Read more about allowed GitHub authentication methods in the [Reference document](https://charmhub.io/repo-policy-compliance/docs/reference-github-auth).

Integrate PostgreSQL and Repo Policy Compliance:

```
juju integrate postgresql-k8s repo-policy
```

Monitor the status:
```
juju status --watch 1s
```

Wait for both applications to reach an active idle state. The output should look similar to the following:

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

Note the IP address of the `repo-policy/0` unit; in the example output above, 10.1.72.167 is the necessary IP address. 

Use <kbd>Ctrl</kbd> + <kbd>C</kbd> to exit.

### Generate an authentication token and test 

Now generate a one-time authentication token for Repo Policy Compliance using `curl` and save it as the `ONE_TIME_TOKEN` environment variable. You will need the IP address of the `repo-policy/0` unit (in this example, 10.1.72.167). You will also need the token used for `charm_token` configuration (in this example, "abc"). 

```
ONE_TIME_TOKEN=$(curl http://10.1.72.167:8000/one-time-token -H"Authorization: Bearer abc" )
```

The variable should look similar to the following:
```
d156dda1f03df9d42fd788d93799c57b4275ca5facccce92ef9b91cf4fc13f6a%
```

Finally, use the `repo-policy-compliance` unit IP address and the one-time token to check for compliance on a GitHub repository formatted as `OWNER/REPO`. 

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

The `204` status code indicates that the repository is compliant.

## Integrations

The `repo-policy-compliance` charm requires a PostgreSQL integration over the [postgresql_client](https://charmhub.io/integrations/postgresql_client) interface. 

To make this charm accessible from outside the Kubernetes cluster, integrate with an ingress charm (for instance, [`nginx-ingress-integrator`](https://charmhub.io/nginx-ingress-integrator)).

To integrate this charm with the `github-runner` charm, the integration is not handled by Juju. In the GitHub runner charm, you create the integration to `repo-policy-compliance` by setting the configuration options [`repo-policy-compliance-url`](https://charmhub.io/github-runner/configurations#repo-policy-compliance-url) and [`repo-policy-compliance-token`](https://charmhub.io/github-runner/configurations#repo-policy-compliance-token) for the URL and token respectively. See the [GitHub runner charm documentation](https://charmhub.io/github-runner) for more details. 

All other supported integrations are with the [Canonical Observability Stack](https://charmhub.io/topics/canonical-observability-stack). See the [Integrations tab](https://charmhub.io/repo-policy-compliance/integrations) for more details.

## See also
* GitHub repository: [repo-policy-compliance](https://github.com/canonical/repo-policy-compliance)
* [GitHub runner charm documentation](https://charmhub.io/github-runner)

### Project and community
The `repo-policy-compliance` charm is a member of the Ubuntu family. It’s an open-source project that warmly welcomes community projects, contributions, suggestions, fixes, and constructive feedback.

* [Code of conduct](https://ubuntu.com/community/code-of-conduct)
* [Get support](https://discourse.charmhub.io/)
* [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
* [Contribute](https://github.com/canonical/repo-policy-compliance/blob/main/CONTRIBUTING.md)


## License
Repo Policy Compliance Documentation
Copyright 2025 Canonical Ltd.

This work is licensed under the Creative Commons Attribution-Share Alike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 171 Second Street, Suite 300, San Francisco, California, 94105, USA.

# Navigation

| Level | Path | Navlink |
| -- | -- | -- |
| 1 | reference | [Reference]() |
| 2 | reference-github-auth | [GitHub Authentication](/t/repo-policy-compliance-docs-github-authentication/15556) |
