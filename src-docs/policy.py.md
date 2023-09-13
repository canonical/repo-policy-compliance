<!-- markdownlint-disable -->

<a href="../repo_policy_compliance/policy.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `policy.py`
Module for the policy document. 

**Global Variables**
---------------
- **ENABLED_KEY**
- **ENABLED_RULE**
- **ALL**

---

<a href="../repo_policy_compliance/policy.py#L89"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../repo_policy_compliance/policy.py#L109"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

Attrs:  BRANCH_PROTECTION: Branch protection for the branch.  COLLABORATORS: Particupants on a repository. 





---

## <kbd>class</kbd> `JobType`
The names of the properties for the policy document. 

Attrs:  PULL_REQUEST: Policies for pull requests.  WORKFLOW_DISPATCH: Policies for workflow dispatch jobs.  PUSH: Policies for push jobs.  SCHEDULE: Policies for scheduled jobs. 





---

## <kbd>class</kbd> `PullRequestProperty`
The names of the properties for the pull request portion of the policy document. 

Attrs:  TARGET_BRANCH_PROTECTION: Branch protection for the target branch.  SOURCE_BRANCH_PROTECTION: Branch protection for the source branch.  COLLABORATORS: Particupants on a repository.  EXECUTE_JOB: Whether a job should be executed. 





---

## <kbd>class</kbd> `BranchJobProperty`
The names of the properties for jobs running on a branch portion of the policy document. 

Attrs:  BRANCH_PROTECTION: Branch protection for the branch.  COLLABORATORS: Particupants on a repository. 





---

## <kbd>class</kbd> `Report`
Reports the result of checking whether a policy document is valid. 

Attrs:  result: The check result.  reason: If the check failed, the reason why it failed. 





---

## <kbd>class</kbd> `BranchJobProperty`
The names of the properties for jobs running on a branch portion of the policy document. 

Attrs:  BRANCH_PROTECTION: Branch protection for the branch.  COLLABORATORS: Particupants on a repository. 





---

## <kbd>class</kbd> `BranchJobProperty`
The names of the properties for jobs running on a branch portion of the policy document. 

Attrs:  BRANCH_PROTECTION: Branch protection for the branch.  COLLABORATORS: Particupants on a repository. 





