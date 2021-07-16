import numpy
#import cv2
from PIL import Image
import time

# NOTE: For this code to work the camera backpack must be enabled
#       and the simulator must be running on the same computer

from micromelon import *
rc = RoverController()
# Connect to simulator
rc.connectIP('127.0.0.1', 9000)

rc.startRover()

# Time the image capture
print('Capture started')
startTime = time.time()
MAX_COUNT = 1
for i in range(MAX_COUNT):
  image = Robot.getImageCapture(640, 480)

totalTime = time.time() - startTime
print('Time per capture: ', totalTime / MAX_COUNT)
print('Image capture complete')

image = image.astype(numpy.uint8)
print('Showing image')

# Pillow (PIL) version
im = Image.fromarray(image)
im.show()

# OpenCV version
#im = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
#cv2.imshow('image', im)
#cv2.waitKey(0)

rc.stopRover()
rc.end()
