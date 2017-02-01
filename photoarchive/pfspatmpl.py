#! /usr/bin/env python

import os
import sys

DEF_CONF_ROW = 5

TMPL_HTMLHEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Photo Archive for %s</title>
</head>
<table>
<tr>
"""
TMPL_HTMLLINK = """<td><a href="%s"><img src="%s" /></a></td>"""
TMPL_HTMLIMG  = """%s (%s)<br />(w %d x h %d)"""
TMPL_HTMLVIDEO = """%s (%s)<br />(w %d x h %d, %.2f fps, %.2f sec)"""
TMPL_HTMLFOOT = """</tr></table></html>"""

# Shall be relaced to real template engine for production

class Template(object):
    conf_row = DEF_CONF_ROW;
    data_out = None
    data_name = ''

    def SetConfig(self, objConfig):
        try:
            crow = objConfig.GetConfigThumb('rows')
        except:
            crow = DEF_CONF_ROW
        self.conf_row = crow

    def SetData(self, objData, title):
        self.data_out = objData
        self.data_name = title

    def Write(self, objFH):
        if self.data_out == None:
            raise Exception("Data not set")
        objFH.write(TMPL_HTMLHEAD % self.data_name)
        ccnt = 0
        ctxt = []
        foth = {}
        for fname in self.data_out.keys():
            cdat = self.data_out[fname]
            if cdat['category'] == 'video':
                objFH.write(TMPL_HTMLLINK % (cdat['orig'], cdat['thumb']))
                co = cdat['video']
                ctxt.append(TMPL_HTMLVIDEO % (fname, co['format'], co['width'], co['height'], co['fps'], co['duration']))
            elif cdat['category'] == 'image':
                objFH.write(TMPL_HTMLLINK % (cdat['orig'], cdat['thumb']))
                co = cdat['image']
                ctxt.append(TMPL_HTMLIMG % (fname, co['format'], co['width'], co['height']))
            else:
                foth[fname] = cdat
                continue
            ccnt += 1
            if ccnt == self.conf_row:
                ccnt = 0
                objFH.write("</tr><tr>")
                for c in ctxt:
                    objFH.write("<td>%s</td>" % (c))
                objFH.write("</tr><tr>")
                ctxt = []
        objFH.write("</tr><tr>")
        for c in ctxt:
            objFH.write("<td>%s</td>" % (c))
        objFH.write(TMPL_HTMLFOOT)

