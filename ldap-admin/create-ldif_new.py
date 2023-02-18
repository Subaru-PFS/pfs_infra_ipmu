#!/usr/bin/env python
import os
import subprocess

import random
import string

import base64

# For option
from argparse import ArgumentParser

import time

import logging

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.INFO)


# Ldif output control options
opt_ldaphost = 'ldap.pfs.ipmu.jp'
opt_ldapadm = 'cn=admin,dc=pfs,dc=ipmu,dc=jp'
opt_gid = '2000'
opt_invalid = '{SSHA}XXXX'
uid_undefined = 65542

ldif_dc_web = 'dc=web,dc=pfs,dc=ipmu,dc=jp'
ldif_dc_shell = 'dc=shell,dc=pfs,dc=ipmu,dc=jp'

# default commands
cmd_add = 'ldapadd    -H ldap://{0} -D {1} -W -x -f '.format(opt_ldaphost, opt_ldapadm)
cmd_mod = 'ldapmodify -H ldap://{0} -D {1} -W -x -f '.format(opt_ldaphost, opt_ldapadm)

cmd_latex = '/usr/bin/pdflatex'
cmd_sendmail = '/usr/bin/sendmail'

# script and files
fname_uid = '00uid.list'
fname_tex = 'skel.tex'
fname_email = 'skel.email'
fname_admin = 'skel.admin.email'


def get_option():

    head_str = 'Availabele options are:'
    tail_str = 'target_list is a filename with lines by "<email> <username> <fullname>"'\
               'uid is taken from "00uid.list" file (last +1)'\
               'default gid is from opt_gid (2000)'\
               'fullname is an option, from third to the end when defined.'

    argparser = ArgumentParser(fromfile_prefix_chars='@', description=head_str,
                               epilog=tail_str)
    argparser.add_argument('fname_addr', help='target list')
    argparser.add_argument('-r', '--reset', action='store_true',
                           help='reset password of the account.')
    argparser.add_argument('-d', '--disable', action='store_true',
                           help='disable the account: remove from default group and set password/email invalid')
    # argparser.add_argument('-e', '--delete', action='store_true',
    #                        help='delete from LDAP group')
    argparser.add_argument('-g', '--group', nargs='*', type=str,
                           action='append',
                           help='list of extra LDAP groups')
    argparser.add_argument('-j', '--jira', action='store_true',
                           help='enable JIRA access')
    argparser.add_argument('-s', '--shell', action='store_true',
                           help='define user as shell group to access IPMU servers (cannot be used with --reset)')
    return argparser.parse_args()


def read_uid(fname_uid, uid):

    with open(fname_uid, 'r') as fh:
        all_lines = fh.readlines()

    last = 0
    for al in all_lines:
        arr = al.split()
        uid[arr[1]] = arr[0]
        if int(arr[0]) > last:
            last = int(arr[0])

    return last, uid


def save_uid(fname_uid, uid):

    fout = open(fname_uid, 'w')

    for k, v in uid.items():
        print(k, v, sep=' ', file=fout)

    fout.close()


def make_pass():

    select = string.ascii_letters + string.digits + './!"#%&()[]{}$-=,*+'

    randlst = [random.choice(select) for i in range(10)]

    return ''.join(randlst)


def mod_tex_skel(skel, texname, uname, email, passwd):

    with open(skel, 'r') as fh:
        string = fh.read()

    string = string.replace('@@EMAIL@@', email)
    string = string.replace('@@USER@@', uname)
    string = string.replace('@@PASS@@', passwd)

    fout = open(texname, 'w')
    print(string, file=fout)
    fout.close()


def mod_email_skel(skel, pdfname, uname, email):

    mime_boundary = str(time.time())

    with open(skel, 'r') as fh:
        string = fh.read()

    string = string.replace('@@EMAIL@@', email)
    string = string.replace('@@USER@@', uname)
    string = string.replace('@@BOUNDARY@@', mime_boundary)

    # attach attachment
    with open(pdfname, 'rb') as fh:
        while True:
            att = fh.read(57)
            if att:
                string = string + str(base64.encodestring(att)) + '\n'
            else:
                break
    string = string + '\n' + mime_boundary + '--'

    # omit \r \n at the begining of the string
    while (string[0] == '\r' or string[0] == '\n'):
        string = string[1]

    return string


def mod_email_admin_skel(skel, uname, email):

    with open(skel, 'r') as fh:
        string = fh.read()

    string = string.replace('@@EMAIL@@', email)
    string = string.replace('@@USER@@', uname)

    # omit \r \n at the begining of the string
    while (string[0] == '\r' or string[0] == '\n'):
        string = string[1]

    return string


def out_ldif_new(supname, uname, ldifname, addr, passwd, ldif_dc,
                 uid=None, fullname=None):

    if uid is None: uid = uid_undefined
    if fullname is None: fullname = uname

    fout = open(ldifname, 'w')
    print('dn: cn={0},ou=Users,{1}'.format(uname, ldif_dc), file=fout)
    print('objectClass: top', file=fout)
    print('objectClass: inetOrgPerson', file=fout)
    print('objectClass: posixAccount', file=fout)
    print('uid: {0}'.format(uname), file=fout)
    print('cn: {0}'.format(uname), file=fout)
    print('sn: {0}'.format(fullname), file=fout)
    print('uidNumber: {0}'.format(uid), file=fout)
    print('gidNumber: {0}'.format(opt_gid), file=fout)
    print('homeDirectory: /home/{0}'.format(uname), file=fout)
    print('mail: {0}'.format(addr), file=fout)
    print('loginShell: /bin/tcsh', file=fout)
    print('userPassword: {0}'.format(passwd), file=fout)
    fout.close()

    outname = supname + '.cmd'
    fout = open(outname, 'w')

    print('{0} {1}'.format(cmd_add, ldifname), file=fout)

    fout.close()


def out_ldif_mod(supname, uname, ldifname, addr, passwd, ldif_dc,
                 mode='passwd', uid=None, fullname=None, cmd_mod_done=0):

    if uid is None: uid = uid_undefined

    fout = open(ldifname, 'a')
    print('dn: cn={0},ou=Users,{1}'.format(uname, ldif_dc), file=fout)
    print('changetype: modify', file=fout)
    if mode == 'passwd':
        print('replace: userPassword', file=fout)
        print('userPassword: {0}'.format(passwd), file=fout)
    elif mode == 'email':
        print('replace: mail', file=fout)
        print('disabled_account@pfs.ipmu.jp', file=fout)
    if fullname is not None and uname != fullname:
        print('', file=fout)
        print('replace: sn', file=fout)
        print('sn: {0}'.format(fullname), file=fout)
    print('', file=fout)
    fout.close()

    if cmd_mod_done == 0:
        outname = supname + '.cmd'
        fout = open(outname, 'a')

        print('{0} {1}'.format(cmd_add, ldifname), file=fout)

    fout.close()


def out_ldif_mod_group(supname, ldifname, add_group, all_new, cmd_mod_done, remove=0):

    fout = open(ldifname, 'a')

    print('dn: cn={0},ou=Groups,{1}'.format(add_group, ldif_dc_web), file=fout)
    print('changetype: modify', file=fout)
    if remove:
        print('delete: memberUid', file=fout)
    else:
        print('add: memberUid', file=fout)
    for al_uname in all_new:
        print('memberUid: {0}'.format(al_uname), file=fout)
    print('', file=fout)

    fout.close()

    if cmd_mod_done == 0:
        outname = supname + '.cmd'
        fout = open(outname, 'a')

        print('{0} {1}'.format(cmd_add, ldifname), file=fout)
        cmd_mod_done == 1

    return cmd_mod_done


def out_ldif_mod_group_jira(supname, ldifname, add_group, all_new, ldif_dc, cmd_mod_done):

    fout = open(ldifname, 'a')

    print('dn: cn={0},ou=Groups,{1}'.format(add_group, ldif_dc_web), file=fout)
    print('changetype: modify', file=fout)
    print('add: member', file=fout)
    for al_uname in all_new:
        print('member: cn={0},ou=Users,{1}'.format(al_uname, ldif_dc), file=fout)
    print('', file=fout)

    fout.close()

    if cmd_mod_done == 0:
        outname = supname + '.cmd'
        fout = open(outname, 'a')

        print('{0} {1}'.format(cmd_add, ldifname), file=fout)
        cmd_mod_done == 1

    return cmd_mod_done


def get_info(line):

    arr = line.split()
    email = arr[0]
    if len(arr) > 1:
        uname = arr[1]
    else:
        uname = arr[0].split('@')  # assuming uname is string before @ mark

    if len(arr) > 2:
        fullname = ' '.join(arr[2:])
    else:
        fullname = uname

    return email, uname, fullname


if __name__ == '__main__':

    args = get_option()

    is_reset = 0
    is_disable = 0
    cmd_mod_done = 0

    ldif_dc = ldif_dc_shell if args.shell else ldif_dc_web

    # LDAP groups
    ldefgroup = ['tech', 'lm']  # default group to be added
    ldefgroup_jira = ['jira-ldap-users']  # default groupOfMember group (external)
    ldefgroup_disabled = ['disabled']  # group for disabled accounts

    if args.group is not None:
        group_list = [el for g in args.group for el in g]
        for g in group_list:
            ldefgroup.append(g)

    unlink_tex = ('aux', 'log', 'pdf')

    uids = {}  # user id dictionary
    last_uid, uids = read_uid(fname_uid, uids)

    with open(args.fname_addr, 'r') as fh:
        all_lines = fh.readlines()

    all_new = []  # list of new users

    # for --disable, not need to process email/tex, just output ldif and cmd
    if args.disable:

        ldifout = args.fname_addr + '.disable.ldif'

        for al in all_lines:
            email, uname, fullname = get_info(al)
            all_new.append(uname)
            out_ldif_mod(args.fname_addr, uname, ldifout, email, opt_invalid,
                         ldif_dc, mode='passwd',
                         uid=uids[uname], fullname=None, cmd_mod_done=1)
            out_ldif_mod(args.fname_addr, uname, ldifout, email, opt_invalid,
                         ldif_dc, mode='email',
                         uid=uids[uname], fullname=None, cmd_mod_done=1)

        for lg in ldefgroup:
            out_ldif_mod_group(args.fname_addr, ldifout, lg, all_new, 1, remove=1)

        for lg in ldefgroup_disabled:
            out_ldif_mod_group(args.fname_addr, ldifout, lg, all_new, 1)

        outname = args.fname_addr + '.cmd'
        fout = open(outname, 'w')
        print('{0} {1}'.format(cmd_mod, ldifout), file=fout)

        fout.close()

    else:  # reset or create

        for al in all_lines:
            email, uname, fullname = get_info(al)
            all_new.append(uname)
            passwd = make_pass()

            if uname not in uids:
                last_uid += 1
                uids[uname] = last_uid

            ldifout = args.fname_addr + '.' + uname + '.ldif'
            if args.reset:
                out_ldif_mod(args.fname_addr, uname, ldifout, email, passwd, ldif_dc,
                             mode='passwd', uid=uids[uname], fullname=fullname)
            else:
                out_ldif_new(args.fname_addr, uname, ldifout, email, passwd, ldif_dc,
                             uid=uids[uname], fullname=fullname)

            fout_tex = args.fname_addr + '.' + uname + '.tex'
            mod_tex_skel(fname_tex, fout_tex, uname, email, passwd)

            # compile PDF and send email
            res = subprocess.run([cmd_latex, fout_tex], stdout=subprocess.PIPE)
            # make email
            fout_tex = args.fname_addr + '.' + uname + '.pdf'
            fout_email = mod_email_skel(fname_email, fout_tex, uname, email)

            res = subprocess.run(['cat', fout_email, '|', cmd_sendmail, '-i', '-t'], stdout=subprocess.PIPE)

            for ul in unlink_tex:
                os.remove(args.fname_addr + '.' + uname + '.' + ul)

            # email to admin
            fout_email = mod_email_admin_skel(fname_email, uname, email)
            res = subprocess.run(['cat', fout_email, '|', cmd_sendmail, '-i', '-t'], stdout=subprocess.PIPE)

        save_uid(fname_uid, uids)

        # new user: add to LDAP groups

        if args.reset is False:
            ldifout = args.fname_addr + '.mga.ldif'
            for lg in ldefgroup:
                cmd_mod_done = \
                             out_ldif_mod_group(args.fname_addr, ldifout, lg,
                                                all_new, cmd_mod_done)
            if args.jira:
                for lg in ldefgroup_jira:
                    cmd_mod_done = \
                             out_ldif_mod_group_jira(args.fname_addr, ldifout,
                                                     lg, all_new, ldif_dc, cmd_mod_done)
