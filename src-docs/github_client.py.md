<!-- markdownlint-disable -->

<a href="../repo_policy_compliance/github_client.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `github_client.py`
Module for GitHub client. 

**Global Variables**
---------------
- **GITHUB_TOKEN_ENV_NAME**
- **GITHUB_APP_ID_ENV_NAME**
- **GITHUB_APP_INSTALLATION_ID_ENV_NAME**
- **GITHUB_APP_PRIVATE_KEY_ENV_NAME**
- **MISSING_GITHUB_CONFIG_ERR_MSG**
- **NOT_ALL_GITHUB_APP_CONFIG_ERR_MSG**
- **PROVIDED_GITHUB_TOKEN_AND_APP_CONFIG_ERR_MSG**

---

<a href="../repo_policy_compliance/github_client.py#L63"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get`

```python
get() → Github
```

Get a GitHub client. 



**Returns:**
  A GitHub client that is configured with a token or GitHub app from the environment. 



**Raises:**
 
 - <b>`ConfigurationError`</b>:  If the GitHub auth config is not valid. 


---

<a href="../repo_policy_compliance/github_client.py#L202"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `inject`

```python
inject(func: Callable[Concatenate[Github, ~P], ~R]) → Callable[~P, ~R]
```

Injects a GitHub client as the first argument to a function. 



**Args:**
 
 - <b>`func`</b>:  The function that requires a GitHub client. 



**Returns:**
 The function where the GitHub client has been injected as the first argument. 


---

<a href="../repo_policy_compliance/github_client.py#L255"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_collaborators`

```python
get_collaborators(
    affiliation: Literal['outside', 'all'],
    permission: Literal['triage', 'maintain', 'admin', 'pull', 'push'],
    repository: Repository
) → list[dict]
```

Get collaborators with a given affiliation and permission. 



**Args:**
 
 - <b>`affiliation`</b>:  The relationship the collaborator has with the repository. 
 - <b>`permission`</b>:  The permission the collaborator has on the repository. 
 - <b>`repository`</b>:  The repository to get collaborators for. 



**Returns:**
 The logins of collaborators that match the criteria. 


---

<a href="../repo_policy_compliance/github_client.py#L290"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_branch`

```python
get_branch(
    github_client: Github,
    repository_name: str,
    branch_name: str
) → Branch
```

Get the branch for the check. 



**Args:**
 
 - <b>`github_client`</b>:  The client to be used for GitHub API interactions. 
 - <b>`repository_name`</b>:  The name of the repository to run the check on. 
 - <b>`branch_name`</b>:  The name of the branch to check. 



**Returns:**
 The requested branch. 


---

<a href="../repo_policy_compliance/github_client.py#L305"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_collaborator_permission`

```python
get_collaborator_permission(
    repository: Repository,
    username: str
) → Literal['admin', 'write', 'read', 'none']
```

Get user permission for a given repository. 



**Args:**
 
 - <b>`repository`</b>:  The repository to get collaborators for. 
 - <b>`username`</b>:  The github login to check for permission. 



**Raises:**
 
 - <b>`GithubClientError`</b>:  if an invalid user permission is returned from the API call. 



**Returns:**
 The collaborator permission. 


