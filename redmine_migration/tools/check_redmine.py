from configparser import ConfigParser
import redminelib
from redminelib import Redmine
import requests


def check(redmine_lib, redmine_iss):
    for issue in redmine_lib.issue.all():
        print(f'issue id: [{issue.id}]')
        print(f'issue status: [{issue.status}]')
        content = redmine_iss.issue.get(issue.id)
        if content.journals is not None:
            for record in content.journals:
                print(f'id={record.id}')
                print(f'created_on={record.created_on}')
                try:
                    print('Getting notes...')
                    print(f'notes=[{record.notes}]')
                except redminelib.exceptions.ResourceAttrError as e:
                    print(e)
    if content.attachments is not None:
        for a in content.attachments:
            print(f'{a.id}')
            print(f'   Created on {a.created_on}')
            print(f'   Created by {a.author.name}')


def check_status(redmine_lib, redmine_iss):
    # issue = redmine_lib.issue.all()[1]
    # content = redmine_iss.issue.get(issue.id)
    # print(content.status.name)
    statuses = set()
    try:
        for issue in redmine_lib.issue.all():
            try:
                content = redmine_iss.issue.get(issue.id)
                # print(f'{dir(issue)}')
                print(f'issue id: [{issue.id}]')
                print(f'issue status: [{content.status}]')
                print(f'% done: {issue.done_ratio}')
                print(f'Author: {issue.author}')
                print(f'Created on: {issue.created_on}')
                statuses.add(content.status.name)
            except redminelib.exceptions.ResourceAttrError as e:
                print(f'Exception: {e}')
    except requests.exceptions.ConnectionError as f:
        print(f)

    print(f'statuses = {statuses}')


def create_redmine():
    from pathlib import Path
    config_file = Path.home()/".oauthconfig/.redmine_jira.config"
    config = ConfigParser()
    config.read(config_file)
    key = config.get("redmine", "key")

    redmine_lib = Redmine('https://projets.lam.fr/projects/cpf', key=key)
    redmine_iss = Redmine('https://projets.lam.fr/', key=key)
    return redmine_lib, redmine_iss


if __name__ == "__main__":

    redmine_lib, redmine_iss = create_redmine()

    # check(redmine_lib, redmine_iss)
    check_status(redmine_lib, redmine_iss)
