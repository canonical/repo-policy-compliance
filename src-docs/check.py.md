<!-- markdownlint-disable -->

<a href="../repo_policy_compliance/check.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `check.py`
Individual checks used to compose job checks. 

**Global Variables**
---------------
- **BYPASS_ALLOWANCES_KEY**
- **FAILURE_MESSAGE**
- **AUTHORIZATION_STRING_PREFIX**
- **EXECUTE_JOB_MESSAGE**

---

<a href="../repo_policy_compliance/check.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `github_exceptions_to_fail_report`

```python
github_exceptions_to_fail_report(
    func: Callable[~P, ~R]
) → Callable[~P, Union[~R, Report]]
```

Catch exceptions and convert to failed report with reason. 



**Args:**
 
 - <b>`func`</b>:  The function to catch the GithubClient exceptions for. 



**Returns:**
 The function where any exceptions raised would be converted to a failed result. 


---

## <kbd>class</kbd> `JobMetadata`
Information about the target job run to check for authorization. 



**Attributes:**
 
 - <b>`branch_name`</b>:  The branch name of the target repository. 
 - <b>`commit_sha`</b>:  The commit SHA of the job run. 
 - <b>`repository_name`</b>:  The repository running the check. 
 - <b>`fork_or_branch_repository_name`</b>:  The repository of the branch/fork. 





---

## <kbd>class</kbd> `Report`
Reports the result of a check. 



**Attributes:**
 
 - <b>`result`</b>:  The check result. 
 - <b>`reason`</b>:  If the check failed, the reason why it failed. 





---

## <kbd>class</kbd> `Result`
The result of a check. 



**Attributes:**
 
 - <b>`PASS`</b>:  The check passed. 
 - <b>`FAIL`</b>:  The check failed. 
 - <b>`ERROR`</b>:  There was an error while performing the check. 





