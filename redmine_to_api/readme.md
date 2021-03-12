# test_api.py

Test script to transfer Redmine tickets to JIR tickets using API.

Authentification with token is used for Redmine, and user/password is used for JIRA (So far, I cannot find a good way to access using token.)

Modify the following parts with your information

```test_api.py
# setting of 1D-DRP Redmine at LAM
# --------------------------------
# API token    
redmine_apikey = 'yor_redmine_api_token'
```

```test_api.py
# setting of PFS JIRA
# -------------------
# API token
jira_apikey = 'your_jira_token'
# account info of admin
jira_user = 'your_name'
jira_pass = 'your_password'
```

## To be considered

* How to link user b/w Redmine and JIRA
* Sort out terminology and equivalent field values
  * priority, status, task name etc..
* How to add attachment
