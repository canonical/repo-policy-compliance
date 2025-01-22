<!-- markdownlint-disable -->

<a href="../repo_policy_compliance/__init__.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `__init__.py`
Library for checking that GitHub repos comply with policy. 



---

## <kbd>class</kbd> `BranchInput`
Input arguments to check jobs running on a branch. 



**Attributes:**
 
 - <b>`repository_name`</b>:  The name of the repository to run the check on. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

## <kbd>class</kbd> `PullRequestInput`
Input arguments for pull request checks. 



**Attributes:**
 
 - <b>`repository_name`</b>:  The name of the repository to run the check on. 
 - <b>`source_repository_name`</b>:  The name of the repository that has the source branch. 
 - <b>`target_branch_name`</b>:  The name of the branch that is targeted by the PR. 
 - <b>`source_branch_name`</b>:  The name of the branch that contains the commits to be merged. 
 - <b>`commit_sha`</b>:  The SHA of the commit that the job is running on. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

## <kbd>class</kbd> `BranchInput`
Input arguments to check jobs running on a branch. 



**Attributes:**
 
 - <b>`repository_name`</b>:  The name of the repository to run the check on. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

## <kbd>class</kbd> `BranchInput`
Input arguments to check jobs running on a branch. 



**Attributes:**
 
 - <b>`repository_name`</b>:  The name of the repository to run the check on. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

## <kbd>class</kbd> `UsedPolicy`
Sentinel to indicate which policy to use. 



**Attributes:**
 
 - <b>`ALL`</b>:  Use all policies. 
 - <b>`PULL_REQUEST_ALLOW_FORK`</b>:  Use policy that lets forked repositories run jobs (default). 
 - <b>`PULL_REQUEST_DISALLOW_FORK`</b>:  Use policy that only blocks disallowed forks. 





---

## <kbd>class</kbd> `BranchInput`
Input arguments to check jobs running on a branch. 



**Attributes:**
 
 - <b>`repository_name`</b>:  The name of the repository to run the check on. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




