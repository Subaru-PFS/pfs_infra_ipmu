#! /usr/bin/env python

import libvirt
import sys
import os
import pfsvirt

DEF_GB_MB = 1024.0
DEF_GB_KB = 1048576.0
DEF_GB_B  = 1073741824.0

ERR_NOT_RUNNING = 1
ERR_NO_CONNECT = 2

def print_server(name, target_uri, summary):
    try:
        lv_conn = libvirt.openReadOnly(target_uri)
    except libvirt.libvirtError:
        return ERR_NOT_RUNNING
    if lv_conn == None:
        return ERR_NO_CONNECT
    print("Information for '{0:s}':".format(name))
    node_info = lv_conn.getInfo()
    node_mem = lv_conn.getMemoryStats(libvirt.VIR_NODE_MEMORY_STATS_ALL_CELLS)
    print(("  Memory : {:5.1f} GB / {:5.1f} GB free, {:5.1f} GB cached, " + \
        "{:5.1f} GB buffers").format( \
        node_mem['total'] / DEF_GB_KB, node_mem['free'] / DEF_GB_KB, 
        node_mem['cached'] / DEF_GB_KB, node_mem['buffers'] / DEF_GB_KB))
    print(("  VCPUs  : {0[0]:2d} in {0[1]:2d} MHz ({0[2]:1d} NUMA, " + \
        "{0[3]:1d} socket, {0[4]:2d} core, {0[5]:1d} thread)").format( \
        node_info[2:8]))
    # getCPUStats(cpu_id) seems to return in cumulative nsec
    print("  CPU    : Model \"{}\"".format(node_info[0]))
    if node_info[4] > 1:
        print("  Memory per NUMA")
        for numa in xrange(node_info[4]):
            buf = lv_conn.getMemoryStats(numa)
            print("    NUMA {:2d}: {:5.1f} GB free in {:5.1f} GB total".format( \
                numa, buf['free'] / DEF_GB_KB, buf['total'] / DEF_GB_KB))
    lv_doms = lv_conn.listAllDomains(0)
    print("  domains:")
    mem_doms = [0, 0] # [max, cur]
    cpu_doms = [0, 0] # [max, cur]
    for lv_proc in lv_doms:
        lv_info = lv_proc.info()
        lv_state = _getStringForState(lv_info[0])
        lv_info[1] /= DEF_GB_KB # max
        lv_info[2] /= DEF_GB_KB # cur
        mem_doms[0] += lv_info[1]
        mem_doms[1] += lv_info[2]
        if lv_info[0] == libvirt.VIR_DOMAIN_RUNNING:
            print(("    {0:15s} ({1:2d}): {2:s} Mem {3[2]:5.1f}GB " + \
                "({3[1]:5.1f}GB max) {3[3]:2d}CPU ({4:2d} max)" \
                ).format(lv_proc.name(), lv_proc.ID(), lv_state, lv_info, \
                lv_proc.maxVcpus()))
            cpu_doms[0] += lv_proc.maxVcpus()
            cpu_doms[1] += lv_info[3]
        else:
            print(("    {0:15s} (--): {1:s} Mem {2[2]:5.1f}GB " + \
                "({2[1]:5.1f}GB max) --CPU ({2[3]:2d} max)" \
                ).format(lv_proc.name(), lv_state, lv_info))
            cpu_doms[0] += lv_info[3]
    mem_free = node_info[1] / DEF_GB_MB - mem_doms[0]
    print("  Memory usage: {:4.1f}GB ({:4.1f}GB max) {:4.1f}GB allocatable" \
        .format(mem_doms[1], mem_doms[0], mem_free))
    print("  CPU usage   : {:2d} ({:2d} total) {:2d} VCPUs allocatable" \
        .format(cpu_doms[1], cpu_doms[0], (node_info[2] - cpu_doms[0])))
    node_summary = [ name, \
        cpu_doms[1], cpu_doms[0], node_info[2], node_info[3], \
        mem_doms[1], mem_doms[0], (node_mem['total'] / DEF_GB_KB) ]
    summary.append(node_summary)
    lv_conn.close()
    return None

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
        print("Configuration '{:s}' load error: {:s}".format(cmd_opt, e))
    not_run = []
    no_conn = []
    vm_summ = []
    for item in objConfig.GetListServers():
        err = print_server(item, objConfig.GetUri(item), vm_summ)
        if err == ERR_NOT_RUNNING:
            not_run.append(item)
        elif err == ERR_NO_CONNECT:
            no_conn.append(item)
        else:
            print("")
    print("")
    print("Summary ([cur]/[max] with [system])")
    for item in vm_summ:
        print(("{:10s}: CPU {:2d}/{:2d} with {:2d}/{:4d}MHz " + \
            "Mem {:5.1f}/{:5.1f}GB with {:5.1f}GB").format(*item))
    print("")
    if len(not_run) > 0:
        print("Targets not running: ")
        for item in not_run:
            print(" {:s}".format(item))
        print("")
    if len(no_conn) > 0:
        print("Targets failed to connect: ")
        for item in no_conn:
            print(" {:s}".format(item))
        print("")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: <script> <json configuration file>")
        sys.exit(1)
    main(sys.argv[1])

