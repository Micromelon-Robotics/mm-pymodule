from micromelon import *

rc = RoverController()
rc.connectIP("127.0.0.1", 9000)

rc.startRover()

Motors.write(20)
while True:
    u = Ultrasonic.read()
    print(u)
    if u < 20:
        break

rc.stopRover()
rc.end()
