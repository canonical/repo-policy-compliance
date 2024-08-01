# GitHub Authentication

This section describes the GitHub authentication options available for the charm.

You can either choose to use

- classic personal access tokens
- fine-grained personal access tokens
- a GitHub app

for authentication. The latter two options are recommended for better security and access control.
They require the fine-grained permissions as mentioned below.

**Note**:  If you are using a personal access tokens rather than a GitHub app,
the user who owns the token must have administrative access to the organisation or repository,
in addition to having a token with the necessary permissions.


## Classic personal access token scopes

If you want to use classic personal access tokens, you will need to select the `repo` 
scope when generating them.

## Fine grained permissions

For fine-grained access control, the following repository permissions are required:

- Administration: read
- Contents: read (if you want to check private repositories)
- Pull requests: read (if you want to check private repositories)