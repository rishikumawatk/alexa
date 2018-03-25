#Take a Break with Walabot
#Written for Python 3.5.3
#Running on Raspberry Pi 3 B with Walabot Maker

from imp import load_source
from os import system
from flask import Flask, request
import math
import time
import RPi.GPIO as GPIO
import sys
import json
import socket

SERVER_ADDRESS = socket.gethostbyname('localhost')
SERVER_PORT = 9999

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.OUT)
GPIO.output(4,0)
GPIO.setwarnings(False)

wlbt = load_source('WalabotAPI', '/usr/share/walabot/python/WalabotAPI.py')
wlbt.Init()

#Input Parameters for Walabot_SetArenaR, Cartesian Coordinates
minInCm, maxInCm, resInCm = 50, 300, 3

#Input Parameters for Walabot_SetArenaTheta, Degrees
minInDeg, maxInDeg, resInDeg = -15, 15, 5

#Input Parameters Walabot_SetArenaPhi, Degrees
minPhiInDeg, maxPhiInDeg, resPhiInDeg = -60, 60, 5

#Set Walabot Threshold
threshold = 2

#Set Take A Break Parameters
lastAvgPos = 0
minAvgDelta = 40
maxStillTime = 1*10 #in seconds
lastTimeMoved = time.time()
#app = Flask(__name__)

#Walabot Connection Function
def connect():
    print("Connecting Walabot...")
    wlbt.Init()
    print("Initializing Walabot...")
    while True:
        try:
            wlbt.ConnectAny()
        except wlbt.WalabotError as err:
            print("Connecting...")
            time.sleep(1)
        else:
            print("Walabot Connected")
            return

#Walabot Startup Function
def startUp():
    print("Configuring Walabot...")
    #Set Profile to Senson
    wlbt.SetProfile(wlbt.PROF_SENSOR)

    #Setup Arena
    wlbt.SetArenaR(minInCm, maxInCm, resInCm)

    #Set Arena Polar Range and Resolution
    wlbt.SetArenaTheta(minInDeg, maxInDeg, resInDeg)

    #Set Arena Azimuth Range and Resolution
    wlbt.SetArenaPhi(minPhiInDeg, maxPhiInDeg, resPhiInDeg)

    #Set Dynamic Imaging Filter to Moving Target Identification
    wlbt.SetDynamicImageFilter(wlbt.FILTER_TYPE_MTI)
    print("Walabot Configured")
    print("Calibrating... Walabot")
    wlbt.Start()
    wlbt.StartCalibration()
    while wlbt.GetStatus()[0] == wlbt.STATUS_CALIBRATING:
        wlbt.Trigger()
    print("Walabot Calibrated and Ready")

#Walabot Disconnect Function
def disconnect():
    wlbt.Stop()
    wlbt.Disconnect()
    print("Walabot Disconnected")

#Walabot Get Targets Function
def getTargets():
    wlbt.Trigger()
    targets = wlbt.GetSensorTargets()
    return targets

#Walabot Target Positions
def getTargetPositions():
    wlbt.Trigger()
    targets = wlbt.GetSensorTargets()
    if targets:
        target = targets[0]
        print(target.xPosCm, target.yPosCm, target.zPosCm, target.amplitude)
    else:
        print (0,0,0,0)

#Last Time Moved Function
def ltm():
    global lastAvgPos, t_end, lastTimeMoved

    #Get Targets from Walabot
    targets = getTargets()
    avg = 0
    count = len(targets)

    for target in targets:
        angle = math.degrees(math.atan(target.yPosCm/target.zPosCm))
        avg += abs(angle)

    if count != 0:
        #getTargetPositions()
        avg /= count
        delta = abs(avg - lastAvgPos)

        if delta >= minAvgDelta:
            #print("Delta: {}".format(delta))
            lastTimeMoved = time.time()
            t_end = lastTimeMoved + maxStillTime
            cleanT_End = time.strftime("%H:%M",time.localtime(t_end))
            cleanLastTimeMoved =  time.strftime("%H:%M",time.localtime(lastTimeMoved))
            #print("T_End: {} LastTimeMoved: {}".format(cleanT_End, cleanLastTimeMoved))
            lastAvgPos = avg
    return lastTimeMoved

#@app.route('/', methods = ['POST', 'GET'])
#def homepage():
#if __name__ == '__main__':
def takeABreak():
    print("Starting 'Take a Break with Walabot'.")

    #var = input("Please set maximum still time in minutes: ")
    #print("Your maximum still time is set to {} minutes".format(var))
    #time.sleep(1)
    #maxStillTime = float(var) * 60
    connect()
    startUp()
    try:
        client_socket = socket.socket()
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        client_socket.bind((SERVER_ADDRESS, SERVER_PORT))
        client_socket.connect((SERVER_ADDRESS, SERVER_PORT))

        lastTimeMoved = time.time()
        t_end = lastTimeMoved + maxStillTime
        while True:
            prevLastTimeMoved = lastTimeMoved
            lastTimeMoved = ltm()
            t_end = lastTimeMoved + maxStillTime
            t_now = time.time()
            if t_now > t_end:
                GPIO.output(4, 1)
                time.sleep(1)
                GPIO.output(4,0)
                client_socket.sendall(json.dumps({"last_time_moved":
                                               lastTimeMoved}).encode('UTF-8'))
            else:
                GPIO.output(4,0)
    except socket.error:
        print("Server is currently unavailable")
    except KeyboardInterrupt:
        pass
    finally:
        disconnect()

if __name__ == '__main__':
    takeABreak()    
