#!/usr/bin/env python
# coding: utf-8

import datetime
import glob
import html
import json
import os
import re
import sys
import textwrap
import urllib.request

class User:
    def __init__(self, userId, userDict):
        self._dict = userDict

        self.userId = userId
        self.name = userDict.get('display_name', "")
        if self.name == "":
            self.name = userDict['real_name']

        self.image_url = userDict.get('image_72')  # URL to look up avatar image

    def __str__(self):
        return self.name if self.name else ""


class Msg:
    def __init__(self, fileName, msgDict, fileDir):
        self.fileName = fileName
        self._dict = msgDict
        self.fileDir = fileDir 

        self.ts = msgDict['ts']
        self.thread_ts = msgDict.get('thread_ts')
        self.date = datetime.datetime.utcfromtimestamp(float(msgDict['ts']))

        if msgDict['type'] not in ["message"]:
            print(msg); raise RuntimeError("")

        global users
        if msgDict['type'] == 'message' and msgDict.get('subtype') == "bot_message":
            self.user = User(msgDict.get('bot_id', "BID"),
                             dict(display_name=msgDict.get('username', "???")))
        elif msgDict['type'] == 'message' and msgDict.get('subtype') == "channel_join":
            self.user = User('channel_join',
                             dict(display_name=msgDict.get('user_name', None)))
        elif msgDict['type'] == 'message' and msgDict.get('subtype') == "tombstone":
            pass
            # 'text': 'This message was deleted.'
        else:
            try:
                rawUserId = msgDict['user']
            except KeyError:
                pass                            # skip if user is not written
            else:
                if rawUserId not in users:  # probably cross-slack user
                    users[rawUserId] = User(rawUserId, msgDict['user_profile'])

                self.user = users[rawUserId]

        # if 'blocks' in msgDict and msgDict['type'] != 'message':
        if 'blocks' in msgDict and 'bot_id' not in msgDict:
            self.blocks = msgDict['blocks']
        else:
            self.blocks = [dict(elements=[dict(elements=[dict(type='text',
                                                               text=msgDict['text'])])])]
        self.files = msgDict.get('files', [])
            
    def __repr__(self):
        return str(self.blocks)

    @staticmethod
    def get_text(el):
        try:
            text = el['text']
        except KeyError:
            print(el)
            text = "--Oops. Something is wrong. :(--"

        if el.get('style', {}).get('code'):
            text = f"<code>{html.escape(text)}</code>"
        else:
            # Expand user references
            while True:
                mat = re.search(r"<@([^>]+)>", text)
                if not mat:
                    break

                rawUserId = mat.group(1)
                userId = re.sub(r"\|.*$", "", rawUserId) # userId can be e.g. @U3A2P4FEH|cloomis
                if userId in users:
                    userName = f"@{users[userId]}"
                else:
                    userName = f"@{userId}"
                text = re.sub(f"<@{rawUserId}>", userName, text)
            #
            # Some text has HTML-style escapes in it, which we'll deal with at the same time
            # (html.escape will change them back)
            #            
            text = text.replace(r"&amp;", '&')
            text = text.replace(r"&gt;", '>')
            text = text.replace(r"&lt;", '<')

            mat = re.search(r"(&[a-zA-Z]+;)", text)
            if mat:
                print(f"Found '{mat.group(1)}' in raw text {text}")
                import pdb; pdb.set_trace() 

            text = html.escape(text)
            text = text.replace('\n', '<BR>')

        return text

    def getOutput(self, width=100):
        dlfile_list = glob.glob(self.fileDir+'/*')
        output = []
        for block in self.blocks:
            if 'elements' in block.keys():
                for el in block['elements']:
                    preformatted = False
                    if el.get('type') == 'rich_text_preformatted':
                        preformatted = True
                        width = None  # disable wrapping
    
                        output.append("<PRE style=\"white-space: pre-wrap ;\">")
                    elif el.get('type') in ['rich_text_list']:
                        pass
                    elif el.get('type') in ['button']:
                        continue
                    else:
                        if el.get('type') not in [None, 'rich_text_section', 'rich_text_quote']:
                            if block['type'] != 'context':
                                print(el['type'], self.fileName)
                                import pdb; pdb.set_trace() 
    
                    for el2 in el['elements']:
                        if el2['type'] == 'text':
                            output.append(self.get_text(el2))
                        elif el2['type'] in ['rich_text_list', 'rich_text_section']:
                            for el3 in el2['elements']:
                                if el3['type'] == 'user':
                                    output.append(users[el3['user_id']].name)
                                elif el3['type'] == 'link':
                                    output.append(el3['url'])
                                elif el3['type'] == 'channel':
                                    channel = f"#{channels[el3['channel_id']]}"
                                    output.append(channel)
                                elif el3['type'] in ['rich_text_list', 'rich_text_section']:
                                    for el4 in el3['elements']:
                                        if el4['type'] == 'user':
                                            output.append(users[el4['user_id']].name)
                                        elif el4['type'] == 'link':
                                            output.append(el4['url'])
                                        else:
                                            output.append(self.get_text(el4))
                                elif el3['type'] == 'emoji':
                                    emoji = '&#x'+el3['unicode']+';'
                                    output.append(emoji)
                                else:
                                    output.append(self.get_text(el3))
    
                            if preformatted:
                                output.append("</PRE>")
                        elif el2['type'] == 'channel':
                            channel = f"#{channels[el2['channel_id']]}"
                            output.append(channel)
                        elif el2['type'] == 'emoji':  # e.g. {'type': 'emoji', 'name': 'slightly_smiling_face'}
                            if 'unicode' in el2:
                                emoji = '&#x'+el2['unicode']+';'
                            else:
                                emoji = f":{el2['name']}:"
                            output.append(emoji)
                        elif el2['type'] == 'link':
                            url = el2['url']
                            link = f"<a href='{url}'>{url}</a>"
                            output.append(link)
                        elif el2['type'] == 'user':   # e.g. {'type': 'user', 'user_id': 'UA82J1WP3'}
                            user = users.get(el2['user_id'], el2['user_id'])
                            user = f"@{user}"
                            output.append(user)
                        elif el2['type'] == 'broadcast':   # e.g. {'type': 'broadcast', 'range': 'channel'}
                            user = f"@{el2['range']}"
                            output.append(user)
                        else:
                            raise RuntimeError(f"Complain to RHL: {el2}")
    
                    if preformatted:
                        output.append("<PRE style=\"white-space: pre-wrap ;\">")
                            
        if width and False:
            output = textwrap.wrap(" ".join(output), width)

        if self.files:
            output.append("<UL style='list-style: none;'>")
            for f in self.files:
                thumb = "thumb_360"

                if f.get('mode') == "tombstone":
                    output.append("(This file was deleted)")
                    continue

                if f.get('mode') == "hidden_by_limit":
                    tmp_l = [s for s in dlfile_list if f['id'] in s]
                    filesName = tmp_l[0]
                    filesStr = os.path.join(os.path.basename(self.fileDir) , filesName.rsplit('/')[-1])
                else:
                    filesName = os.path.join(self.fileDir, f['id'] + '_' + f['name'])
                    filesStr = os.path.join(os.path.basename(self.fileDir), f['id'] + '_' + f['name'])
                # print(filesName,filesStr)

                if not os.path.exists(filesName):
                    try:
                        urllib.request.urlretrieve(f['url_private_download'], filesName)
                    except KeyError:
                        urllib.request.urlretrieve(f['url_private'], filesName)

                thumbName = filesName + '.thumb.png'
                if thumb in f:
                    if not os.path.exists(thumbName):
                        urllib.request.urlretrieve(f['thumb_360'], thumbName)
                    nameStr = f"<IMG SRC='{filesStr}.thumb.png'></IMG>"
                    # nameStr = f"<IMG SRC='{f['thumb_360']}'></IMG>"
                else:
                    if os.path.exists(thumbName):
                        nameStr = f"<IMG SRC='{filesStr}.thumb.png'></IMG>"
                    #filesName = os.path.join(self.fileDir, f['id'] + '_' + f['name'])
                    # if not os.path.exists(filesName):
                    #    urllib.request.urlretrieve(f['url_private_download'], filesName)
                    # filesStr = os.path.join(os.path.basename(self.fileDir), f['id'] + '_' + f['name'])
                    else:
                        nameStr = os.path.basename(filesStr)
                    # nameStr = f['name']

                '''
                try:
                    output.append(f"<LI><A HREF='{f['url_private_download']}'>{nameStr}</A></LI>")
                except KeyError:
                    output.append(f"<LI><A HREF='{f['url_private']}'>{nameStr}</A></LI>")
                '''

                output.append(f"<LI><A HREF='{filesStr}'>{nameStr}</A></LI>")

            output.append("</UL>")
                
        return output

    def __str__(self):
        return "\n".join(self.getOutput())

def format_msg(msg, indent=""):
    """Format a single message, possibly with an indent at the start of each line"""
    
    output = []
    indent = ""
    output.append("<DT>")

    timeStr = msg.date.strftime('%a %Y-%m-%d %I:%M%p')

    if hasattr(msg, 'user'):
        img = f"<img width=16 height=16 src={msg.user.image_url}></img>" if msg.user.name else ""
        output.append(f"{img}  {str(msg.user):25s}  {timeStr}")

    output.append("</DT><DD>")

    outputStr = "\n".join(msg.getOutput())

    try:
        msg.fileName.encode('ascii')
    except UnicodeEncodeError:
        pass                            # don't bother to fix Japanese text!
    else:
        for ci, co in [('’', "'"), 
                       ('…', '...'),
                       ('…', '...'),
                       ('“', '"'),
                       ('”', '"'),
                       ('´', "'"),
                       (' ', '_'),
                       ('—', '-'),
                       ('·', '.'),
                       ('⌘', '&smashp;'),   # not great
                       ('\U0010fc0e', '?'), # '?' in a square
                       ('？', '?'),
                       ('、', ','),  # zenkau kuten
                       ('±', '&plusmn;'),
                       ('²', '&sup2;'),
                       ('§', '&;'),
                       ('§', '&sect;'),
                       ('α', '&alpha;'),
                       ('𝛼', '&alpha;'),
                       ('µ', '&mu;'),
                       ('１', '1'),  # zenkau 1
                       ('２', '2'),  # zenkau 2
                       ('Å', '&Aring;'),
                       ('À', '&Agrave;'),
                       ('à', '&agrave;'),
                       ('à', '&agrave;'),
                       ('á', '&aacute;'),
                       ('â', '&acirc;'),
                       ('ā', '&amacr;'),
                       ('Ç', '&Ccedil;'),
                       ('ć', '&cacute;'),
                       ('ç', '&ccedil;'),
                       ('ë', '&euml;'),
                       ('é', '&eacute;'),
                       ('é', '&eacute;'),
                       ('É', '&Eacute;'),
                       ('è', '&egrave;'),
                       ('ê', '&ecirc;'),
                       ('¡', 'i'),
                       ('í', '&iacute;'),
                       ('Í', '&Iacute;'),
                       ('ó', '&oacute;'),
                       ('ñ', '&ntilde;'),
                       ('ö', '&ouml;'),
                       ('û', '&ucirc;'),
                       ('ü', '&uuml;'),
                       ('ù', '&ugrave;'),
                       ('ž', '&zcaron;'),
                       ('λ', '&lambda;'),
                       ('σ', '&sigma;'),
                       ('Σ', '&Sigma;'),
                       ('þ', '&thorn;'),
                       ('•', '&bull;'),
                       ('◯', '&#9711;'),
                       ('Ⰳ', '&#x2C03;'), # Glagolitic_script : ⰾⰰⰳⱁⰾⰹⱌⰰ
                       ('ⰰ', '&#x2C30;'),
                       ('ⰳ', '&#x2C33;'),
                       ('ⱁ', '&#x2C41;'),
                       ('ⰾ', '&#x2C34;'),
                       ('ⰹ', '&#x2C39;'),
                       ('ⱌ', '&#x2C4C;'),
                       ('􏰎', ' '),
                       ('°', '&deg'),
                       ('ï', '&iuml;'),  # really i dieresis
                       ('ô', '&ocirc;'),
                       ('γ', '&upsilon;'),
                       ('–', '-'),
                       ('‘', "'"),
                       ('：', ":"),
                       ('↑', '&uarr;'),
                       ('\u2502', '|'),  # Box drawings light vertical
                       ('↓', '&darr;'),
                       ('←', '&larr;'),
                       ('→', '&rarr;'),
                       ('×', '&#10005;'),
                       ('ʻ', '\''),
                       ('├', '&#9500;'),
                       ('─', '&#9472;'),
                       ('└', '&#9492;'),
                       ('　', '&emsp;'), # zenkaku space
                       ('（', '('), # zenkaku left-parenthesis
                       ('❯', '>'), 
                       ('≲', '&#8830;'),
                       ('‎', ''),  # left-to-right mark

        ]:
            outputStr = outputStr.replace(ci, co)

        try:
            outputStr.encode('ascii')
        except UnicodeEncodeError as e:
            if re.search("[\u3040-\u30ff\u4e00-\u9FFF]", outputStr):
                if False:
                    print(f"In {msg.fileName} Japanese character: {outputStr[e.start:e.end]}", file=sys.stderr)
            else:
                print(f"In {msg.fileName} (ts: {msg.ts}) non-ascii character: {outputStr[e.start:e.end]}", file=sys.stderr)
                print(f"non-ascii character: {outputStr[e.start:e.end]}", file=sys.stderr)
                pass

    output.append(outputStr)
    
    output.append("</DD>")

    return indent + f"\n{indent}".join(output)

def formatSlackArchive(rootDir, channelList=None, outputDir=None, fileDir='_files', projectName="PFS"):
    """Format a slack archive to be human readable

    If channelList is not None, it's a list of channels to process (otherwise
    we process all of them)

    The layout is expected to be like:
       rootdir/channel1/date1.json
                        date2.json
               channel2/date1.json
                        date2.json
               ...

    and the output is
        outputDir/channel1.html
                  channel2.html
                  ...
    """

    if outputDir == None:
        outputDir = rootDir

    if not os.path.isdir(outputDir):
        os.makedirs(outputDir)
    fileDir = outputDir + '/' +fileDir
    if not os.path.isdir(fileDir):
        os.makedirs(fileDir)
    #
    # Start by defining all channels and users
    #
    data = []
    for fn in ["channels.json", "channels-extra.json",]:
        if os.path.exists(os.path.join(rootDir, fn)):
            with open(os.path.join(rootDir, fn)) as fd:
                data += json.load(fd)

    global channels
    channels = {}
    for msg in data:
        channels[msg['id']] = msg['name']

    with open(os.path.join(rootDir, "users.json")) as fd:
        data = json.load(fd)

    global users
    users = {}
    for msg in data:
        user = User(msg['id'], msg['profile'])
        users[user.userId] = user
    #
    # Then read all the messages
    #
    global msgs, threads
    msgs = {}
    threads = {}
    inputFiles = {} 
    for channel in glob.glob(os.path.join(rootDir, "*")):
        if not os.path.isdir(channel):  # e.g. older channel.txt outputs
            continue

        channelName = os.path.split(channel)[-1]

        if channelList is not None and channelName not in channelList:
            continue

        msgs[channelName] = []
        threads[channelName] = {}

        inputFiles[channelName] = sorted(glob.glob(os.path.join(rootDir, channelName, "20*.json")))
        for fileName in inputFiles[channelName]:
            with open(fileName) as fd:
                data = json.load(fd)

            for msg in data:
                if msg.get('subtype') in ["file_comment"]:
                    continue

                msg = Msg(fileName, msg, fileDir)
                msgs[channelName].append(msg)

                if msg.thread_ts:
                    if msg.thread_ts not in threads[channelName]:
                        threads[channelName][msg.thread_ts] = []
                    threads[channelName][msg.thread_ts].append(msg)
    #
    # Ready for output
    #
    for channel in msgs:
        if len(inputFiles[channel]) == 0:
            continue

        dates = [os.path.splitext(os.path.split(f)[1])[0] for f in inputFiles[channel]]
        title = f"{projectName} slack archives {channel} {dates[0]}---{dates[-1]}"
        with open(os.path.join(outputDir, f"{channel}.html"), "w") as fd:
            print(f"""
    <HTML>
    <HEAD>
      <meta charset="utf-8"/>
      <TITLE>{title}</TITLE>
    </HEAD>

    <BODY>
    <H3>{title}</H3>

    <DL>""", file=fd)

            for msg in msgs[channel]:
                if msg.thread_ts in threads[channel]:
                    msgs_thread = threads[channel][msg.thread_ts]
                    if msg != msgs_thread[0]:
                        continue   # already processed

                    print(format_msg(msg), file=fd)

                    if len(msgs_thread) > 1:
                        print("<DT></DT><DD><DL>", file=fd)

                    for m in msgs_thread[1:]:
                        print(format_msg(m, "|\t"), file=fd)

                    if len(msgs_thread) > 1:
                        print("</DD></DL>", file=fd)

                else:
                    print(format_msg(msg), file=fd)

                print('', file=fd)

            print(f"""
    </DL>
    </BODY>
    </HTML>""", file=fd)

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
           

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="")

    parser.add_argument('rootDir', type=str, help="Directory containing directories with json")
    parser.add_argument('--outputDir', '-o', help="Directory to write files; default <rootDir>")
    parser.add_argument('--channels', '-c', nargs="+", help="Only process these channels")
    parser.add_argument('--project', '-p', help="Name of project; default PFS", default="PFS")
    parser.add_argument('--fileDir', '-f', default='_files', help="Directory to store downloaded files")

    args = parser.parse_args()

    formatSlackArchive(args.rootDir, channelList=args.channels,
                       outputDir=args.outputDir, fileDir=args.fileDir, projectName=args.project)
