# repo-policy-compliance
Tool to check a GitHub repository for compliance with policy

The module exposes several functions to check for compliance with the following
policies:

* `target_branch_protection`: That the branch targeted by a pull request has
  protection enabled, stale reviews are dismissed and that rules cannot be
  bypassed. The requirement for reviews is relaxed for non-default branches
  where both the source and target branch are on the repository.
* `collaborators`: Check that all outside collaborators of the project have at
  most `read` permissions.
* `execute_job`: That a user with write permission or above has left the comment
  `/canonical/self-hosted-runners/run-workflows <commit SHA>` approving a
  workflow run for a specific commit SHA. Only applicable to forked source
  branches.
* `pull_request`: Runs `target_branch_protection`, `collaborators` and
  `execute_job`.
* `workflow_dispatch`: Runs `collaborators`.
* `push`: Runs collaborators`.
* `schedule`: Runs collaborators`.

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

## Running the Tests

To run the tests, the `GITHUB_TOKEN` environment variable must be set. This
should be a classic token with all repo permissions and the delete repo
permission. The delete repo permission is used to create forks to test forked
branches. The commaned `tox -e test` can be used to run all the tests, which are
primarily integration tests.

GitHub actions should be configured to have access to a similar token that is
short lived, e.g., 7 days. If it expires, a new token needs to be set.

On GitHub actions, an expanded set of tests is run as the `GITHUB_TOKEN` for a
bot is available which can be used to test things like comments from a user that
does not have write permission or above.
