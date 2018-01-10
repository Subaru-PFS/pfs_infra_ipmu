#! /usr/bin/env python3

import sys

TGT_DIR = [ 'sda1', 'sdb1', 'sdc1' ]
TGT_BS  = [ '4k', '8k', '16k', '1M', '2M', '4M', '32M' ]
TGT_NJ  = [ '1', '2', '4', '8' ]

CONF_GLOBAL = [ 'direct=1', 'rw=read', 'size=32G', 'group_reporting=1' ]

def main():

  fcmd = open('cmd_fio_config.sh', 'w')
  for tdir in TGT_DIR:
    for tbs in TGT_BS:
      for tnj in TGT_NJ:
        fname = 'config_{}_{}_job{}'.format(tdir, tbs, tnj)
        fobj = open(fname + '.ini', 'w')
        fobj.write('[global]\n')
        fobj.write('\n'.join(CONF_GLOBAL))
        fobj.write('\n')
        fobj.write('\n')
        fobj.write('[{}_{}_job{}]\n'.format(tdir, tbs, tnj))
        fobj.write('filename=/mnt/{}/test\n'.format(tdir))
        fobj.write('bs={}\n'.format(tbs))
        fobj.write('numjobs={}\n'.format(tnj))
        fobj.write('name={}_{}_job{}\n'.format(tdir, tbs, tnj))
        fobj.write('\n')
        fobj.close()
        print('Created {}'.format(fname))
        fcmd.write('fio --output-format=json+ --output={}.out {}.ini\n'.format(fname, fname))
  fcmd.close()

if __name__ == '__main__':
  main()


