#! /usr/bin/env python

import sys
import json
import os

DEF_VIDEO_PLACE  = 0.5
DEF_THUMB_SIZE   = 250

class PFSPhotArchConfig(object):

    def Load(self, fname):
        try:
            fjson = open(fname, 'r')
        except IOError, e:
            raise Exception("File '%s' open error: %s" % (fname, e))
        try:
            self.config = json.load(fjson)
        except:
            raise Exception("json format parse error for '%s'" % (fname))

    def Dump(self, pretty=False):
        self._verifyConfig()
        opt_indent = 4 if pretty else None
        try:
            return json.dumps(self.config, indent=opt_indent)
        except e:
            raise Exception("Json format error: %s" % (e))

    def GetDirectory(self, target):
        self._verifyConfig()
        objConf = self.config['config']
        if not objConf.has_key('data'):
            raise Exception("Configuration for root directory not found")
        if target == "":
            return objConf['data']
        if not objConf.has_key(target):
            raise Exception("Configuration for '%s' not found" % (target))
        return objConf[target]

    def GetConfigThumb(self, target):
        self._verifyConfig()
        objConf = self.config['thumbnail']
        if target == "":
            raise Exception("No target specified")
        if not objConf.has_key(target):
            if (target == 'size'):
                return DEF_THUMB_SIZE
            raise Exception("Configuration for '%s' not found" % (target))
        return objConf[target]

    def GetConfigVideoThumb(self, duration):
        self._verifyConfig()
        objConf = self.config['thumbnail']
        cPos = objConf['video_pos'] if objConf.has_key('video_pos') else DEF_VIDEO_PLACE
        cUnit = objConf['video_unit'] if objConf.has_key('video_unit') else 'relative'
        if cUnit == 'relative':
            if (cPos < 0.0) or (cPos > 1.0):
                raise Exception("Relative position %f is not valid" % (cPos))
            ret = duration * cPos
        elif cUnit == 'sec':
            if (cPos < 0.0) or (cPos > duration):
                ret = duration * DEF_VIDEO_PLACE
            else:
                ret = cPos
        else:
            raise Exception("Unit '%s' is not valid" % (cUnit))
        return ret

    def _verifyConfig(self):
        if self.config == None:
            raise Exception("Configuration not loaded")
        if not self.config.has_key('config'):
            raise Exception("Configuration 'config' block is required")
        if not self.config.has_key('thumbnail'):
            raise Exception("Configuration 'thumbnail' block is required")
        return True

def selftest():
    if len(sys.argv) < 2:
        raise Exception("Option not added. Use as <script> <json filename>")
    objConfig = PFSPhotArchConfig()
    objConfig.Load(sys.argv[1])
    print objConfig.Dump(True)

if __name__ == "__main__":
    selftest()
