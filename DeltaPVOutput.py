#A simple script to read values from a delta inverter and post them to 
#PVoutput.org

import time, subprocess, serial, traceback
from deltaInv import DeltaInverter
from time import localtime, strftime
import commands
import os

#PVOutput.org API Values - UPDATE THESE TO YOURS!
from pvoutputid import *
# pvoutputid.py should contain the following two lines
#SYSTEMID="YOUR_PVOUPUT_ID"
#APIKEY="YOUR_PVOUTPUT_API_KEY"

if __name__ == '__main__':

    #Edit your serial connection as required!!
    connection = serial.Serial('/dev/ttyUSB0',19200,timeout=0.4);
     
    logTime = strftime('%Y%m%d-%H:%M')
    logDate = strftime('%Y%m%d')
    logFile = "./log/solar.log.%s" % strftime('%Y%m%d')
    logFileError = "./log/solarerror.log.%s" % strftime('%Y%m%d')
    t_date = 'd={0}'.format(strftime('%Y%m%d'))
    t_time = 't={0}'.format(strftime('%H:%M'))

    timeUpdateDone = False # Becomes True if the time update gets done

    inv1 = DeltaInverter(1) #init Inverter 1
    #Get the Daily Energy thus far
    
    data = {}
    cmds = ['DC Cur1', 'DC Volts1', 'DC Pwr1', 'DC Cur2', 'DC Volts2', 'DC Pwr2', 'AC Current', 'AC Volts', 'AC Power', 'AC I Avg', 'AC V Avg', 'AC P Avg', 'Day Wh', 'Uptime', 'AC Temp', 'DC Temp']
    success = True
    for string in cmds:
        cmd = inv1.getCmdStringFor(string)
        connection.write(cmd)
        response = connection.read(100)
        if not response:
            # Change this to use the new log files above
            print "No response from inverter - shutdown? No Data sent to PVOutput.org"
            success = False # if any one of the readings fails it's not a success. 
            break
        else :
            value = inv1.getValueFromResponse(response)
            data[string.replace(" ", "_")] = "{0}".format(value)
            
            # if the day's file doesn't yet exist and the time update hasn't been done
            # set the inverter's system time - it seems to messed up sometimes making bogus daily energy totals
            if (not timeUpdateDone) and (not os.path.isfile(logFile)):
                cmdSetDate,cmdSetTime = inv1.getCmdsSetClock()
                connection.write(cmdSetDate)
                response = connection.read(100)
                connection.write(cmdSetTime)
                response = connection.read(100)
                timeUpdateDone = True
                
    if success :		
        t_energy = 'v1={0}'.format(data['Day_Wh'])
        t_power = 'v2={0}'.format(data['AC_Power'])
        t_volts = 'v6={0}'.format(data['AC_Volts'])
        t_temp = 'v5={0}'.format(data['DC_Temp'])
    #Send it all off to PVOutput.org
        cmd = ['/usr/bin/curl',
            '-d', t_date,
            '-d', t_time,
            '-d', t_energy,
            '-d', t_power, 
            '-d', t_volts,
            '-d', t_temp,
            '-H', 'X-Pvoutput-Apikey: ' + APIKEY, 
            '-H', 'X-Pvoutput-SystemId: ' + SYSTEMID, 
            'http://pvoutput.org/service/r1/addstatus.jsp']
        try:
            pass
            ret = subprocess.call (cmd)
        except:
            traceback.print_exc()
            print "Failed to send:", cmd
        print ""
        print " ".join(cmd)
        logStr = ""
        for cmd in cmds:
            logStr = logStr + "," + "{0}".format(data[cmd.replace(" ","_")])
        logStr = logTime + logStr
        commands.getoutput('echo "%s" >> %s' % (logStr, logFile))
    else:
        print "No response from inverter - shutdown? No Data sent to PVOutput.org"
    connection.close()
