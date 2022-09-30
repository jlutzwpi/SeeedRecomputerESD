#!/usr/bin/env python

import device_patches       # Device specific patches for Jetson Nano (needs to be before importing cv2)

import cv2
import os
import time
import sys, getopt
import numpy as np
from edge_impulse_linux.image import ImageImpulseRunner
import nanocamera as nano

runner = None
# if you don't want to see a video preview, set this to False
show_camera = True
#count the number of objects to avoid false detections
numWatch=0
numRing=0
numStrap=0
isFile = False

if (sys.platform == 'linux' and not os.environ.get('DISPLAY')):
    show_camera = False


def help():
    print('python3 ppe-classify.py [stream | rtsp | file_name]')


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "h", ["--help"])
    except getopt.GetoptError:
        help()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help()
            sys.exit()

    if len(args) != 1:
        help()
        sys.exit(2)

    # hard code the model name
    model = "jetson-recomputer-ppe-linux-aarch64-v3.eim"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    modelfile = os.path.join(dir_path, model)
    print('MODEL: ' + modelfile)
    print(cv2.__version__)

    #setup info to save file
    fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
    out = cv2.VideoWriter('output.avi', fourcc, 10, (270,  160), False)

    with ImageImpulseRunner(modelfile) as runner:
        try:
            model_info = runner.init()
            print('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
            labels = model_info['model_parameters']['labels']

            #parse through the command line input for the type of video
            #choices are rstp, streaming, or a file (file name provided)
            video_type = args[0]
            if video_type == 'rtsp':
                #start RTSP camera instance
                rtsp_location = "admin:Run4fun@192.168.86.39:554//h264Preview_01_main"
                vidcap = nano.Camera(camera_type=2, source=rtsp_location, width=1280, height=760, fps=30)
            elif video_type == 'stream':
                #start CSI camera instance using nanocamera            
                vidcap= nano.Camera(flip=0, width=1280, height=760, fps=30)
            else:
                print("*** File selected..." + video_type)
                vidcap = cv2.VideoCapture(video_type)
                print("isOpened" + str(vidcap.isOpened()))
                global isFile
                isFile = True

            sec = 0
            alertBuffer = 0
            start_time = time.time()

            def getFrame(sec):
                global isFile
                if isFile == True:
                    vidcap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
                    hasFrames,image = vidcap.read()
                    if hasFrames:
                        return image
                else:
                    image = vidcap.read()
                    return image


            img = getFrame(sec)

            while img.size != 0:

                # imread returns images in BGR format, so we need to convert to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # get_features_from_image also takes a crop direction arguments in case you don't have square images
                #features, cropped = runner.get_features_from_image(img)
                # make two cuts from the image, one on the left and one on the right
                features_l, cropped_l = runner.get_features_from_image(img, 'left')
                features_r, cropped_r = runner.get_features_from_image(img, 'right')

                # the image will be resized and cropped, save a copy of the picture here
                # so you can see what's being passed into the classifier
                #cv2.imwrite('debug.jpg', cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))

                #res = runner.classify(features)
                # classify both
                res_l = runner.classify(features_l)
                res_r = runner.classify(features_r)

                cv2.imwrite('debug_l.jpg', cv2.cvtColor(cropped_l, cv2.COLOR_RGB2BGR))
                cv2.imwrite('debug_r.jpg', cv2.cvtColor(cropped_r, cv2.COLOR_RGB2BGR))

                def classification(res, cropped):
                    if "classification" in res["result"].keys():
                        print('Result (%d ms.) ' % (res['timing']['dsp'] + res['timing']['classification']), end='')
                        for label in labels:
                            score = res['result']['classification'][label]
                            print('%s: %.2f\t' % (label, score), end='')
                        print('', flush=True)

                    elif "bounding_boxes" in res["result"].keys():
                        print('Found %d bounding boxes (%d ms.)' % (len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
                        for bb in res["result"]["bounding_boxes"]:
                            print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))
                            if bb['label'] == 'ring':
                                global numRing 
                                numRing+=1 
                            if bb['label'] == 'watch':
                                global numWatch 
                                numWatch+=1
                            elif bb['label'] == 'wrist-strap':
                                global numStrap
                                numStrap+=1
                            cropped = cv2.rectangle(cropped, (bb['x'], bb['y']), (bb['x'] + bb['width'], bb['y'] + bb['height']), (255, 0, 0), 1)
                            
                        
                classification(res_l, cropped_l)
                classification(res_r, cropped_r)
                #combine left and right into one image
                #since there is a little overlap, crop left image
                resized = cropped_l[0:160,0:110]
                combined = np.concatenate((resized, cropped_r), axis=1)
                #if a ring or watch is present, give a warning
                message = "ESD risk:"
                if numRing > 4:
                    message += " Ring detected!"
                if numWatch > 4:
                    message += " Watch detected!"
                if numRing > 4 or numWatch > 5:
                    combined = cv2.putText(combined, message, (5,10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,0,0),1)
                #if no ESD risk and wrist strap, then we are clear
                if numStrap > 4 and numRing <= 4 and numWatch <= 4:
                    message = "Wrist strap on. ESD safe!"
                    combined = cv2.putText(combined, message, (5,10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,0,0),1)
                if (show_camera):
                    cv2.imshow('PPE Test', cv2.cvtColor(combined, cv2.COLOR_RGB2BGR))
                    out.write(combined)
                    if cv2.waitKey(1) == ord('q'):
                        break

                sec = time.time() - start_time
                sec = round(sec, 2)
                print(sec)
                img = getFrame(sec)
                
        finally:
            if (runner):
                runner.stop()
            vidcap.release()
            out.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
   main(sys.argv[1:])
