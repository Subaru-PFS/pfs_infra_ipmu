#! /usr/bin/env python

import sys
import json

class PFSVirtConfig(object):

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

    def GetUri(self, target):
        self._verifyConfig()
        if target == "":
            raise Exception("No target specified")
        if not self.config['servers'].has_key(target):
            raise Exception("Configuration missing")
        conf_target = self.config['servers'][target]
        conn_mode = conf_target['mode'] if conf_target.has_key('mode') else 'tls'
        conn_addr = conf_target['addr']
        return "qemu+%s://%s/system" % (conn_mode, conn_addr)

    def GetListServers(self):
        self._verifyConfig()
        return self.config['servers'].keys()

    def IsServerDefined(self, target):
        self._verifyConfig()
        if target == "":
            raise Exception("No target specified")
        if not self.config['servers'].has_key(target):
            return False
        return True

    def _verifyConfig(self):
        if self.config == None:
            raise Exception("Configuration not loaded")
        if not self.config.has_key('servers'):
            raise Exception("Configuration 'servers' block is required")
        return True

def selftest():
    if len(sys.argv) < 2:
        raise Exception("Option not added. Use as <script> <json filename>")
    objConfig = PFSVirtConfig()
    objConfig.Load(sys.argv[1])
    print objConfig.Dump(True)
    if objConfig.IsServerDefined('sample'):
        print "URI for 'sample': %s" % (objConfig.GetUri('sample'))

if __name__ == "__main__":
    selftest()
