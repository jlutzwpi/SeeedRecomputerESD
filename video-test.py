#!/usr/bin/python3

#import jetson.utils
#import sys
#import time
#from datetime import datetime

#input = jetson.utils.videoSource("rtsp://admin:Run4fun@192.168.86.39:554/h264Preview_01_main",['--input-height=1080', '--input-width=1920'])
#output = jetson.utils.videoOutput("",['--input-height=1080', '--input-width=1920'])

# process frames until the user exits

#while True:
	# capture the next image
#	try:
#		img = input.Capture()
#	except:
#		print("\n*** Image could not be captured.  Wifi interruption maybe? ***\n\n")
#	else:
#		# render the image
#		output.Render(img)
		# update the title bar
		# exit on input/output EOS
#		if not input.IsStreaming() or not output.IsStreaming():
#			break


import jetson.utils
import time

camera = jetson.utils.videoSource("csi://0")

while True:
	img = camera.Capture()
	video = jetson.utils.videoOutput(f"ppe-{time.time()}.mp4")
	start = time.time()
	frame = img
	# Record video for 30 seconds
	while time.time() < start + 30:
		video.Render(frame)
		frame = camera.Capture()
	break


