#!/usr/bin/env python3

import alsaaudio
import time, json
import RPi.GPIO as GPIO
import subprocess as sub
import json, logging, time
from Adafruit_LED_Backpack import SevenSegment
from datetime import datetime as dt
from playsong import play
from w1thermsensor import W1ThermSensor # GPIO22 set in boot/config.txt
import requests
from threading import Thread

'''
 https://github.com/adafruit/Adafruit_Python_LED_Backpack
 https://github.com/adafruit/Adafruit_Python_LED_Backpack/blob/master/Adafruit_LED_Backpack/SevenSegment.py
 http://openweathermap.org
'''

#--- runs as a service ---
#12-apr-2019
#26-apr-2019 added dbay msg
#14-aug-2022 updated ver.
#19-aug-2022 combined iClock and main.
#12-jan-2023 installed sensors
#16-jan-2023 added external temperature reading

logging.basicConfig(filename='/home/pi/clock/mylogs.log',level=logging.INFO)
playfile = 'python3 /home/pi/clock/playsong.py '
diag_sound_file = 'python3 /home/pi/clock/soundDiag.py'
diag_display_file = 'python3 /home/pi/clock/displayDiag.py '
fname = '/home/pi/clock/data/settings.json'
api_key = '9da08d160fc04c96093847f5fa6941a3'
base_url = 'http://api.openweathermap.org/data/2.5/weather?'
country = 'US'
city = 'Los Angeles'

# init gpio pin
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
button = 23
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
pir = 17
GPIO.setup(pir, GPIO.IN)
photores = 27
GPIO.setup(photores, GPIO.IN)

# init display. Must be called once before using the display.
seg = SevenSegment.SevenSegment(address=0x70)
seg.begin()

#content: space h a p p y space b i r t h d a y
arry = [0x00, 0x76, 0x77, 0x73, 0x73, 0x6E,
        0x00, 0x7c, 0x10, 0x50, 0x78, 0x76, 0x5E, 0x77, 0x6E,
        0x00, 0x00, 0x00]
#       0x00, 0x5E, 0x77, 0x54, 0x10, 0x00, 0x00, 0x00]

#in hex
largeH = 0x76 # H
largeO = 0x3F # O
largeL = 0x38 # L
largeA = 0x77 # A
smallD = 0x5E # d
smallN = 0x54 # n
smallI = 0x10 # i
largeP = 0x73 # P
largeB = 0x7C # B
largeY = 0x6E # Y
largeC = 0x39 # C
largeF = 0x71 # F
colon = 0x02  # time colon
ADot = 0x08   # alarm set dot
degree = 0x63 # º

#set variables
alarmON = 1
bhour = 8
bmin = 0
Dbday = 29
Dbmon = 4
Mbday = 29
Mbmon = 12
hour = 7
minutes = 0
we = 0
rdm = 1
loops = 1
vol = 100
diag_sound = 0
diag_display = 0
brightness = 10
brightness2 = 1
pause = 0     #used to stop clock
bday = 0      #used to display msg
now = 0       #actual time
cnt = 0       #push button pulse counter
oldtime = 0   #used to reset counter
now = dt.now() # get time

m = alsaaudio.Mixer()
darkness = False
temp_sensor = W1ThermSensor()
int_temperature = 0
temp_adj = 1
temp_mode = 1
pir_state = False
ext_temperature = 0

def msg():
    ''' displays HOLA dANI'''
    seg.clear()
    seg.set_brightness(brightness)
    seg.set_digit_raw(0, largeH)
    seg.set_digit_raw(1, largeO)
    seg.set_digit_raw(2, largeL) # 2 is colon
    seg.set_digit_raw(3, largeA)

    # This must be called to update the actual display LEDs.
    seg.write_display()
    time.sleep(2)  # enjoy seeing my work
    seg.clear()
    seg.set_digit_raw(0, smallD)
    seg.set_digit_raw(1, largeA)
    seg.set_digit_raw(2, smallN)
    seg.set_digit_raw(3, smallI)

    # This must be called to update the actual display LEDs.
    seg.write_display()
    time.sleep(2)  # enjoy seeing my work
    seg.clear()


def scroll_msg():
    ''' displays happy birthday from array'''

    seg.clear()
    for t in range(len(arry)):
      seg.set_digit_raw(3, arry[t])
      seg.set_digit_raw(2, arry[t-1])
      seg.set_digit_raw(1, arry[t-2])
      seg.set_digit_raw(0, arry[t-3])
      seg.write_display()
      time.sleep(.5)


def get_temps():
    global ext_temperature, int_temperature
    # https://api.openweathermap.org/data/2.5/weather?q={city name},{country code}&appid={API key}
    while True:
       try:
           url = base_url + 'q=' + city + '&' + country + '&appid=' + api_key
           response = requests.get(url)
           x= response.json()
           if x['cod'] != '404':
              y = x['main']
              ext_temperature = round((y['temp'] - 273.15))

           int_temperature = int(temp_sensor.get_temperature()) - temp_adj
           if not temp_mode:
              # return temp in Fº
              int_temperature = int(int_temperature * 9.0 / 5.0 + 32.0)
              ext_temperature = int(ext_temperature * 9.0 / 5.0 + 32.0)
           time.sleep(60)
       except Exception as err:
           print('Get temps error',err)
           time.sleep(1)
           pass


try:
    t1 = Thread(target=get_temps)
    t1.start()
except Exception as err:
    print('Thread error', err)
    pass


def read_sensors():
    global darkness, pir_state
    #seg.set_left_colon(True)
    #seg.write_display()
    try:
        i = GPIO.input(pir)
        time.sleep(0.1)
        if i == 0:
           pir_state = False
        else:
           pir_state = True
        # ##
        ph = GPIO.input(photores)
        time.sleep(0.1)
        if ph == 1:
           darkness = False
        elif ph == 0:
           darkness = True
        # print(temperature, pir_state, darkness)

    except Exception as err:
       print("error in sensors", err)
       pass


def check_brightness():
    if now.hour > 22 or now.hour < 7:
         seg.set_brightness(brightness2)
    else:
         seg.set_brightness(brightness)
    if pir_state and darkness:
         seg.set_brightness(brightness)


def clock():
    ''' Show time on the 7 segment LED display '''
    global now

    if(pause == False):
      #get the current date and time
      now = dt.now()
      hour = now.hour
      minute = now.minute
      second = now.second
      elapsedTime = 1 #seconds

      seg.clear()
#      check_brightness()
      if now.hour > 22 or now.hour < 7:
         seg.set_brightness(brightness2)
      else:
         seg.set_brightness(brightness)
      if pir_state and darkness:
         seg.set_brightness(brightness)


      '''Set brightness to specified value
      16 levels, from 0 to 15)'''

      # Show hours
      seg.set_digit(0, int(hour / 10))     # Tens
      seg.set_digit(1, hour % 10)          # Ones

      # Show minutes
      seg.set_digit(2, int(minute / 10))   # Tens
      seg.set_digit(3, minute % 10)        # Ones

      # Toggle colon at 1 Hz
      seg.set_colon(second % 2)

      if(alarmON):
          # To turn on the left side colon:
          #display.set_left_colon(True)
          # To turn off the left side colon:
          #display.set_left_colon(False)
          # To turn on the fixed decimal point (in upper right in normal orientation):
          seg.set_fixed_decimal(True)
      else:
          # To turn off the fixed decimal point:
          seg.set_fixed_decimal(False)

          # This must be called to update the actual display LEDs.
      seg.write_display()
          #cpu taking a breath


def read_file():
    global alarmON, pause, hour, minutes,\
           we,rdm,loops,vol,brightness,brithness2, bday,\
           diag_sound,diag_display,temp_mode,city

    with open(fname) as json_file:
        data = json.load(json_file)
        rdm = int(data[0]['random'])
        loops = int(data[0]['loops'])
        vol = int(data[0]['volume'])
        brightness = int(data[0]['brightness'])
        brightness2 = int(data[0]['brightness2'])
        pause = int(data[0]['pause'])
        hour = int(data[1]['hour'])
        minutes = int(data[1]['minutes'])
        alarmON = int(data[1]['alarmON'])
        we = int(data[1]['weekend'])
        diag_sound = int(data[3]['sound'])
        diag_display = int(data[3]['display'])
        temp_mode = int(data[3]['temp_mode'])
        if temp_mode > 1:
           temp_mode = 1
        city = data[3]['city']
    #let's limit it to max 15
    if(brightness > 15):
      brightness = 15
    if brightness2 > 15:
       brightness2 = 0


def write_file(x):
    with open(fname, "r+") as jsonFile:
        data = json.load(jsonFile)

        tmp = data[0]
        data[0]['pause'] = x
        data[0]['bday'] = x

        jsonFile.seek(0)  # rewind
        json.dump(data, jsonFile)
        jsonFile.truncate()


def checkPB():
    global cnt, oldtime
    if not GPIO.input(button):     # if port 23 == 1
      #reset counter if passed a minute
      m.setvolume(80)
      if(now.minute > oldtime): cnt = 0
      cnt += 1
      oldtime = now.minute
      #beep(5, 440, 960)
      if(cnt == 1):
        time.sleep(.25)
        sub.call(['espeak "one" 2>/dev/null'], shell=True)
      elif(cnt == 2):
        time.sleep(.25)
        sub.call(['espeak "two" 2>/dev/null'], shell=True)
      elif(cnt == 3):
        time.sleep(.25)
        sub.call(['espeak "tree" 2>/dev/null'], shell=True)
      elif(cnt == 4):
        time.sleep(.25)
        sub.call(['espeak "four" 2>/dev/null'], shell=True)
      elif(cnt == 5):
        time.sleep(1)
        sub.call(['espeak "good  bye" 2>/dev/null'], shell=True)
        cmd = "/usr/bin/sudo /sbin/shutdown -h now"
        process = sub.Popen(cmd.split(), stdout=sub.PIPE)
        output = process.communicate()[0]


def check_alarm():
    global oldtime
    #update variable now with current time
    now = dt.now()
    #match weekday time
    weekday = now.weekday()     #Monday is 0 and Sunday is 6
    newtime = now.minute #used as a timer of one minute

    if(alarmON == 1 and we == 0 and (weekday >= 0 and weekday < 5)):
        if now.hour == hour and newtime == minutes and not (oldtime == newtime):
           #print beep.main() #beeps for x seconds set in module beep.py
           playAlarm()

    if(alarmON == 1 and we == 1 and (weekday >= 5 and weekday < 7)):
        if now.hour == hour and newtime == minutes and not (oldtime == newtime):
           #print beep.main() #beeps for x seconds set in module beep.py
           playAlarm()
    oldtime = newtime


def check_bdays():
    #get current time
    now = dt.today()
    currdate = dt(now.year, now.month, now.day)
    Dbdate = dt(now.year, Dbmon, Dbday) #4-29 Dani's birthday
    Mbdate = dt(now.year, Mbmon, Mbday) #12-29 Miao's birthday
    bh = bhour                    #morning time
    bm = bmin
    #for debug():

    #check if it's today
    if((currdate == Dbdate or currdate == Mbdate) and now.hour == bh and now.minute == bm):
      #block display and show msg
      write_file(1)
      playBday()
      #reset display to show time
      write_file(0)


def playAlarm():
    import os
    #send variables to script
    var = ''.join([str(rdm), ' ', str(vol), ' ', str(loops), ' ', '0'])
    #execute file
    os.system(playfile + var)


def playBday():
    import os
    #send variables to script
    var = ''.join([str(rdm), ' ', str(vol), ' ', str(loops), ' ', '1'])
    #play song
    os.system(playfile + var)
    time.sleep(1.5)


def diags():
    import os

    if diag_sound:
      os.system(diag_sound_file)
    elif diag_display:
      #block display and show msg
      write_file(1)
      os.system(diag_display_file)
      #reset display to show time
      write_file(0)
    else:
      pass


oldepoch = 0
def main():
    global pause,oldepoch
    read_file()
    check_alarm()
    check_bdays()
    clock()
    read_sensors()
    if time.time() - oldepoch >= 60:
       oldepoch = time.time()
       seg.clear()
       #seg.set_left_colon(True)
       seg.set_digit(0,int(int_temperature / 10))
       seg.set_digit(1,int_temperature % 10)
       seg.set_digit_raw(2, degree)
       if temp_mode == 1:
          seg.set_digit_raw(3, largeC)
       else:
         seg.set_digit_raw(3, largeF)
       seg.write_display()
       time.sleep(2)
       seg.clear()
       seg.set_digit(0,int(ext_temperature / 10))
       seg.set_digit(1,ext_temperature % 10)
       seg.set_digit_raw(2, degree)
       if temp_mode == 1:
          seg.set_digit_raw(3, largeC)
       else:
          seg.set_digit_raw(3, largeF)
       seg.write_display()
       time.sleep(2)

    checkPB()
    diags()
    if(bday == True and pause == True):
      scroll_msg()


if __name__ == '__main__':
    #one time run
    msg()

    #loop
    while True:
        main()
        time.sleep(0.3)
