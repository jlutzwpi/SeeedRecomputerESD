# SeeedRecomputerESD

Classify potential ESD risks in a video (either live stream via CSI camera or RSTP, or an archived video).

To run: python3 model_name.eim [stream | rstp | video]

Support files:
video_test.py: generates the video files to use as input to Edge Impulse.  Can be either through RTSP or the CSI camera.  Once the video is created, use extract_frames.py to create images (ie every 1 second)
csi-camera-test.py: tests to make sure the camera is working
extract_frames.py: I took this from the Advantech Edge Impulse workshop.  Very help utility to split a video into images.
