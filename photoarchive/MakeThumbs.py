#! /usr/bin/env python

import sys
import json
import os
import av
from PIL import Image

import pymagic.magic
import pfspaconf
import pfspatmpl

DEF_THUMB_EXT = '.jpg'

def CheckFile(fname):
    return pymagic.magic.from_file(fname, True)

def ListFiles(dir_root, dir_orig, dir_thumb):
    fdlist = os.listdir(os.path.join(dir_root, dir_orig))
    flist = {}
    for fname in fdlist:
        cfull = os.path.join(dir_orig, fname)
        tfull = os.path.join(dir_thumb, fname) + DEF_THUMB_EXT
        if os.path.isfile(os.path.join(dir_root, cfull)):
            flist[fname] = {'orig': cfull,
                'type': CheckFile(os.path.join(dir_root, cfull)),
                'fname': fname, 't_thumb': tfull }
            cid = flist[fname]['type'].index('/')
            if cid > 0:
                flist[fname]['category'] = flist[fname]['type'][:cid]
            else:
                flist[fname]['category'] = flist[fname]['type']
            flist[fname]['size'] = os.path.getsize(os.path.join(dir_root, cfull))
    return flist

def CheckImageStat(dir_root, flist, objConfig):
    for fname in flist.keys():
        if flist[fname]['category'] != 'image':
            continue
        try:
            objImage = Image.open(str(os.path.join(dir_root, flist[fname]['orig'])))
        except Exception, e:
            print "Error on loading '%s': %s" % (flist[fname]['orig'], e)
            continue
        flist[fname]['image'] = {
            'width':   objImage.size[0],
            'height':  objImage.size[1],
            'format':  objImage.format
        }
        saved = SaveThumbnail(objImage, str(os.path.join(dir_root, flist[fname]['t_thumb'])), objConfig)
        if saved != None:
            flist[fname]['thumb'] = flist[fname]['t_thumb']
            flist[fname]['thumb_width'] = saved['width']
            flist[fname]['thumb_height'] = saved['height']

def CheckMovieStat(dir_root, flist, objConfig):
    for fname in flist.keys():
        if flist[fname]['category'] != 'video':
            continue
        objAv = av.open(str(os.path.join(dir_root, flist[fname]['orig'])))
        tpos = objConfig.GetConfigVideoThumb(objAv.duration / float(av.time_base))
        objAv.seek(tpos)
        objVStrm = objAv.streams.video[0]
        flist[fname]['video'] = {
            'width':    objVStrm.width,
            'height':   objVStrm.height,
            'fps':      1.0 / float(objVStrm.rate),
            'duration': objVStrm.duration * float(objVStrm.time_base),
            'bitrate':  objAv.bit_rate,
            'format':   objVStrm.long_name,
            'thumb_sec': tpos,
        }
        objVPkt = objAv.demux(objVStrm)
        objPIL = None
        for packet in objVPkt:
            objVFrm = packet.decode_one()
            if objVFrm != None:
                objPIL = objVFrm.to_image()
                break
        if objPIL == None:
            continue
        saved = SaveThumbnail(objPIL, str(os.path.join(dir_root, flist[fname]['t_thumb'])), objConfig)
        if saved != None:
            flist[fname]['thumb'] = flist[fname]['t_thumb']
            flist[fname]['thumb_width'] = saved['width']
            flist[fname]['thumb_height'] = saved['height']

def SaveThumbnail(objPIL, target, objConfig):
    if objPIL == None:
        return None
    size = objConfig.GetConfigThumb('size')
    objPIL.thumbnail((size, size), Image.ANTIALIAS)
    objPIL.save(target)
    return {'target': target, 'width': objPIL.size[0], 'height': objPIL.size[1]}

def main(config, target):
    objConfig = pfspaconf.PFSPhotArchConfig()
    try:
        objConfig.Load(config)
        dir_orig = os.path.join(objConfig.GetDirectory('original'), target)
        dir_thumb = os.path.join(objConfig.GetDirectory('thumbnail'), target)
        dir_root = objConfig.GetDirectory('')
    except Exception, e:
        raise Exception("Error on reading configuration '%s' by '%s'" % (config, e))
    try:
        os.mkdir(os.path.join(dir_root, dir_thumb))
    except OSError, e:
        print "Directory '%s' already exists: %s" % (dir_thumb, e)
    flist = ListFiles(dir_root, dir_orig, dir_thumb)
    CheckImageStat(dir_root, flist, objConfig)
    CheckMovieStat(dir_root, flist, objConfig)
    for fname in flist.keys():
        del flist[fname]['t_thumb']
    try:
        ojson = os.path.join(dir_root, target + '.json')
        objFH = open(ojson, 'w')
        objFH.write(json.dumps(flist))
        objFH.close()
    except Exception, e:
        print "File '%s' create failed: %s" % (ojson, e)
        print json.dumps(flist)
    try:
        ohtml = os.path.join(dir_root, target + '.html')
        objFH = open(ohtml, 'w')
        objTmpl = pfspatmpl.Template()
        objTmpl.SetConfig(objConfig)
        objTmpl.SetData(flist, target)
        objTmpl.Write(objFH)
        objFH.close()
    except Exception, e:
        print "File '%s' create failed: %s" % (ohtml, e)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise Exception("<script> <config> <target>")
    main(sys.argv[1], sys.argv[2])
