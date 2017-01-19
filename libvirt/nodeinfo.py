#! /usr/bin/env python

import libvirt
import sys
import os
import pfsvirt

def print_server(name, target_uri):
    try:
        lv_conn = libvirt.openReadOnly(target_uri)
    except libvirt.libvirtError:
        print "Target '{}' is not running".format(target_uri)
        return None
    if lv_conn == None:
        print "Failed to connect '{}'".format(target_uri)
        return None
    print "Information for '%s':" % (name)
    node_info = lv_conn.getInfo()
    print "  Memory : {:.1f} GB / {:.1f} GB free".format( \
        node_info[1] / 1024.0, lv_conn.getFreeMemory() / 1073741824.0)
    print ("  VCPUs  : {0[0]:d} in {0[1]:d} MHz ({0[2]:d} NUMA, " + \
        "{0[3]:d} socket, {0[4]:d} core, {0[5]:d} thread)").format( \
        node_info[2:8])
    lv_doms = lv_conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)
    print "  domains:"
    for lv_proc in lv_doms:
        lv_info = lv_proc.info()
        lv_state = _getStringForState(lv_info[0])
        lv_info[1] /= 1048576.0
        lv_info[2] /= 1048576.0
        print ("    {0:15s} ({1:2d}): {2:s} Mem {3[2]:.1f}GB " + \
            "({3[1]:.1f}GB max) {3[3]:d}CPU ({4:d} max)") \
            .format(lv_proc.name(), lv_proc.ID(), lv_state, lv_info, \
            lv_proc.maxVcpus())
    lv_conn.close()

def _getStringForState(state):
    if state == libvirt.VIR_DOMAIN_NOSTATE:
        str_state = 'NOSTATE'
    elif state == libvirt.VIR_DOMAIN_RUNNING:
        str_state = 'RUNNING'
    elif state == libvirt.VIR_DOMAIN_BLOCKED:
        str_state = 'BLOCKED'
    elif state == libvirt.VIR_DOMAIN_PAUSED:
        str_state = 'PAUSED '
    elif state == libvirt.VIR_DOMAIN_SHUTDOWN:
        str_state = 'SHUTDWN'
    elif state == libvirt.VIR_DOMAIN_SHUTOFF:
        str_state = 'SHUTOFF'
    elif state == libvirt.VIR_DOMAIN_CRASHED:
        str_state = 'CRASHED'
    elif state == libvirt.VIR_DOMAIN_PMSUSPENDED:
        str_state = 'SUSPEND'
    else:
        str_state = 'UNKNOWN'
    return str_state

def main(cmd_opt):
    objConfig = pfsvirt.PFSVirtConfig()
    try:
        objConfig.Load(cmd_opt)
    except e:
        print "Configuration '%s' load error: %s" % (cmd_opt, e)
    for item in objConfig.GetListServers():
        print_server(item, objConfig.GetUri(item))
        print ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: <script> <json configuration file>"
        sys.exit(1)
    main(sys.argv[1])

