#! /usr/bin/env python3
# Parse json(+) output from fio into TSV

import sys
import json

RW_CONFIG = { 'read': 'read', 'write': 'write', 'trim': 'trim', 
    'randread': 'read', 'randwrite': 'write', 'randtrim': 'trim' }

def LoadJson(fname):
    try:
        fjson = open(fname, 'r')
    except IOError as e:
        raise Exception("File '%s' open error: %s" % (fname, e))
    try:
        fdata = json.load(fjson)
    except:
        raise Exception("json format parse error for '%s'" % (fname))
    return fdata

def GetOptions(json):
    opts = {}
    if 'global options' in json:
        for item in json['global options'].keys():
            opts[item] = json['global options'][item]
    if 'job options' in json['jobs'][0]:
        for item in json['jobs'][0]['job options'].keys():
            opts[item] = json['jobs'][0]['job options'][item]
    return opts

def GetJobData(json, data):
    for item in [ 'jobname', 'usr_cpu', 'sys_cpu', 'ctx', 'majf', 'minf' ]:
        data[item] = json[item]

def GetRWData(json, data):
    for item in [ 'bw', 'iops', 'runtime' ]:
        data[item] = json[item]
    for item in [ 'min', 'max', 'mean', 'stddev' ]:
        data['clat_' + item] = json['clat'][item]
        data['lat_' + item] = json['lat'][item]
    return data

def ExecOneJson(fname, fout):
    fdata = LoadJson(fname)
    fopts = GetOptions(fdata)
    frwda = {}
    if fopts['rw'] in RW_CONFIG:
        GetJobData(fdata['jobs'][0], frwda)
        GetRWData(fdata['jobs'][0][RW_CONFIG[fopts['rw']]], frwda)
    else:
        return
    fout.write('{}\t'.format(frwda['jobname']))
    if 'filename' in fopts:
        fout.write('{}\t'.format(fopts['filename']))
    elif 'directory' in fopts:
        fout.write('{}\t'.format(fopts['directory']))
    for item in [ 'rw', 'size', 'bs', 'numjobs' ]:
        if item in fopts:
            fout.write('{}\t'.format(fopts[item]))
        else:
            fout.write('\t')
    for item in [ 'bw', 'iops', 'runtime', 'usr_cpu', 'sys_cpu', 'ctx', \
      'majf', 'minf', 'clat_min', 'clat_max', 'clat_mean', 'clat_stddev', \
      'lat_min', 'lat_max', 'lat_mean', 'lat_stddev']:
        fout.write('{}\t'.format(frwda[item]))
    fout.write('\n')

def PrintHeader(fout):
    fout.write('jobname\ttarget\t')
    for item in [ 'rw', 'size', 'bs', 'numjobs' ]:
        fout.write('{}\t'.format(item))
    for item in [ 'bw', 'iops', 'runtime', 'usr_cpu', 'sys_cpu', 'ctx', \
      'majf', 'minf', 'clat_min', 'clat_max', 'clat_mean', 'clat_stddev', \
      'lat_min', 'lat_max', 'lat_mean', 'lat_stddev']:
        fout.write('{}\t'.format(item))
    fout.write('\n')

def main():
    PrintHeader(sys.stdout)
    for item in range(1, len(sys.argv)):
        ExecOneJson(sys.argv[item], sys.stdout)

if __name__ == '__main__':
  main()


