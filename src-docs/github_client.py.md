<!-- markdownlint-disable -->

<a href="../repo_policy_compliance/github_client.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `github_client.py`
Module for GitHub client. 

**Global Variables**
---------------
- **GITHUB_TOKEN_ENV_NAME**

---

<a href="../repo_policy_compliance/github_client.py#L25"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get`

```python
get() → Github
```

Get a GitHub client. 



**Returns:**
  A GitHub client that is configured with a token from the environment. 



**Raises:**
 
 - <b>`ConfigurationError`</b>:  If the GitHub token environment variable is not provided or empty. 


---

<a href="../repo_policy_compliance/github_client.py#L43"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../repo_policy_compliance/github_client.py#L89"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_collaborators`

```python
get_collaborators(
    affiliation: Literal['outside', 'all'],
    permission: Literal['triage', 'maintain', 'admin', 'pull'],
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

<a href="../repo_policy_compliance/github_client.py#L119"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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


