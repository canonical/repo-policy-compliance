# GitHub Token Permissions

You can either choose to use a personal access token (PAT) or a fine-grained access token for the 
`github_token` configuration. The token permissions/scopes are different for each type of token.


## Fine grained access token permissions

**Note**: In addition to having a token with the necessary permissions, the user who owns the
token also must have admin access to the organisation or repository.

For fine-grained access control, the following repository scopes are required:

- Administration: read
- Contents: read (if you want to check private repositories)
- Pull requests: read (if you want to check private repositories)

## Personal access token scopes

If you want to use classic PATS, you will need to select the `repo` scope.