from configparser import ConfigParser
import re
from pathlib import Path
import logging
import redminelib
from redminelib import Redmine
import jira
from jira import JIRA
import sys
from argparse import ArgumentParser

# folder to save attachments temporarily
dir_att = Path.home()/'temp/redmine_jira/attachments'
dir_att.mkdir(parents=True, exist_ok=True)

jira_user = 'r2j.migrate'
jira_project = 'TSP'
redmine_project = 'pylibamazed'

# Maps redmine statuses to Jira ones
status_map = {'Merged': 'Done',
              'Feedback': 'In Progress',
              'In Progress': 'In Progress',
              'New': 'Open',
              'Closed': 'Done',
              'Rejected': "Won't Fix",
              'Resolved': 'Done'}


def create_redmine(url, key):
    """Creates a Redmine instance based on user/pass info
    """
    if url[-1] == '/':
        url = url[0:-1]

    redmine = Redmine(url=url, key=key)
    return redmine


def create_jira(jira_url, oauth_token, oauth_token_secret,
                consumer_key, jira_oauth_private_key_file):
    """Creates a Jira instance based on oauth information
    """
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

    jira_iss = JIRA(oauth=oauth_dict, server=jira_url)
    return jira_iss


def create_redmine_jira(config_file, jira_oauth_private_key_file):

    config = ConfigParser()
    config.read(config_file)

    rm_iss_url = config.get("redmine", "issue_url")
    rm_key = config.get("redmine", "key")
    redmine_iss = create_redmine(rm_iss_url, key=rm_key)

    jira_url = config.get("jira", "base_url")
    oauth_token = config.get("jira", "oauth_token")
    oauth_token_secret = config.get("jira", "oauth_token_secret")
    consumer_key = config.get("jira", "consumer_key")
    jira_iss = create_jira(jira_url, oauth_token, oauth_token_secret,
                           consumer_key, jira_oauth_private_key_file)

    return redmine_iss, jira_iss


def find_migrated_tickets(jira_iss):
    """Get a list of all tickets that have
    already been migrated to Jira from
    redmine.
    """
    redmine_jira_map = dict()
    query = f"project={jira_project}"

    # Using algorithm in
    # https://community.atlassian.com/t5/Jira-Core-Server-questions/List-all-the-issues-of-a-project-with-JIRA-Python/qaq-p/350521
    # to loop through all tickets
    block_size = 50
    block_num = 0
    while True:
        start_idx = block_num * block_size
        j_issues = jira_iss.search_issues(query, start_idx, block_size)
        if len(j_issues) == 0:
            # Retrieve issues until there are no more to come
            break
        block_num += 1
        for j_issue in j_issues:
            j_summary = j_issue.fields.summary
            m = re.search(r"\[RM\-([0-9]+)\].*", j_summary)
            if m:
                r_issue_id = int(m.group(1))
                if r_issue_id in redmine_jira_map:
                    raise ValueError('Duplicate issues with redmine ID '
                                     f'{r_issue_id} exist.')
                else:
                    redmine_jira_map[r_issue_id] = j_issue.key
            else:
                continue
    return redmine_jira_map


def print_jira_fields(j_issue):
    logger = logging.getLogger(__name__)
    for field_name in j_issue.raw['fields']:
        logger.info("Field:", field_name, "Value:",
                    j_issue.raw['fields'][field_name])


def migrate_ticket(r_issue,
                   migrated_tickets,
                   redmine,
                   jira_iss,
                   update):
    """Migrates a single redmine issue.

       If the issue already exists in JIRA,
       update it.

    """

    logger = logging.getLogger(__name__)

    issue_dict = {
        'project': {'key': jira_project},
        'summary': f'[RM-{r_issue.id}] {r_issue.subject}',
        'description': (f'_{{color:#505f79}}'
                        f' Created on {r_issue.created_on}'
                        f' by {r_issue.author}.'
                        f' % Done: {r_issue.done_ratio}'
                        f'{{color}}_\n\n\n'
                        f'{r_issue.description}'),
        'issuetype': {'name': 'Task'},
    }

    j_issue = None
    if update:
        migrated_j_issue_key = migrated_tickets[r_issue.id]
        j_issue = jira_iss.issue(migrated_j_issue_key)
        # To update attachment and comments,
        # simplest way is to delete existing ones
        # and re-add those from redmine
        for a in j_issue.fields.attachment:
            jira_iss.delete_attachment(a.id)
        for c in j_issue.fields.comment.comments:
            c.delete()
        j_issue.update(fields=issue_dict)
    else:
        j_issue = jira_iss.create_issue(fields=issue_dict)
        logger.debug(f'Created new issue {j_issue.key}')
        migrated_tickets[r_issue.id] = j_issue.key

    # Try to assign version
    logger.info(f'Looking at version for redmine issue {r_issue.id}')
    try:
        r_version = r_issue.fixed_version
        j_version = None
        for version in jira_iss.project_versions(jira_project):
            logger.debug(f'looking at version name {version.name}')
            if r_version.name == version.name:
                j_version = version
                break
        else:
            j_version = jira_iss.create_version(r_version.name,
                                                jira_project,
                                                r_version.name)
        issue_dict = {'fixVersions':
                      [{'add': [{j_version.name: j_version.name}]}]}
        logger.info(f'Redmine issue {r_issue.id}:'
                    f' Adding version {j_version.name} to migrated ticket.')
        j_issue.update(fields=issue_dict)
        logger.info(j_issue.fields.fixVersions)
    except redminelib.exceptions.ResourceAttrError as e:
        logger.info(f'Redmine issue {r_issue.id}: no fixed version ({e})')

    # No assignee information can be pulled out from redmine.
    # In meantime, use special migrator user as assignee.
    jira_iss.assign_issue(j_issue, jira_user)

    # Populate comments, attachments and status
    if r_issue.journals is not None:
        add_comments(r_issue, jira_iss, j_issue)
    if r_issue.attachments is not None:
        add_attachments(r_issue, redmine, jira_iss, j_issue)
    jira_iss.transition_issue(j_issue.key, status_map[r_issue.status.name])

    operation = 'Updated' if update else 'Migrated'
    logger.debug(f'{operation} ticket {r_issue.id} '
                 f'to JIRA {j_issue.key} successfully.')

    return j_issue


def add_comments(r_content, jira_iss, j_issue):
    """Add all comments to Jira issue
    """
    logger = logging.getLogger(__name__)
    for j in r_content.journals:
        try:
            if j.notes != '':
                comment = (f'Comment by {j.user.name} '
                           f'on {j.created_on}:\n'
                           f'{j.notes}')
                jira_iss.add_comment(j_issue.key, comment)
        except redminelib.exceptions.ResourceAttrError as e:
            logger.debug(f'Problems adding comment. Exception is {e}')


def add_attachments(r_issue, redmine, jira_iss, j_issue):
    """Add all attachments in Jira issue
    """
    logger = logging.getLogger(__name__)
    for a in r_issue.attachments:
        try:
            attachment = redmine.attachment.get(a.id)
            attachment.download(savepath=dir_att, filename=a.filename)
            jira_iss.add_attachment(j_issue.key, f'{dir_att}/{a.filename}')
        except redminelib.exceptions.ResourceAttrError as e:
            logger.debug(f'Problems adding attachment. Exception is {e}')


def migrate_tickets(redmine_iss, jira_iss):

    logger = logging.getLogger(__name__)
    logger.info('Migrating tickets...')
    migrated_tickets = find_migrated_tickets(jira_iss)
    logger.debug(f'already migrated redmine tickets: {migrated_tickets}')

    # Migrate open redmine tickets
    # and those which are closed, but have been previously migrated.
    count_total = 0
    count_open_migrated = 0
    count_open_updated = 0
    count_misc_skipped = 0

    with redmine_iss.session():
        for r_issue in redmine_iss.issue.all():
            count_total += 1
            logger.info(f'Processing redmine ticket [{r_issue.id}] '
                        f'and status [{r_issue.status.name}] ..')
            update = r_issue.id in migrated_tickets
            if r_issue.status.name in status_map:
                # try:
                #     j_issue = migrate_ticket(r_issue, migrated_tickets,
                #                              redmine_iss, jira_iss, update)
                # except (AttributeError,
                #         redminelib.exceptions.ResourceAttrError,
                #         jira.exceptions.JIRAError) as e:
                #     logger.warning('Could not process redmine issue '
                #                    f'{r_issue.id} due to {e}. Skipping.')
                #     count_misc_skipped += 1
                #     continue

                if update:
                    logger.info('Updated Jira ticket '
                                f'{migrated_tickets[r_issue.id]} '
                                f'for open redmine ticket {r_issue.id}')
                    count_open_updated += 1
                else:
                    logger.info('Created new Jira ticket '
                                # f'{j_issue.key} '
                                f'for open redmine ticket {r_issue.id}')
                    count_open_migrated += 1
            else:
                logger.warning(f'Redmine issue {r_issue.id} and '
                               f'Status {r_issue.status.name}:'
                               'Cannot process. Skipping.')
                count_misc_skipped += 1

    logger.info(f'SUMMARY:\n'
                f'Processed {count_total:6} Redmine tickets. Of which:\n'
                f'--> {count_open_migrated:6} were newly migrated tickets\n'
                f'--> {count_open_updated:6} were updated tickets\n'
                f'--> {count_misc_skipped:6} '
                'could not be processed and skipped.')


def main(args):
    # https://dev.to/micahcarrick/python-argument-parsing-with-log-level-and-config-file-1d6p
    argparse = ArgumentParser(prog=__file__, add_help=False)
    argparse.add_argument('-l', '--log', default='INFO',
                          help='set logger level')
    argparse.add_argument("-n", '--debug', action="store_true",
                          help="Debug mode")
    args, _ = argparse.parse_known_args(args)

    try:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            level=args.log)
    except ValueError:
        logging.error("Invalid log level: {}".format(args.log))
        sys.exit(1)

    logger = logging.getLogger(__name__)
    logger.info("Log level set to "
                f"{logging.getLevelName(logger.getEffectiveLevel())}")

    auth_config_file = Path.home()/".oauthconfig/.redmine_jira.config"
    pem_file = Path.home()/".oauthconfig/oauth.pem"

    redmine_iss, jira_iss = create_redmine_jira(auth_config_file,
                                                pem_file)

    migrate_tickets(redmine_iss, jira_iss)


if __name__ == "__main__":
    main(sys.argv[1:])
