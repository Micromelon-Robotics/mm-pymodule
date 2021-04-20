import sys
import re
from micromelon import *

rc = RoverController()

if len(sys.argv) != 2 or not re.search("^\d{1,4}$", sys.argv[1]):
  print("USAGE: python3 ble_rainbow.py botID")
  print("\tbotID argument required")
  print("\tbotID must be a 1-4 digit number")
  rc.end()

rc.connectBLE(sys.argv[1])
rc.startRover()

print("Rainbow")
for i in range(0, 360, 5):
  LEDs.writeAll(Colour.hue(i))
print("Square")
for i in range(4):
  Motors.moveDistance(20)
  Motors.turnDegrees(90)
print("Done")


rc.stopRover()
rc.end()
