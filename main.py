#  CompTech 10 Term 2 Project - Raspberry Pi Pico Weather Station with LCD Display & WIFI
#  By Evan Prael, Feb 15, 2024
#
#  This program runs on a Raspberry Pi Pico W, reads a weather sensor and displays that data
#  on a LCD Screen. It also connects to WIFI and displays it on a web page. 
# 
#  Code and libraries used from these websites:
#
# web server, weather sensor:  
# https://how2electronics.com/bme280-raspberry-pi-pico-w-web-server-weather-station/
# https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf#page=22
#
# LCD display & fonts
# https://diyprojectslab.com/raspberry-pi-pico-tft-lcd-touch-screen-tutorial/
# https://github.com/rdagger/micropython-ili9341/tree/master
#
# Complete Project on Github
# https://github.com/eprael/weatherstation
#
# Parts list on Amazon
# https://www.amazon.ca/hz/wishlist/ls/19ZVP4QBNUOJP?viewType=grid

# micropython libraries
from machine import Pin, I2C, SPI       # pico board libraries
import time, sys                        # system libraries
import socket, network                  # network libraries
import bme280                           # weather sensor library (bme280.py)
from ili9341 import Display, color565   # LCD display library (ili9341.py)
from xglcd_font import XglcdFont        # GLCD font library (xglcd_font.py)
import random

# Onboard LED - turn on right away and use as a power light
led = machine.Pin("LED", machine.Pin.OUT)
led.on()

print('initializing devices...')

# weather sensor and pins
i2c=I2C(0,sda=Pin(20), scl=Pin(21), freq=400000)    

# LCD display and pins
spi = SPI(1, baudrate=40000000, sck=Pin(14), mosi=Pin(15))
display = Display(spi, dc=Pin(6), cs=Pin(17), rst=Pin(7))


# fonts for display 
print('loading fonts...')
smallFont = XglcdFont('fonts/Verdana12x13.c', 12, 13)
smallFontBold = XglcdFont('fonts/VerdanaBold16x14.c', 16, 14)
largeFont = XglcdFont('fonts/EspressoDolce18x24.c', 18, 24)

# screen colors
backgroundColor = color565(0, 0, 255)  # blue
headerColor = color565(255, 0, 0) # red
headerBackground = color565(255, 255, 255) # white
footerColor = color565(0, 255, 255) # cyan
footerBackground = color565(0, 0, 180) # darkblue
textColor = color565(255, 255, 0) # yellow
shadowColor = color565(0, 0, 0) # black

# data for screen and web
temperature = ''
pressure = ''
humidity = ''

# wifi networks to try (WIFI NAME : WIFI PWD) 
wifiNetworks = {
   'SM-S918W0938' : 'xxxxx',
   'TLA Student' : 'yyyy'
}


# setup wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

#disable power saving for wifi
wlan.config(pm = 0xa11140)
 

# ----------------- functions -----------------

# refresh weather data from sensor
def refresh_weatherData():
    global temperature, pressure, humidity
    try:
        bme = bme280.BME280(i2c=i2c)
        temperature = bme.values[0]
        pressure = bme.values[1]
        humidity = bme.values[2]
    except:
        # sensor not connected or not working
        temperature = "n/a"
        pressure =  "n/a"
        humidity =  "n/a"

        # random data for testing
        # temperature = f"{random.randint(19,28)}*C"
        # pressure = f"{random.randint(950,1090)}.2 hPa"
        # humidity = f"{random.randint(30,40)}.1%"

# create a web page with the weather data in it
# this gets sent back to the browser 

def web_page():
    html = """
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:,">
    <style>
        body { text-align: center; font-family: "Helvetica", Arial;}
        table { border-collapse: collapse; width:55%; margin-left:auto; margin-right:auto; }
        th { padding: 12px; background-color: #87034F; color: white; }
        tr { border: 2px solid #000556; padding: 12px; }
        tr:hover { background-color: #bcbcbc; }
        td { border: none; padding: 14px; }
        .sensor { color:DarkBlue; font-weight: bold; background-color: #ffffff; padding: 1px;  
        
        img{display: block; margin-left: auto; margin-right: auto;}
    </style>
    <meta http-equiv="refresh" content="60">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <h1>
        Welcome to Evan's Weather Station
    </h1>
    Want to know the temperature, check it here! <br>
    <br>
    
    <img src="https://static.wikia.nocookie.net/legobatman/images/a/af/Batman1_Robin.png" height="200" />

    <table>
    <tr>
        <th>Parameters</th><th>Value</th>
    </tr>
    <tr>
        <td>
            Temperature
        </td>
        <td>
            <span class="sensor">""" + temperature + """</span>
        </td>
    </tr>
    <tr>
        <td>
            Pressure</td><td><span class="sensor">""" + pressure + """</span>
        </td>
    </tr>
    <tr>
        <td>Humidity</td>
        <td><span class="sensor">""" + humidity + """</span></td>
    </tr> 
    </table>
</body>
</html>"""
    return html


# connect to wifi. Try each wifi network until connected
# return True if connected, False if not    
def connect_to_wifi():
   
    wlan.disconnect()
    time.sleep(1)

    # try different wifis until connected
    for ssid, password in wifiNetworks.items():

        # sometimes the pico doesn't connect on the first try, so try twice
        for i in range(2):

            print('connecting to network', ssid, ',', password, '...')
            wlan.connect(ssid, password)
            wait = 0
            #while not wlan.isconnected() and wait < 10:
            while wlan.status() >= 0 and wlan.status() < 3 and wait < 10:
                print ('waiting for connection... status = ', wlan.status())
                time.sleep(1)
                wait += 1

            if wlan.isconnected():
                print(f"connected. IP: {wlan.ifconfig()[0]}")  
                return True
            else:
                print(f"connection to {ssid} failed. status = {wlan.status()}")
    
    return False
           

# display-print: writes text to the display using display.draw_text.  
def dprint (x,y,foreColor,backColor,font,msg):
    display.draw_text(y, 320-x, msg, font, foreColor, landscape=True, background=backColor)


# initialize the display
# draw title and show "connecting to wifi" message
def initialize_display():
    print('initializing display...')
    display.clear(backgroundColor)
    display.fill_rectangle(0,0,40,320,headerBackground)
    display.fill_rectangle(41,0,1,320,shadowColor)
    dprint (35,10, headerColor, headerBackground, largeFont, "Evan`s Weather Station")
    dprint (54,96, textColor, backgroundColor, largeFont, 'Connecting to WIFI')
    dprint (90,144, textColor, backgroundColor,largeFont, 'Please wait...')

# show wifi info at bottom of screen
def setup_display():
    # clear all but the header
    display.fill_rectangle(43,0,197,320,backgroundColor)

    # create footer bar
    display.fill_rectangle(200,0,40,320,footerBackground)
    display.fill_rectangle(199,0,1,320,shadowColor)

    # show what to do to view weather data online
    if (wlan.isconnected()):
        dprint (5,204,footerColor,footerBackground, smallFont, f"To view online, use WIFI: [{wlan.config('essid')}]") 
        dprint (33,222,footerColor,footerBackground, smallFont, f"and go to ")
        dprint (110,221,footerColor,footerBackground, smallFontBold, f"http://{wlan.ifconfig()[0]}")
    else:
        dprint (96,215,footerColor,footerBackground, smallFont, f"WIFI not available") 

    # display weather headings
    dprint (20, 65, textColor, backgroundColor, largeFont, 'Temperature')
    dprint (20, 107, textColor, backgroundColor, largeFont, 'Air Pressure')
    dprint (20, 150, textColor, backgroundColor, largeFont, 'Rel. Humidity')
    # display colons separately so they can be aligned
    dprint (160, 63, textColor, backgroundColor, largeFont, ':')
    dprint (160, 104, textColor, backgroundColor, largeFont, ':')
    dprint (160, 148, textColor, backgroundColor, largeFont, ':')


# refresh and display weather data 
def display_weatherData():
    print('updating display...')
    refresh_weatherData()
    dprint (175, 65, textColor, backgroundColor, largeFont, f"{temperature}  ")
    dprint (175, 107, textColor, backgroundColor, largeFont, f"{pressure}  ")
    dprint (175, 150, textColor, backgroundColor, largeFont, f"{humidity}  ")

# with wifi connected, run both the display and web server
def run_display_and_webserver():

    # first update the display, then update it every 30s while waiting for a web connection
    display_weatherData()

    print('launching web server...')

    # setup web server on port 80
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('', 80))
    server.listen(5)
    print('listening on', addr)

    stay_in_loop=True

    # while waiting for a web connection, break out every 30s to update the display
    server.settimeout(30)
    while stay_in_loop:
        try:
            print('waiting for connection...')
            conn, addr = server.accept()

            print('connection from %s' % str(addr))
            conn.settimeout(3.0)
            try:
                print('receiving request...')
                request = conn.recv(1024)
                print(str(request))              
            except:
                print('receiving request timed out')

            # HTTP-Response send
            print('getting web page')
            returnHTML = web_page()
            print(returnHTML[0:100])
            print('sending header...')
            conn.send('HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n')
            print('sending html...')
            conn.sendall(returnHTML)
            print('closing connection')
            conn.close()

        except OSError as e:
            # error 110 is the timeout that happens every 30s when waiting for a web connection
            # so just update the display and continue
            if e.errno == 110:
                display_weatherData()
            else:
                print('OSError', e)

        except Exception as e:
            print ('Exception', e)
            conn.close()
            print('connection closed')        
        except KeyboardInterrupt:
            # if the user presses ctrl-c or presses stop in vscode, 
            # it's helpful to close everything down, otherwise the web server 
            # doesn't startup properly the next time and needs a reset
            print('KeyboardInterrupt')
            keepListening = False
            print('connection closed')
            stay_in_loop = False

    print('closing server...')
    server.close()
    time.sleep(1)
    print('disconnecting wifi...')
    wlan.disconnect()
    time.sleep(1)
    print('cleaning up...')
    wlan.active(False)
    print('web server ended.')


def run_display_only():

    print('launching display loop...')
    stay_in_loop=True

    while stay_in_loop:
        try:
            display_weatherData()
            time.sleep(30)
        except Exception as e:
            print ('Exception', e)
        except KeyboardInterrupt:
            print ('Keyboard interrupt')
            stay_in_loop = False

    print('display loop ended.')



# ----------------- main -----------------


initialize_display()
connect_to_wifi()
setup_display()

if wlan.isconnected():
    run_display_and_webserver()
else:
    run_display_only()

print('clearing display...')
display.clear()
print('turning off LED...')
led.off()
print('done.')


