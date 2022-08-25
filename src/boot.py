# This file is executed on every boot (including wake-boot from deepsleep)

import esp
"""
esp.osdebug(None)
#import webrepl
#webrepl.start()

import network
import time

#import webrepl_setup # this is causing Thonny to generate inside Thonny errors
wlan = network.WLAN(network.STA_IF) # create station interface
wlan.active(True)       # activate the interface

print("trying to connect to WiFi")
if not wlan.isconnected(): wlan.connect('<your SSID here>', '<your WiFi password here')
# connect to an AP

start_time = time.time()
while not wlan.isconnected():
            if time.time() - start_time > 5:
                print("failed to connect")
                break

if wlan.isconnected():
    print (wlan.ifconfig())         # get the interface's IP/netmask/gw/DNS addresses
    import webrepl
    #webrepl.start()
    webrepl.start(password="test")
"""