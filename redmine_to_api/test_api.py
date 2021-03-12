#!/usr/bin/env python

import sys

import redminelib
from redminelib import Redmine

import urllib.request
import json

from datetime import datetime as dt

# setting of 1D-DRP Redmine at LAM
# --------------------------------
# # API token
redmine_apikey = 'yor_redmine_api_token'
# project of the DRP library
url_lam_lib = 'https://projets.lam.fr/projects/cpf'
# project of DRP client
url_lam_cli = 'https://projets.lam.fr/projects/pfs-dev'
# issues
url_lam_iss = 'https://projets.lam.fr/'

# setting of PFS JIRA
# -------------------
# API token
jira_apikey = 'your_jira_token'
# account info of admin
jira_user = 'your_name'
jira_pass = 'your_password'
# metadata
url_jira = 'https://pfspipe.ipmu.jp/jira/rest/api/2/issue/'

# folder to save attachments
dir_att = './attachments'


def read_redmine(write='print'):
    """
    Get Redmine issues using API
    Documents of python-redmine module: https://python-redmine.com/index.html

    Parameters
    write: (optional) "print" or convert to JIRA "json"
    ----------
    """

    redmine_lib = Redmine(url_lam_lib, key=redmine_apikey)
    redmine_cli = Redmine(url_lam_cli, key=redmine_apikey)
    redmine_iss = Redmine(url_lam_iss, key=redmine_apikey)

    issues_lib = redmine_lib.issue.all()
    issues_cli = redmine_cli.issue.all()

    # print(vars(issues))
    for issue in issues_cli:

        # test_id = 6147
        content = redmine_iss.issue.get(issue.id,
                                        include=['children', 'attachments',
                                                 'relations', 'journals',
                                                 'watchers'])
        if write == 'print':
            redmine_write_text(content, redmine_iss)
        elif write == 'json':
            redmine_to_jira(content, redmine_iss)
        else:
            print('chose either "print" or "json"')


def redmine_write_text(content, redmine):
    """
    Write down every issue and its comments.
    Here, only comments are written, ignoring property change.
    Attachments is also downloaded

    Parameters
    ----------
    content: redminelib.ResourceSet object
    redmine: redminelib.Redmine object
    """

    ofile = open('parameters_redmine.txt', 'a')

    # print(vars(testissue))
    print(f'\nIssue ID: {content.id}', file=ofile)
    print(f'Subject: {content.subject}', file=ofile)
    print(f'Description: {content.description}', file=ofile)
    print(f'Created on: {content.created_on}', file=ofile)
    print(f'Updated on: {content.updated_on}', file=ofile)
    print(f'Status: {content.status.name}', file=ofile)
    print(f'Priority: {content.priority.name}', file=ofile)
    print(f'Author (Reporter): {content.author.name}', file=ofile)
    print(f'Assigned to (Assignee): {content.assigned_to.name}', file=ofile)
    if content.attachments is not None:
        for a in content.attachments:
            print(f'{a.id}', file=ofile)
            attachment = redmine.attachment.get(a.id)
            attachment.download(savepath=dir_att, filename=a.filename)
            print(f'Download attachment: {a.filename}', file=ofile)
            print(f'   Created on {a.created_on}', file=ofile)
            print(f'   Created by {a.author.name}', file=ofile)
    if content.journals is not None:
        print('Notes:', file=ofile)
        for j in content.journals:
            try:
                if j.notes != '':
                    print(f'Comment by:{j.user.name}', file=ofile)
                    print(f'Comment on: {j.created_on}', file=ofile)
                    print(f'Comment: {j.notes}\n', file=ofile)
            except redminelib.exceptions.ResourceAttrError:
                pass
    print('--*--*--*--*--', file=ofile)

    ofile.close()


def redmine_to_jira(content, redmine):

    """
    Make json from redmine contents to JIRA
    Here, only comments are written, ignoring property change.
    Attachments is also downloaded
    document: https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/

    Parameters
    ----------
    content: redminelib.ResourceSet object
    redmine: redminelib.Redmine object
    """

    # To create issue
    dict_fields = {'project': {'key': "PIPE1D"},
                   'summary': content.subject,
                   'reporter': content.author.name,  # This should be linked to JIRA user name
                   'description': content.description,
                   'created': content.created_on.isoformat(timespec='milliseconds'),  # time zone?
                   'updated': content.updated_on.isoformat(timespec='milliseconds'),  # time zone?
                   'priority': content.priority.id,  # should be changed to JIRA priority
                   'status': content.status.name,   # should be changed to JIRA status
                   'assignee': content.assigned_to.name}   # This should be linked to JIRA user name

    dict_add = {'fields': dict_fields}
    # where to put Redmine ID? content.id
    json_add = json.dumps(dict_add, indent=2)
    print(json_add)

    '''
    POST /rest/api/2/issue
    When creating the JIRA issue, the key of issue will be returned
    '''

    # To add attachment : To be checked
    '''
    POST /rest/api/2/issue/{issueIdOrKey}/attachments
    '''

    # To add comment
    if content.journals is not None:
        for j in content.journals:
            try:
                dict_comment = {'body': j.notes,
                                'author': j.user.name,  # This should be linked to JIRA user name
                                'created': j.created_on.isoformat(timespec='milliseconds')}  # time zone?

                json_comment = json.dumps(dict_comment, indent=2)
                print(json_comment)

                '''
                POST /rest/api/2/issue/{issueIdOrKey}/comment
                '''

            except redminelib.exceptions.ResourceAttrError:
                pass


def read_jira():

    ofile = open('parameters_jira.txt', 'w')

    # params = {jira_user: jira_apikey}
    params = {jira_user: jira_pass}
    issue = 'DAMD-1'
    url = f'{url_jira}{issue}?{urllib.parse.urlencode(params)}'
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            body = json.loads(response.read())
            headers = response.getheaders()
            status = response.getcode()

            print(headers, file=ofile)
            print(status, file=ofile)
            print(json.dumps(body, indent=2), file=ofile)

    except urllib.error.URLError as e:
        print(e.reason, file=sys.stderr)

    '''
    This works, but receive Unauthorized (401)

    curl -D- \
       -u pfs-jira:jira-token \
       -X GET \
       -H "Content-Type: application/json" \
       https://pfspipe.ipmu.jp/jira/rest/api/2/issue/DAMD-1

    If username and password are used, it works.
    '''

    ofile.close()


if __name__ == "__main__":

    # read_jira()
    # read_redmine(write='print')
    read_redmine(write='json')
