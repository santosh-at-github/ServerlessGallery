from __future__ import print_function
import boto3
import botocore
#import time
import urllib
import os
import sys
import string
import json
import subprocess
from PIL import Image, ImageFile

DBucket = 'dnd-sntkum-thmbnail'
s3 = boto3.client('s3')

def S3Download (bucket, key, downfile):
    try:
        s3.download_file(bucket, key, downfile)
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        print("Error in Downloading file", bucket, "/", key, "ErrorCode: ", error_code)
        return "Failed"
    return "Success"

def S3Upload(dimage, bucket, key):
    if os.path.isfile(dimage):
        s3.upload_file(dimage, bucket, key)
        print("Image upload complete")
        return dimage
    else:
        print("File ", dimage, "does not exists!! Failed to upload Image to S3!!")
        return 10

def JpgConvert(Simage, Size):
    Dpath='/tmp/Converted/'
    if not os.path.exists(Dpath):
        os.makedirs(Dpath)
    Dimage = Dpath + os.path.basename(Simage)
    img_file = Image.open(Simage)
    if Size == 'Shrinked':
        try:
            img_file.save(Dimage, format='JPEG', optimize=True, quality=30, progressive=True)
        except IOError as e:
            print("Error in saving optimizing the image. Error: ", e)
            return "Failed"
        return Dimage
    else:
        baseWidth = int(Size)
        widthPercent = (baseWidth / float(img_file.size[0]))
        height = int((float(img_file.size[1]) * float(widthPercent)))
        try:
            img=img_file.resize((baseWidth, height), Image.BILINEAR)
            img.save(Dimage, format='JPEG', optimize=True, progressive=True)
        except IOError as e:
            print("Error in resizing and saving JPEG image. Error: ", e)
            return "Failed"
        return Dimage

def RawConvert(bucket, key, simage, Size):
    #print("From Function RawConvert")
    CWD = os.getcwd()
    #CWD='/mnt'
    ufraw = CWD + "/ufraw-batch"
    simage = str(simage)
    jimage = simage.replace('.NEF', '')
    dimage = jimage + ".jpg"
    Size = str(Size)

    if Size == 'Original':
        bashcommand = "set -x; export LD_LIBRARY_PATH=" + CWD + "; " + ufraw + " --wb=auto --out-path=/tmp/ --out-type=jpeg --overwrite --silent --exposure=1.9 --out-depth=16 --restore=hsv " + simage
        jkey = os.path.dirname(key) + "/" + Size + "/" + os.path.basename(dimage)
    elif Size == 'Shrinked':
        bashcommand = "set -x; export LD_LIBRARY_PATH=" + CWD + "; " + ufraw + " --wb=auto --out-path=/tmp/ --out-type=jpeg --overwrite --silent --exposure=2.9 --out-depth=16 --restore=hsv --shrink=6 " + simage
        jkey = os.path.dirname(key) + "/" + Size + "/" + os.path.basename(dimage)
    else:
        bashcommand = "set -x; export LD_LIBRARY_PATH=" + CWD + "; " + ufraw + " --wb=auto --out-path=/tmp/ --out-type=jpeg --overwrite --silent --exposure=1.9 --out-depth=16 --restore=hsv --size=" + Size + " " + simage
        jkey = os.path.dirname(key) + "/" + Size + "x" + Size + "/" + os.path.basename(dimage)

    try:
        p = subprocess.Popen(bashcommand, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, bufsize = -1)
        (output, err) = p.communicate()
        p_status = p.wait()
        #========== TestCode =============
        print("Command Output: ", output)
        print("Return Code: ", p_status)
        #print(subprocess.check_output("uname -a".split(' ')))
        #print(subprocess.check_output("cat /etc/issue".split(' ')))
        #print(subprocess.check_output("find /tmp/ -ls".split(' ')))
        #=================================
        #retcode = os.system(bashcommand)
        if p_status != 0:
            print("RawConvert child was terminated with exit status ", p_status, file=sys.stderr)
        else:
            print("Child returned exit status ", p_status, file=sys.stderr)
            print("Image Conversion complete")
    except OSError as e:
        print("Execution failed: ", e)

    #========== TestCode =============
    #print(bashcommand)
    #print(p_status)
    #print(dimage)
    #print(DBucket)
    #print(jkey)
    print(subprocess.check_output("find /tmp/ -ls".split(' ')))
    #=================================
    #if os.path.isfile(PATH) and os.access(PATH, os.R_OK):
    #jkey=os.path.dirname(key) + "/" + os.path.basename(dimage)
    status = S3Upload(dimage, DBucket, jkey)
    return status

def lambda_handler(event, context):
    print('Loading function')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'])
    print(bucket, key)
    downfile = "/tmp/" + os.path.basename(key)
    status = S3Download(bucket, key, downfile)
    if status == "Success":
        print("Downloded image ", key, "successfully from S3 bucket")
    else:
        print("Failed to download Image file form S3, aborting scripr eecution")
        sys.exit(20)

    ext=str(key).split('.')[-1].lower()
    if ext == 'nef' or ext == 'NEF':
        dimage=RawConvert(bucket, key, downfile, 'Original')
        if str(dimage) != '10':
            print("Successfully converted image ", bucket, "/", key, " to .jpg size Original and uploded to S3")
            os.remove(dimage)
        else:
            os.remove(downfile)
            print("Failed to convert image file to .jpg")

        dimage = RawConvert(bucket, key, downfile, 'Shrinked')
        if str(dimage) != '10':
            print("Successfully converted image ", bucket, "/", key, " to .jpg size Shrinked and uploded to S3")
            os.remove(dimage)
        else:
            os.remove(downfile)
            print("Failed to convert image file to .jpg")

        dimage = RawConvert(bucket, key, downfile, 100)
        if str(dimage) != '10':
            print("Successfully converted image ", bucket, "/", key, " to .jpg size 100 and uploded to S3")
            os.remove(dimage)
        else:
            os.remove(downfile)
            print("Failed to convert image file to .jpg")

        dimage = RawConvert(bucket, key, downfile, 200)
        if str(dimage) != '10':
            print("Successfully converted image ", bucket, "/", key, " to .jpg size 200 and uploded to S3")
            os.remove(dimage)
        else:
            os.remove(downfile)
            print("Failed to convert image file to .jpg")

        dimage = RawConvert(bucket, key, downfile, 400)
        if str(dimage) != '10':
            print("Successfully converted image ", bucket, "/", key, " to .jpg size 400 and uploded to S3")
            os.remove(dimage)
        else:
            os.remove(downfile)
            print("Failed to convert image file to .jpg")
    elif ext == 'jpg' or ext == 'jpeg':
        Size='Shrinked'
        dimage = JpgConvert(downfile, Size)
        if str(dimage) != 'Failed':
            print("Image Converted successfully")
            jkey = os.path.dirname(key) + "/" + str(Size) + "/" + os.path.basename(dimage)
            status = S3Upload(dimage, DBucket, jkey)
            if str(status) != '10':
                print("Image ", DBucket, jkey, "uploded to S3 successfully")
            else:
                print("Failed to upload image ", dimage, "to S3")
        else:
            print("Failed to convert image", downfile)
        Size=200
        dimage = JpgConvert(downfile, Size)
        if str(dimage) != 'Failed':
            print("Image Converted successfully")
            jkey = os.path.dirname(key) + "/" + str(Size) + "x" + str(Size) + "/" + os.path.basename(dimage)
            status = S3Upload(dimage, DBucket, jkey)
            if str(status) != '10':
                print("Image ", DBucket, jkey, "uploded to S3 successfully")
            else:
                print("Failed to upload image ", dimage, "to S3")
        else:
            print("Failed to convert image ", downfile)

    os.remove(downfile)
    print("Clenaup Completed!! Finished Code Execution")
