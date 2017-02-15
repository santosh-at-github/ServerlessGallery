from __future__ import print_function
import boto3
import sys
import os
import urllib
from collections import defaultdict

s3 = boto3.resource('s3')
webs3 = boto3.client('s3')

def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

def S3_Upload(SFile, Dbucket, Dkey):
    print(SFile, Dbucket, Dkey)
    try:
        webs3.upload_file(SFile, Dbucket, Dkey, ExtraArgs={'ContentType': "text/html", 'ACL': "public-read"})
        #webs3.put_object_acl(ACL='public-read', Bucket=Dbucket, Key=Dkey)
        return 0
    except boto3.exceptions.S3UploadFailedError as e:
        print("Failed to upload file to s3. Error: ", e)
        return 10

def lambda_handler(event, context):
    bucket = str(event['Records'][0]['s3']['bucket']['name'])
    key = str(urllib.unquote_plus(event['Records'][0]['s3']['object']['key']))
    print(bucket, key)
    if bucket == "gallery.sntkum.myinstance.com" and key == "GenerateMyStaticGallery.txt": 
        html1='''
        <!doctype html>
        <html>
            <head>
                <meta charset="utf8">
                <title>Gallery</title>
                <link href="https://s3.amazonaws.com/gallery.sntkum.myinstance.com/WebContents/CSS/LandingPagestyles.css" rel="stylesheet" type="text/css">

            </head>

            <body>
                <div id="container">
        '''

        html2='''
                </div>
            </body>
        </html>
        '''

        HtmlData1 = '''
        <!doctype html>
        <html>
            <head>
                <meta charset="utf8">
                <title>Gallery</title>
                <!--[if IE]>
                    <script src="http://html5dhiv.googlecode.com/svn/trunk/html5.js"></script>
                <![endif]-->
                <link href="https://s3.amazonaws.com/gallery.sntkum.myinstance.com/WebContents/CSS/styles.css" rel="stylesheet" type="text/css">

                        <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
                        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
                        <meta name="HandheldFriendly" content="true">

            </head>

            <body>
                <div class="container">
                    <header><h3>Welcome to My gallary</h3></header>
                    <section id="content">
                        <div class="gallery">
                            <ul>
        '''

        HtmlData2 = '''
                            </ul>
                        </div>
                    </section>
                    <footer><p>My Gallary</p></footer>
                </div>
                <!-- Add jQuery library -->
                <script type="text/javascript" src="http://code.jquery.com/jquery-latest.min.js"></script>
                <!-- Add fancyBox -->
                <link rel="stylesheet" href="https://s3.amazonaws.com/gallery.sntkum.myinstance.com/WebContents/source/jquery.fancybox.css" type="text/css" media="screen" />
                <script type="text/javascript" src="https://s3.amazonaws.com/gallery.sntkum.myinstance.com/WebContents/source/jquery.fancybox.pack.js"></script>
                        <script type="text/javascript">
                            $(document).ready(function() {
                                $('.fancybox-buttons').fancybox({
                                        openEffect  : 'elastic',
                                        openSpeed  : 150,
                                        closeEffect : 'elastic',
                                        closeSpeed  : 150,
                                        closeClick : true,
                                        prevEffect : 'elastic',
                                        nextEffect : 'elastic',

                                        closeBtn  : false,
                                        helpers : {
                                                title : {
                                                        type : 'inside'
                                                },
                                                buttons : {}
                                        },

                                        afterLoad : function() {
                                                this.title = 'Image ' + (this.index + 1) + ' of ' + this.group.length + (this.title ? ' - ' + this.title : '');
                                        }
                                });
                            });
                        </script>
            </body>
        </html>
        '''

        IconLocation="https://s3.amazonaws.com/MyImpData-DND/camera_folder_icon.png"
        bucket = 'dnd-sntkum-thmbnail'
        webbucket='gallery.sntkum.myinstance.com'
        ThumbSize='200x200'
        ODir = '/tmp'
        Directory = {}
        #Data = defaultdict(list) # Define a list of dictonary
        Data = nested_dict(2, list) # Difines a list of 2 dimentional dictonary
        LPUrls = list()

        s3bucket = s3.Bucket(bucket)
        objects = s3bucket.objects.all()

        for obj in objects:
            mykey = obj.key
            name = mykey.split('/')
            Data[name[-4]][name[-3]].append(mykey)
            #print(mykey)

        for DirName in Data:
            #print(DirName)
            OFileName = DirName + '.html'
            OFile = ODir + '/' + OFileName
            LPUrls.append(OFileName)
            ofhan = open(OFile, 'w')
            print(HtmlData1, file=ofhan)
            for Key, Values in Data[DirName].iteritems():
                print('<fieldset><legend>' + Key + '</legend>', file=ofhan)
                for value in Values:
                    if ThumbSize in str(value):
                        Vl=value.split('/')
                        idx = 0
                        uri = bucket
                        while (len(Vl) - idx > 4):
                            uri = uri + '/' + Vl[idx]
                            idx = idx + 1
                        TURL="https://s3.amazonaws.com/" + uri + "/" + Vl[-4] + "/" + Vl[-3] + "/" + ThumbSize + "/" + Vl[-1]
                        OURL="https://s3.amazonaws.com/" + uri + "/" + Vl[-4] + "/" + Vl[-3] + "/" + "Shrinked" + "/" + Vl[-1]
                        print('<li><a class="fancybox-buttons" rel="fancybox-button" href="' + OURL + '" title="' + Vl[-1] + '"><img src="' + TURL + '" width="100" height="100" alt="' + Vl[-3] + '"></a></li>', file=ofhan)
                        #print(value, TURL, OURL)
                print('</fieldset>', file=ofhan)
            print(HtmlData2, file=ofhan)
            ofhan.close()
            ststus = S3_Upload(OFile, webbucket, OFileName)
            if ststus == 0:
                print(OFile, " uploded to s3 successfully")
            else:
                print(OFile, " failed to uploded to s3")
            os.remove(OFile)

        LFile = ODir + '/LandingPage.html'
        lfhan = open(LFile, 'w')
        LPUrls.sort()
        print(html1, file=lfhan)
        for File in LPUrls:
            txt='<a href="' + File + '"><figure><img src="' + IconLocation + '" width="170px" height="135px" /><figcaption>' + File.replace('.html', '') + '</figcaption></figure></a>'
            print(txt, file=lfhan)
        print(html2, file=lfhan)
        lfhan.close()

        S3_Upload(LFile, webbucket, 'LandingPage.html')
        if ststus == 0:
            print(LFile, " uploded to s3 successfully")
        else:
            print(LFile, " failed to uploded to s3")
        os.remove(LFile)
        print("Cleanup Complete. Finished script execution successfully!!")
