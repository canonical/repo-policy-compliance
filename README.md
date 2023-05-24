# repo-policy-compliance
Tool to check a GitHub repository for compliance with policy

The module exposes several functions to check for compliance with the following
policies:

* `target_branch_protection`: That the branch targeted by a pull request has
  protection enabled, requires reviews by the code owner, stale reviews are
  dismissed, that rules cannot be bypassed and that signed commits are
  required.
* `source_branch_protection`: That the branch containing the commits to be
  merged has protections enabled and requires signed commits. Additionally, all
  commits on the branch and not on the target branch must be signed. Not
  applicable to forked source branches.
* `collaborators`: Check that all outside collaborators of the project have at
  most `read` permissions.
* `execute_job`: That a maintainer or above has left the comment
  `/canonical/self-hosted-runners/run-workflows <commit SHA>` approving a
  workflow run for a specific commit SHA. Only applicable to forked source
  branches.
* `all_`: All of the above are checked.

These policies are designed for workflow runs in the context of a pull request.

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
is not a maintainer or above.
