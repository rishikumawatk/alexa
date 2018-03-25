#WallyFlow Mindfulness with Alexa and Walabot
#Written for Python 3.5.3
#Running on Rasbperry Pi 3 B With Walabot Developer

from imp import load_source
from os import system
import math
import time
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session

wlbt = load_source('WalabotAPI', '/usr/share/walabot/python/WalabotAPI.py')
wlbt.Init()

app = Flask(__name__)
ask = Ask(app, "/")

lastAveragePosition = 0
lastMoveTime = time.time()
minAverageDelta = 30
maxStillTime = 1 * 60

minInCm, maxInCm, resInCm = 50, 300, 3                          # Walabot_SetArenaR - input parameters   
minIndegrees, maxIndegrees, resIndegrees = -15, 15, 5           # Walabot_SetArenaTheta - input parameters
minPhiInDegrees, maxPhiInDegrees, resPhiInDegrees = -60, 60, 5  # Walabot_SetArenaPhi - input parameters

threshold = 4

    
def connect():
    while True:
        try:
            wlbt.ConnectAny()
        except wlbt.WalabotError as err:
            time.sleep(1)
        else:
            print("Walabot Connected")
            return
def configure():
    wlbt.SetProfile(wlbt.PROF_SENSOR)                                   # Set Profile - to Sensor
    wlbt.SetArenaR(minInCm, maxInCm, resInCm)                           # Setup arena - specify it by Cartesian coordinates.
    wlbt.SetArenaTheta(minIndegrees, maxIndegrees, resIndegrees)        # Sets polar range and resolution of arena (parameters in degrees).
    wlbt.SetArenaPhi(minPhiInDegrees, maxPhiInDegrees, resPhiInDegrees) # Sets azimuth range and resolution of arena.(parameters in degrees).
    wlbt.SetDynamicImageFilter(wlbt.FILTER_TYPE_MTI)                    # Dynamic-imaging filter for moving target identification
    print("Walabot Configured")

def calibrate():
    wlbt.Start()
    wlbt.StartCalibration()
    print("Calibrating Walabot...")
    while wlbt.GetStatus()[0] == wlbt.STATUS_CALIBRATING:
        wlbt.Trigger()
    print("Walabot Ready")

def disconnect():
    wlbt.Stop()
    wlbt.Disconnect()
    print("Walabot Disconnected")

def getTargets():
    wlbt.Trigger()
    targets = wlbt.GetSensorTargets()
    return targets

def getTargetPosition():
    wlbt.Trigger()
    targets = wlbt.GetSensorTargets()
    if targets:
        target = targets[0]
        return (target.xPosCm, target.yPosCm, target.zPosCm, target.amplitude)
    else:
        return (0,0,0,0)
    
def PrintSensorTargets(targets):
    system('clear')
    if targets:
        for i, target in enumerate(targets):
            print('Target #{}:\nx: {}\ny: {}\nz: {}\namplitude: {}\n'.format(
                i+1,target.xPosCm, target.yPosCm, target.zPosCm, target.amplitude))

def readSensor():
    wlbt.Trigger()
    targets = wlbt.GetSensorTargets()
    PrintSensorTargets(targets)
    
def mindful():
    global lastAveragePosition, lastMoveTime, t_end

    #Get Targets from Walabot
    targets = getTargets()
    average = 0
    count = len(targets)
    
    for target in targets:
        angle = math.degrees(math.atan(target.yPosCm/target.zPosCm)) 
        average += abs(angle)
        
    if count != 0:
        average /= count
        delta = abs(average - lastAveragePosition)

        if delta >=  minAverageDelta:
            #print("Average: " + str(average) + " Delta: " + str(delta)+"\n")
            lastMoveTime = time.time()
            t_end = lastMoveTime + maxStillTime
            lastAveragePosition = average
            #print('LAP: ' + str(lastAveragePosition))

@app.route('/')
def homepage():
    return render_template('home')

@ask.launch
def startSkill():
    return question(render_template('welcome')) \
           .reprompt(render_template('reprompt'))

@ask.intent("YesIntent", convert={'minutes':int})
def yesIntent():
    return question(render_template('yesA', minutes = maxStillTime))

@ask.intent("MovedIntent")
def setTime(minutes):
    global lastMoveTime
    stillTime = round((time.time()-lastMoveTime) / 60)
    return statement(render_template('time', time = stillTime))
 
@ask.intent("NoIntent")
def noIntent():
    return statement(render_template('bye'))


"""
def wallyFlow():
    wlbt.Init()
    connect()
    
    calibrate()
    t_end = time.time() + maximumStillTime
    start_msg = "Starting Wally Flow. Be Mindful!"
    statement(start_msg)
    try:
        while True:
            mindful()
            if time.time() > t_end:
                move_msg = "Time to move"
                return statement(move_msg)
    except KeyboardInterrupt:
        disconnect()
"""
if __name__ == '__main__':     
    app.run(debug = True)


