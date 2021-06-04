from configparser import ConfigParser
import re
import logging
from jira import JIRA

log = logging.getLogger("unmark-logger")
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.INFO)

jira_project = 'TSP'


def unmark_migrated_tickets(jira):
    """Unmarks tickets that are originally marked as
    migrated-from-redmine.

    This helps with testing with migration, as the migration code
    assumes that redmine tickets have yet to be migrated.

    Tickets that are migrated have the prefix '[RM:xxxxx]'
    in the summary field. Simply modify that prefix.
    """
    query = f"project='{jira_project}'"
    count = 0
    unmarked = 0
    # Using algorithm in
    # https://community.atlassian.com/t5/Jira-Core-Server-questions/List-all-the-issues-of-a-project-with-JIRA-Python/qaq-p/350521
    # to loop through all tickets
    block_size = 50
    block_num = 0
    while True:
        start_idx = block_num*block_size
        j_issues = jira.search_issues(query, start_idx, block_size)
        if len(j_issues) == 0:
            # Retrieve issues until there are no more to come
            break
        block_num += 1
        for j_issue in j_issues:
            print(j_issue.key)
            j_summary = j_issue.fields.summary
            m = re.search(r"\[RM\-([0-9]+)\].*", j_summary)
            if m:
                modified_summary = j_issue.fields.summary.replace(r'[RM-',
                                                                  r'[UM-')
                log.info(f'Unmarked ticket {j_issue.key}')
                j_issue.update(summary=modified_summary)
                unmarked += 1
            count += 1
    log.info(f"Unmarked {unmarked} tickets from a total of {count} in project")


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
    unmark_migrated_tickets(jira)
