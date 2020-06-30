# Train Platform Data Script
# Copyright (c) 2020 Oliver Hallifax, Elegant Bricks

# Modify values in these sections with care to customise your display

#Section 1
#set mode to "fantasy" or "live"
#If set to "live" then the values in Section 2 are required to use the National Rail Enquiries real-time data lookup service.
#You will need to register for an API key for this service.
#If set to "fantasy" then the values in Section 3 are used to generate realistic looking train data with fake station names.
mode = "fantasy"

#Section 2
#  For Realtime National Rail data:
#  Key = API key obtained from their developer site
#  URL = API endpoint (should not change normally or often)
#  crs = CRS code for the station to show data for.
#  dst = (OPTIONAL) CRS code for a destination station to filter the data for.  For all trains to Waterloo from Clapham Junction use 'crs = "CLJ"' and 'dst = "WAT"'.
key = ""
url = 'https://lite.realtime.nationalrail.co.uk/OpenLDBWS/ldb11.asmx'
crs = "WAT"
dst = "WNR"

#Section 3
#  For fantasy timetable data:
#  towns = list of destination names, each in double quotes with a comma between them
#  platforms = list of platform numbers, separated by a comma
#  latetrainpercent = percentage of trains which run late, from 0 to 100%.  Specify just a number, without a % symbol.
#  latetrainmax = maximum number of minutes trains can run late by.
#  preventduplicates = True or False. If set to True will ensure no duplicate destinations ever appear. Requires at least 3 destination towns though!
#  magic = percentage of trains which get moved to platform 9 3/4.  Keep this number low - the default is 3.

#  Town names must fit in a 22 character field
#  e.g. this example is 20 characters
#  1234567890123456789012
#  Vancouver Brick City

towns = ["Stud City","Brickston","Attic Brick City","Murp Grove","Brickville","Bricknell","Bricksburg","Legollywood","Legoburg", "Vancouver Brick City","Micro:Bit City","Seattle Brick City", "Brickstown on Sea", "Seahaven"]
platforms = [1, 2, 3, 4, 5, 6, 7, 8, 9]
latetrainpercent = 80
latetrainmax = 4
preventduplicates = True
magic = 2

import os
import sys
import time
import json
import logging
import argparse
import random
from PIL import ImageFont
from time import gmtime, strftime, ctime, mktime, localtime
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("The requests library was not found. Run 'sudo -H pip3 install requests' to install it.")
    sys.exit()

try:
    import xmltodict
except ImportError:
    print("The xmltodict library was not found. Run 'sudo -H pip3 install xmltodict' to install it.")
    sys.exit()

try:
    from luma.core.render import canvas
    from luma.core import cmdline, error
except ImportError:
    print("The luma library was not found. Run 'sudo -H pip3 install luma.oled' to install it.")
    sys.exit()


#Global variables and constants
#Do not modify these
i = 0
rows = []
lasttrain = mktime(localtime())
destinationlength = 23
platformlength = 6

def get_eta(scheduled):
    #Function to randmly make some trains a little bit late.  Just like real life.
    global latetrainpercent
    global latetrainmax
    if (random.choice(range(0,100))>latetrainpercent):
        #Make it late - add a random number of minutes from 1 to 4 (expressed in seconds)
        etanumber = scheduled + (random.choice(range(1,latetrainmax))*60)
        etastring = ctime(etanumber)
        hour = etastring[11:13]
        mins = etastring[14:16]
        if (len(hour) == 1):
            hour = "0" + hour
        if (len(mins) == 1):
            mins = "0" + mins

        return (etanumber)

    else:
        return "On time"

def get_destination():
    if preventduplicates ==  True:
        found = False
        while found == False:
            dupe = False
            destination = destination = random.choice(towns)
            if (random.choice(range(0,100))>(100-magic)):
                destination = "Hogwarts"
            for row in rows:
                #Check all the rows to see if this is already in there somewhere
                if destination in row:
                    dupe = True
            if dupe == False:
                found = True
    else:
        destination = destination = random.choice(towns)
        if (random.choice(range(0,100))>(100-magic)):
            destination = "Hogwarts"

    return (destination)

def build_fantasy_data():
    #wipe our global list of rows
    rows.clear()
    currenttimenumber = mktime(localtime())

    while len(rows) < 3:
        #take the current time in seconds and add a random number of minutes from 2 to 5 (expressed in seconds)
        currenttimenumber = currenttimenumber + random.choice(range(2,4))*60
        currenttimestring = ctime(currenttimenumber)
        eta = get_eta(currenttimenumber)

        hour = currenttimestring[11:13]
        minute = currenttimestring[14:16]

        #Set this on each run to get the highest value when the function finishes looping.
        global lasttrain
        lasttrain =  currenttimenumber

        if len(str(eta)) > 7:
            etastring = ctime(eta)
            eta = etastring[11:13] + ":" + etastring[14:16]

        platform = str(random.choice(platforms)).strip()
        destination = get_destination().strip()

        if destination == "Hogwarts":
            platform = "9 3/4"

        newrow = hour + ":" + minute + " " + destination.ljust(destinationlength,' ') + platform.ljust(platformlength,' ') + str(eta)
        rows.append(newrow)

def update_fantasy_data():
    #Every period, check the list and remove any that are in the past.
    for row in rows:

        currentminute = int(str(ctime())[14:16])
        currenthour = int(str(ctime())[11:13])
        currenttime = datetime.now()

        #Check for a delayed time:
        if row.endswith("On time"):
            #Take the scheduled time
            traintime = row[0:6]
            hours = traintime[0:2]
            mins = traintime[3:5]
            #print(traintime)
        else:
            #Take the delayed time
            traintime = row[len(row)-5:]
            hours = traintime[0:2]
            mins = traintime[3:5]
            #print(traintime)

        #Bodge the time using the hours and minutes on the screen
        traintimestring = str(currenttime)[0:10] + " " + hours + ":" + mins + ":00.000000"
        traindatetime = datetime(int(traintimestring[0:4]),int(traintimestring[5:7]),int(traintimestring[8:10]),int(traintimestring[11:13]),int(traintimestring[14:16]))
        #then check if it's more than 12 hours different as that's clearly a time just past midnight
        diff = traindatetime - currenttime
        if diff.total_seconds() < -1000:
            traindatetime = traindatetime + timedelta(hours=24)

        #Remove entries in the timetable which have already departed.
        if traindatetime < currenttime:
            del rows[rows.index(row)]

    #We might have less than 3 on the board - let's build the list back up again.
    while len(rows) < 3:
        #take the current last train time in seconds and add a random number of minutes from 2 to 5 (expressed in seconds)
        global lasttrain
        lasttrain = float(lasttrain) + random.choice(range(2,4))*60

        currenttimestring = ctime(lasttrain)
        eta = get_eta(lasttrain)

        hour = currenttimestring[11:13]
        minute = currenttimestring[14:16]

        if len(str(eta)) > 7:
            etastring = ctime(eta)
            eta = etastring[11:13] + ":" + etastring[14:16]

        platform = str(random.choice(platforms)).strip()
        destination = get_destination().strip()

        if destination == "Hogwarts":
            platform = "9 3/4"

        if len(destination) > destinationlength:
            destination = destination[0:destinationlength]

        newrow = hour + ":" + minute + " " + destination.ljust(destinationlength, ' ') + platform.ljust(platformlength,' ') + str(eta)

        rows.append(newrow)

def fetch_nre_board():

    try:
        #Clear the whole board each time as data is coming live from NRE system.
        rows.clear()

        headers = {'content-type': 'text/xml'}
        xml_payload = '''
            <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                xmlns:types="http://thalesgroup.com/RTTI/2013-11-28/Token/types"
                xmlns:ns0="http://thalesgroup.com/RTTI/2017-10-01/ldb/">
            <SOAP-ENV:Header>
                <types:AccessToken>
                    <types:TokenValue>{KEY}</types:TokenValue>
                </types:AccessToken>
            </SOAP-ENV:Header>
            <SOAP-ENV:Body>
                <ns0:GetDepartureBoardRequest>
                <ns0:numRows>3</ns0:numRows>
                <ns0:crs>{CRS}</ns0:crs>
                <ns0:filterCrs>{DST}</ns0:filterCrs>
                <ns0:filterType>to</ns0:filterType>
                <ns0:timeOffset>2</ns0:timeOffset>
                <ns0:timeWindow>120</ns0:timeWindow>
                </ns0:GetDepartureBoardRequest>
            </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>
        '''

        payload = xml_payload.replace("{KEY}", key).replace("{CRS}", crs).replace("{DST}", dst)

        response = requests.post(url, data=payload, headers=headers)

        data = xmltodict.parse(response.content)

        services = data["soap:Envelope"]["soap:Body"]["GetDepartureBoardResponse"]["GetStationBoardResult"]["lt7:trainServices"]["lt7:service"]

        if type(services) is not list:
            services = [services]

        for service in services:
                try:
                    destination = service["lt5:destination"]["lt4:location"]["lt4:locationName"].strip()
                except Exception as e:
                    destination = ""

                try:
                    platform = service["lt4:platform"].strip()
                except Exception as e:
                    platform = ""

                if len(destination) > destinationlength:
                    destination = destination[0:destinationlength]

                destination = destination.ljust(destinationlength, ' ')
                platform = platform.ljust(platformlength, ' ')
                newrow = service["lt4:std"] + " " + destination + platform + service["lt4:etd"]
                rows.append(newrow)

    except Exception as e:
        logging.critical(e, exc_info=False)
        rows.append("ERROR : Cannot get live data")
        print("Error getting live data from National Rail Enquiries")
        print(str(e))


def show_data(device):

    pathname = os.path.dirname(os.path.abspath(__file__))

    # use custom fonts
    font1 = ImageFont.truetype(pathname + "/Cousine-Bold.ttf", 11)
    font2 = ImageFont.truetype(pathname + "/CourierPrime-Regular.ttf", 10)
    font3 = ImageFont.truetype(pathname + "/CourierPrime-Regular.ttf", 14)

    with canvas(device) as draw:
            draw.text((0,0), 'DEPARTURES               Plat Expt', font=font1, fill="white")
            maxrows = len(rows)
            if maxrows > 3:
                maxrows = 3
            for index in range(maxrows):
                draw.text((0, index*12+15), rows[index], font=font2, fill="white")
            draw.text((100, 52), time.strftime("%H:%M:%S", time.localtime()), font=font3, fill="white")

def show_startup(device):

    pathname = os.path.dirname(os.path.abspath(__file__))

    # use custom fonts
    font1 = ImageFont.truetype(pathname + "/CourierPrime-Regular.ttf", 8)
    font2 = ImageFont.truetype(pathname + "/CourierPrime-Regular.ttf", 10)
    font3 = ImageFont.truetype(pathname + "/CourierPrime-Regular.ttf", 15)

    with canvas(device) as draw:
            draw.text((0,0), 'The Elegant Departure Board', font=font3, fill="white")
            print('The Elegant Departure Board')
            draw.text((0,15), 'by www.elegantbricks.com', font=font2, fill="white")
            print('by www.elegantbricks.com')
            if mode =="fantasy":
                    draw.text((0,30), 'Running in fantasy mode with ' + str(len(platforms)) + ' platforms.', font=font1, fill="white")
                    print('Running in fantasy mode with ' + str(len(platforms)) + ' platforms.')
                    draw.text((0,38), str(len(towns)) + ' possible destinations.', font=font1, fill="white")
                    print(str(len(towns)) + ' possible destinations.')
                    draw.text((0,46), 'and ' + str(latetrainpercent) + '% of trains run on time.', font=font1, fill="white")
                    print('and ' + str(latetrainpercent) + '% of trains run on time.')
                    print('Stations are : ' + str(towns))
            else:
                    draw.text((0,30), 'Running in live mode for station "' + crs +'"', font=font2, fill="white")
                    print('Running in live mode for station "' + crs +'"')
                    if len(dst)>0:
                        draw.text((0,38), 'Filtered for trains to/via "' + dst + '"', font=font2, fill="white")
                        print('Filtered for trains to/via "' + dst +'"')
    time.sleep(10)

def display_settings(args):
    """
    Display a short summary of the settings.

    :rtype: str
    """
    iface = ''
    display_types = cmdline.get_display_types()
    if args.display not in display_types['emulator']:
        iface = 'Interface: {}\n'.format(args.interface)

    lib_name = cmdline.get_library_for_display_type(args.display)
    if lib_name is not None:
        lib_version = cmdline.get_library_version(lib_name)
    else:
        lib_name = lib_version = 'unknown'

    import luma.core
    version = 'luma.{} {} (luma.core {})'.format(
        lib_name, lib_version, luma.core.__version__)

    return 'Version: {}\nDisplay: {}\n{}Dimensions: {} x {}\n{}'.format(
        version, args.display, iface, args.width, args.height, '-' * 60)


def get_device(actual_args=None):
    """
    Create device from command-line arguments and return it.
    """
    if actual_args is None:
        actual_args = sys.argv[1:]
    parser = cmdline.create_parser(description='luma.examples arguments')
    args = parser.parse_args(actual_args)

    if args.config:
        # load config from file
        config = cmdline.load_config(args.config)
        args = parser.parse_args(config + actual_args)

    print(display_settings(args))

    # create device
    try:
        device = cmdline.create_device(args)
    except error.Error as e:
        parser.error(e)

    return device

def main():

    show_startup(device)

    while True:
        global i
        if mode =="fantasy":
            #No messing around with timestamps - build a full timetable of rows only if the rows list is empty.
            if len(rows) < 1:
                build_fantasy_data()

            #update the data array every 5 seconds
            if i==0:
                update_fantasy_data()

            #Update the screen
            show_data(device)

            i = i + 1
            if i>5:
                i=0

            time.sleep(1)

        elif mode=="live":
            #check a key has been provided
            if key == "":
                print("Error : in Live mode an API key is required from National Rail Enquiries.  You require a Darwin 'OpenLDBWS' free developer key.")
                print("Please check at https://www.nationalrail.co.uk/100296.aspx for further information on this service.")
                sys.exit()

            #Live data - call the API every 30 seconds
            if i==0:
                fetch_nre_board()

            #Update the screen
            show_data(device)
            i = i + 1
            if i>29:
                i=0
            time.sleep(1)

if __name__ == "__main__":

    try:
        device = get_device()
        main()
    except KeyboardInterrupt:
        pass


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)-15s - %(message)s'
)
# ignore PIL debug messages
logging.getLogger('PIL').setLevel(logging.ERROR)
