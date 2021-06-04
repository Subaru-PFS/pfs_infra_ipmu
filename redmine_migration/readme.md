# Redmine to Jira Migration software

## Introduction

This code is used to migrate the 1D DRP tickets maintained on the LAM
Redmine ticketing system to the PFS Jira tracking system.

## Pre-requisites

It is assumed that python 3.6 or better is installed.

The code requires both the [python-redmine](https://python-redmine.com/index.html)
and [python-jira](https://jira.readthedocs.io/en/master/) libraries installed.

You will also need accounts on Redmine and on Jira.

## Setup

### Authentication

For access to Redmine, you need to generate an access key.
This is available on your account page ( /my/account )
when logged in, on the right-hand pane of the default layout.

For access to Jira, you need to arrange for OAuth1 Authentication.

We recommend [this tool](https://github.com/rkadam/jira-oauth-generator) for generating
the Oauth authentication tokens. Follow the instructions in the README there.

Note that in those instructions, it suggests
a fix to `rsakey.py` file using `hashBytes = SHA1(bytearray(bytes, "utf8"))`.
This did not work for one of us (Hassan), but the following was successful:
```hashBytes = secureHash(bytearray(bytes, 'utf8'), hAlg)```

With the instructions above you should have generated a RSA private key (oauth.pem),
an 'oauth token', and an 'oauth secret token'.

Create the following file `${HOME}/.oauthconfig/.redmine_jira.config`
with the following contents:

```
[redmine]
	lib_url=https://projets.lam.fr/projects/cpf
	issue_url=https://projets.lam.fr/
	key=xxxxxxxxx
[jira]
	base_url=https://pfspipe.ipmu.jp/jira
	oauth_token=xxxxxxxxxxxxx
	oauth_token_secret=xxxxxxxxxxxxxx
	consumer_key=jira-oauth1-rest-api-access2
```

Replacing the 'xxxxxxxxxxxx's with the redmine key,
and the Jira oauth tokens you created above, respectfully.

Copy your oauth.pem file to the directory `{HOME}/.oauthconfig/.`

## Testing

Run the `check_jira.py` and `check_redmine.py` scripts in the `tools` folder:

```
cd tools
python check_jira.py
python check_redmine.py
```

and check for any errors.

## Running the migration

Run the migration as follows:

```python migration.py```

Check for errors etc. If all goes well, the final log output is the summary, an example of which
is below:

```
2021-06-03 19:31:31,824 INFO: SUMMARY:
85 were migrated from redmine, of which:
-->      0 were newly migrated tickets
-->     85 were updated tickets, of which:
------>      0 have been recently closed on redmine
```

## Additional tools

In the tools folder there's an additional script `unmark_migrated_tickets.py` which can be used to 'unmark' previously migrated tickets, forcing the subsequent migration to assume that there are no already-migrated
tickets. This is useful for testing, although other approaches (eg deleting migrated tickets via
the Jira interface) may be an alternative (albeit less safe).
