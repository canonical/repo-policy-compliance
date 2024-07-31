# repo-policy-compliance
Tool to check a GitHub repository for compliance with policy

The module exposes several functions to check for compliance with the following
policies:

* `target_branch_protection`: That the branch targeted by a pull request has
  protection enabled and that rules cannot be bypassed. The requirement for
  reviews is relaxed for non-default branches where both the source and target
  branch are on the repository.
* `collaborators`: Check that all outside collaborators of the project have at
  most `read` permissions.
* `execute_job`: That a user with write permission or above has left the comment
  `/canonical/self-hosted-runners/run-workflows <commit SHA>` approving a
  workflow run for a specific commit SHA. Only applicable to forked source
  branches.
* `pull_request`: Runs `target_branch_protection`, `collaborators` and
  `execute_job`.
* `workflow_dispatch`: Runs `collaborators`.
* `push`: Runs `collaborators`.
* `schedule`: Runs `collaborators`.

These policies are designed for workflow runs in the context of a pull request.

## Customizing Enabled Policies

Each of `pull_request`, `workflow_dispatch`, `schedule` and `push` accept a
`policy_document` argument which can be used to change which policies are
enabled. If supplied, it should be a dictionary that complies with the
[policy JSON schema](repo_policy_compliance/policy_schema.yaml).

If nothing is supplied for a particular policy (e.g.,
`pull_request.target_branch_protection`) it is treated as enabled.

## Flask Blueprint

The functions are made available via a
[flask blueprint](repo_policy_compliance/blueprint.py). This is designed to run
in a single thread for simplicity.

The blueprint exposes an endpoint `/always-fail/check-run` that simulates a
failing check to be used for testing purposes.

## Running the Tests

There are two types of test: the application test and the charm test.

### Application tests
To run the application tests, the `AUTH_GITHUB_TOKEN` environment variable must be set. This
should be a token of a user with full repo permissions for the test repository. 
You can also pass in `AUTH_APP_ID`, `AUTH_INSTALLATION_ID`, and `AUTH_PRIVATE_KEY` 
to test the authentication using GitHub App Auth. In that case, the tests will additionally
be executed using GitHub App auth. Note that the GitHub app should be installed
in the test repository organisation/user namespace, with access granted to the test repository
and in the user namespace that owns the GitHub token with access to the forked repository.

The command `tox -e test` can be used to run all tests, which are primarily integration tests.
You can also select the repository against which to run the tests by setting
the `--repository` flag. The tests will fork the repository and create PRs against it.
Note that the tests are currently designed to work for specific Canonical repositories, 
and may need to be for other repositories 
(e.g. `tests.app.integration.test_target_branch_protection.test_fail` 
assumes that certain collaborators are in the `users_bypass_pull_request_allowances` list).
Also note that the forks are created in the personal space of the user whose token is being used, 
and that the forks are not deleted after the run. 
The reason for this is that it is only possible to create one fork of a repository, 
and deleting it would interfere with concurrent runs, 
which can happen for multiple PRs at the same time.
It is also possible to pass a `CI_GITHUB_TOKEN` per env variable for a
bot to test things like comments from a user with no write permissions or above.

GitHub actions should have access to the GitHub token via a secret
called `PERSONAL_GITHUB_TOKEN`. It is recommended to use either a fine-grained PAT or a 
token that is short-lived, e.g. 7 days. When it expires, a new token must be set.
For the GitHub App Auth, the `TEST_GITHUB_APP_ID`, `TEST_GIHUB_APP_INSTALLATION_ID`, and
`TEST_GITHUB_APPP_RIVATE_KEY` should be set as secrets.

### Charm tests

To run the charm tests, a valid GitHub token (permissions do not matter) must be passed
to the `tox` command using the `--github-token` flag. You will also need to pass the charm file
using the `--charm-file` flag and the OCI image using the `--repo-policy-compliance-image` command.
The `tox -e charm-integration-test` command can be used to run the tests.
For example

```bash
tox -e charm-integration-test -- --model testing --keep-models --charm-file=./repo-policy-compliance_ubuntu-22.04-amd64.charm --repo-policy-compliance-image=ghcr.io/canonical/repo-policy-compliance:5ed6216396522d813c06d5b0e709b72bbec6d6e0-_1.8.4_amd64 --github-token=<token>.
```
