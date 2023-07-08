from configparser import ConfigParser
from jira import JIRA
from datetime import datetime
import time

jira_project = 'TSP'


def search_tickets(jira):
    query = f"project={jira_project}"

    # Using algorithm in
    # https://community.atlassian.com/t5/Jira-Core-Server-questions/List-all-the-issues-of-a-project-with-JIRA-Python/qaq-p/350521
    # to loop through all tickets
    block_size = 50
    block_num = 0
    while True:
        start_idx = block_num * block_size
        j_issues = jira.search_issues(query, start_idx, block_size)
        if len(j_issues) == 0:
            # Retrieve issues until there are no more to come
            break
        block_num += 1
        for j_issue in j_issues:
            print(j_issue.fields.summary)
            j_uptime = datetime.strptime(j_issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z")
            ts_jira = j_uptime.timestamp()
            ts_now = time.time()
            print(f"Time since update:{ts_jira-ts_now}")


def create_jira():
    from pathlib import Path
    jira_oauth_private_key_file = Path.home()/".oauthconfig/oauth.pem"
    config_file = Path.home()/".oauthconfig/.redmine_jira.config"

    config = ConfigParser()
    config.read(config_file)

    jira_url = config.get("jira", "base_url")
    oauth_token = config.get("jira", "oauth_token")
    oauth_token_secret = config.get("jira", "oauth_token_secret")
    consumer_key = config.get("jira", "consumer_key")

    rsa_private_key = None
    # Load RSA Private Key file.
    with open(jira_oauth_private_key_file, 'r') as key_cert_file:
        rsa_private_key = key_cert_file.read()

    if jira_url[-1] == '/':
        jira_url = jira_url[0:-1]

    oauth_dict = {
        'access_token': oauth_token,
        'access_token_secret': oauth_token_secret,
        'consumer_key': consumer_key,
        'key_cert': rsa_private_key
    }

    return JIRA(oauth=oauth_dict, server=jira_url)


if __name__ == "__main__":

    jira = create_jira()
    search_tickets(jira)
