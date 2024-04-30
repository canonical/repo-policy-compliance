<!-- markdownlint-disable -->

<a href="../repo_policy_compliance/log.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `log.py`
Module for logging. 


---

<a href="../repo_policy_compliance/log.py#L14"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `call`

```python
call(func: Callable[~P, ~R]) → Callable[~P, ~R]
```

Log before func and result of func. 



**Args:**
 
 - <b>`func`</b>:  The function that executes a func. 



**Returns:**
 The function where the func is logged before it starts and the results are logged. 


---

<a href="../repo_policy_compliance/log.py#L43"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `is_setup`

```python
is_setup() → bool
```

Check if logging has already been setup. 



**Returns:**
  True if logging has already been setup, False otherwise. 


---

<a href="../repo_policy_compliance/log.py#L55"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `setup`

```python
setup(handlers: Optional[list[Handler]] = None) → None
```

Initialise logging for check execution. 



**Args:**
 
 - <b>`handlers`</b>:  The handlers to use for logging. If not provided, a StreamHandler is used. 


