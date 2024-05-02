<!-- markdownlint-disable -->

<a href="../repo_policy_compliance/database.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `database.py`
Provides persistence for runner tokens. 

**Global Variables**
---------------
- **db_connect_str**

---

<a href="../repo_policy_compliance/database.py#L45"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `add_token`

```python
add_token(token: str) → None
```

Add a new token. 



**Args:**
 
 - <b>`token`</b>:  The token to add. 


---

<a href="../repo_policy_compliance/database.py#L57"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_token`

```python
check_token(token: str) → bool
```

Check whether a token is valid. 



**Args:**
 
 - <b>`token`</b>:  The token to check. 



**Returns:**
 Whether the token is valid. 


---

## <kbd>class</kbd> `Base`
Base class for ORM models. 





---

## <kbd>class</kbd> `OneTimeToken`
Stores one time tokens. 



**Attributes:**
 
 - <b>`value`</b>:  The token. 





