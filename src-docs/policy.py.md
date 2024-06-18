<!-- markdownlint-disable -->

<a href="../repo_policy_compliance/policy.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `policy.py`
Module for the policy document. 

**Global Variables**
---------------
- **ENABLED_KEY**
- **ENABLED_RULE**
- **DISABLED_RULE**
- **ALL**
- **ALLOW_FORK_RUN_WITH_COMMENT**

---

<a href="../repo_policy_compliance/policy.py#L100"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check`

```python
check(document: dict) → Report
```

Check that a policy document is valid. 



**Args:**
 
 - <b>`document`</b>:  The dictionary containing the policy to check. 



**Returns:**
 Whether the policy document is valid. 


---

<a href="../repo_policy_compliance/policy.py#L120"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `enabled`

```python
enabled(
    job_type: JobType,
    name: PullRequestProperty | BranchJobProperty,
    policy_document: mappingproxy
) → bool
```

Check whether a given policy is enabled. 



**Args:**
 
 - <b>`job_type`</b>:  The type of the job to check. 
 - <b>`name`</b>:  The property name of the policy. 
 - <b>`policy_document`</b>:  Describes the policies that should be run. 



**Returns:**
 Whether the policy is enabled in the document. 


---

## <kbd>class</kbd> `BranchJobProperty`
The names of the properties for jobs running on a branch portion of the policy document. 



**Attributes:**
 
 - <b>`COLLABORATORS`</b>:  Participants on a repository. 





---

## <kbd>class</kbd> `JobType`
The names of the properties for the policy document. 



**Attributes:**
 
 - <b>`PULL_REQUEST`</b>:  Policies for pull requests. 
 - <b>`WORKFLOW_DISPATCH`</b>:  Policies for workflow dispatch jobs. 
 - <b>`PUSH`</b>:  Policies for push jobs. 
 - <b>`SCHEDULE`</b>:  Policies for scheduled jobs. 





---

## <kbd>class</kbd> `PullRequestProperty`
The names of the properties for the pull request portion of the policy document. 



**Attributes:**
 
 - <b>`TARGET_BRANCH_PROTECTION`</b>:  Branch protection for the target branch. 
 - <b>`COLLABORATORS`</b>:  Participants on a repository. 
 - <b>`DISALLOW_FORK`</b>:  Whether a forked repository should not be allowed to run jobs. 
 - <b>`EXECUTE_JOB`</b>:  Whether a job should be executed. 





---

## <kbd>class</kbd> `BranchJobProperty`
The names of the properties for jobs running on a branch portion of the policy document. 



**Attributes:**
 
 - <b>`COLLABORATORS`</b>:  Participants on a repository. 





---

## <kbd>class</kbd> `Report`
Reports the result of checking whether a policy document is valid. 



**Attributes:**
 
 - <b>`result`</b>:  The check result. 
 - <b>`reason`</b>:  If the check failed, the reason why it failed. 





---

## <kbd>class</kbd> `BranchJobProperty`
The names of the properties for jobs running on a branch portion of the policy document. 



**Attributes:**
 
 - <b>`COLLABORATORS`</b>:  Participants on a repository. 





---

## <kbd>class</kbd> `BranchJobProperty`
The names of the properties for jobs running on a branch portion of the policy document. 



**Attributes:**
 
 - <b>`COLLABORATORS`</b>:  Participants on a repository. 





