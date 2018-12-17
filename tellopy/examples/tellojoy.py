"""
tellopy sample using joystick and video palyer

 - you can use PS3/PS4/XONE joystick to controll DJI Tello with tellopy module
 - you must install mplayer to replay the video
 - Xbox One Controllers were only tested on Mac OS with the 360Controller Driver.
    get it here -> https://github.com/360Controller/360Controller'''
"""

import time
import sys
import platform as ptf
import tellopy
import pygame
import pygame.locals
from subprocess import Popen, PIPE


class JoystickPS4_MAC:
    # d-pad
    UP = 1  # UP
    DOWN = -1  # DOWN
    ROTATE_LEFT = -10  # LEFT
    ROTATE_RIGHT = 10  # RIGHT

    # buttons
    LEFT = 0  # SQUARE
    BACKWARD = 1  # CROSS
    RIGHT = 2  # CIRCLE
    FORWARD = 3  # TRIANGLE
    TAKEOFF = 4  # L1
    LAND = 5  # R1
    # UNUSED = 6 #L2
    # UNUSED = 7 #R2
    RECORD = 8  # SHARE
    TAKE_PICTURE = 9  # OPTIONS
    # UNUSED = 10 #LEFT STICK
    # UNUSED = 11 #RIGHT STICK
    FN = 12  # PS
    # UNUSED = 13  # TOUCHPAD

    # axis
    LEFT_X = 0  # LEFT STICK X
    LEFT_Y = 1  # LEFT STICK X
    RIGHT_X = 2  # RIGHT STICK X
    RIGHT_Y = 3  # RIGHT STICK Y
    SPEED_UP = 4  # L2
    SPEED_DOWN = 5  # R2

    # axis value
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0

    # others
    NO_INPUT = 0
    ORI_VALUE = 0.0
    DEADZONE = 0.1
    IF_FN = 0
    IF_PRESSED = 0


class JoystickPS4_Linux:
    # d-pad
    UP = 1  # UP
    DOWN = -1  # DOWN
    ROTATE_LEFT = -10  # LEFT
    ROTATE_RIGHT = 10  # RIGHT

    # buttons
    LEFT = 3  # SQUARE
    BACKWARD = 0  # CROSS
    RIGHT = 1  # CIRCLE
    FORWARD = 2  # TRIANGLE
    TAKEOFF = 4  # L1
    LAND = 5  # R1
    # UNUSED = 6 #L2
    # UNUSED = 7 #R2
    RECORD = 8  # SHARE
    TAKE_PICTURE = 9  # OPTIONS
    # UNUSED = 11 #LEFT STICK
    # UNUSED = 12 #RIGHT STICK
    FN = 10  # PS
    # UNUSED = 13  # TOUCHPAD

    # axis
    LEFT_X = 0  # LEFT STICK X
    LEFT_Y = 1  # LEFT STICK X
    RIGHT_X = 3  # RIGHT STICK X
    RIGHT_Y = 4  # RIGHT STICK Y
    SPEED_UP = 2  # L2
    SPEED_DOWN = 5  # R2

    # axis value
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0

    # others
    NO_INPUT = 0
    ORI_VALUE = 0.0
    DEADZONE = 0.1
    IF_FN = 0
    IF_PRESSED = 0


prev_flight_data = None
video_player = None
buttons = None
log = tellopy._internal.logger.Logger('Tello')
ori_speed = 30
max_speed = 100
speed_scale = max_speed - ori_speed
speed = ori_speed
throttle = 0.0
yaw = 0.0
pitch = 0.0
roll = 0.0


def handler(event, sender, data, **args):
    global prev_flight_data
    global video_player
    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        if prev_flight_data != str(data):
            print(data)
            prev_flight_data = str(data)
    elif event is drone.EVENT_VIDEO_FRAME:
        if video_player is None:
            video_player = Popen(['mplayer', '-fps', '35', '-'], stdin=PIPE)
        try:
            video_player.stdin.write(data)
        except IOError as err:
            print(err)
            video_player = None
    else:
        print('event="%s" data=%s' % (event.getname(), str(data)))


def update(old, new, max_delta=0.3):
    if abs(old - new) <= max_delta:
        res = new
    else:
        res = 0.0
    return res


def handle_input_event(drone, e):
    global speed
    global ori_speed
    global throttle
    global yaw
    global pitch
    global roll

    if e.type == pygame.locals.JOYAXISMOTION:
        # ignore small input values (Deadzone)
        if -buttons.DEADZONE <= e.value <= buttons.DEADZONE:
            e.value = buttons.ORI_VALUE
        if e.axis == buttons.SPEED_UP:
            speedvalue = (e.value + 1) / 2 * speed_scale + ori_speed
            if speed < speedvalue:
                speed = speedvalue
                speed = round(speed)
                if speed > 100:
                    speed = 100
                log.info("speed up to %d" % (speed))
        elif e.axis == buttons.SPEED_DOWN:
            speedvalue = max_speed - (e.value + 1) / 2 * speed_scale
            if speed > speedvalue:
                speed = speedvalue
                speed = round(speed)
                if speed > 100:
                    speed = 100
                log.info("speed down to %d" % (speed))
        elif buttons.IF_PRESSED == 0:
            if e.axis == buttons.LEFT_Y:
                throttle = update(throttle, e.value * buttons.LEFT_Y_REVERSE)
                drone.set_throttle(throttle)
            elif e.axis == buttons.LEFT_X:
                yaw = update(yaw, e.value * buttons.LEFT_X_REVERSE)
                drone.set_yaw(yaw)
            elif e.axis == buttons.RIGHT_Y:
                pitch = update(pitch, e.value * buttons.RIGHT_Y_REVERSE)
                drone.set_pitch(pitch)
            elif e.axis == buttons.RIGHT_X:
                roll = update(roll, e.value * buttons.RIGHT_X_REVERSE)
                drone.set_roll(roll)
    elif e.type == pygame.locals.JOYHATMOTION:
        buttons.IF_PRESSED = 1
        hatvalue = e.value[0] * 10 + e.value[1]
        if hatvalue == buttons.ROTATE_LEFT:
            drone.counter_clockwise(speed)
        if hatvalue == buttons.ROTATE_RIGHT:
            drone.clockwise(speed)
        if hatvalue == buttons.UP:
            drone.up(speed)
        if hatvalue == buttons.DOWN:
            drone.down(speed)
        if hatvalue == buttons.NO_INPUT:
            drone.clockwise(buttons.ORI_VALUE)
            drone.up(buttons.ORI_VALUE)
            buttons.IF_PRESSED = 0
    elif e.type == pygame.locals.JOYBUTTONDOWN:
        buttons.IF_PRESSED = 1
        if e.button == buttons.LAND:
            if buttons.IF_FN == 1:
                drone.palm_land()
            else:
                drone.land()
        elif e.button == buttons.FN:
            buttons.IF_FN = 1
        elif e.button == buttons.FORWARD:
            if buttons.IF_FN == 1:
                drone.flip_forward()
            else:
                drone.forward(speed)
                buttons.IF_FORWARD = 1
        elif e.button == buttons.BACKWARD:
            if buttons.IF_FN == 1:
                drone.flip_back()
            else:
                drone.backward(speed)
        elif e.button == buttons.RIGHT:
            if buttons.IF_FN == 1:
                drone.flip_right()
            else:
                drone.right(speed)
        elif e.button == buttons.LEFT:
            if buttons.IF_FN == 1:
                drone.flip_left()
            else:
                drone.left(speed)
    elif e.type == pygame.locals.JOYBUTTONUP:
        buttons.IF_PRESSED = 0
        if e.button == buttons.TAKEOFF:
            if throttle != buttons.ORI_VALUE:
                print('###')
                print('### throttle != 0.0 (This may hinder the drone from taking off)')
                print('###')
            drone.takeoff()
        elif e.button == buttons.FN:
            buttons.IF_FN = 0
        elif e.button == buttons.FORWARD:
            drone.forward(buttons.ORI_VALUE)
        elif e.button == buttons.BACKWARD:
            drone.backward(buttons.ORI_VALUE)
        elif e.button == buttons.RIGHT:
            drone.right(buttons.ORI_VALUE)
        elif e.button == buttons.LEFT:
            drone.left(buttons.ORI_VALUE)


def main():
    global buttons
    pygame.init()
    pygame.joystick.init()

    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        js_name = js.get_name()
        print('Joystick name: ' + js_name)
        print('Platform system: ' + ptf.system())
        if 'Darwin' in ptf.system():
            buttons = JoystickPS4_MAC
        else:
            buttons = JoystickPS4_Linux
    except pygame.error:
        pass

    drone = tellopy.Tello()
    drone.connect()
    drone.start_video()
    drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
    drone.subscribe(drone.EVENT_VIDEO_FRAME, handler)

    try:
        while 1:
            # loop with pygame.event.get() is too much tight w/o some sleep
            time.sleep(0.01)
            for e in pygame.event.get():
                handle_input_event(drone, e)
    except KeyboardInterrupt as e:
        print(e)
    except Exception as e:
        print(e)

    drone.quit()
    exit(1)


if __name__ == '__main__':
    main()
