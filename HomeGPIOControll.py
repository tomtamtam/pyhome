import string
#import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt


jalousineNames = ["zimmerTom", "zimmerElla", "schlafZimmer", "badBraun", "wohnZimmerGarten", "WohnZimmerStraße","hauswirtschaftsraum", "kücheGarten", "kücheStraße", "büroGarten", "büroStraße"]
jalousineDurationTimes = [20, 40, 40, 10, 60, 10, 10, 10, 10, 40, 10]
currentPercentages = [100.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]


def pulse_pin(pin: int, duration: float = 0.1):
    #GPIO.setmode(GPIO.BCM)  # BCM-Nummerierung verwenden
    #GPIO.setup(pin, GPIO.OUT)

    #GPIO.output(pin, GPIO.HIGH)
    #time.sleep(duration)
    #GPIO.output(pin, GPIO.LOW)

    #GPIO.cleanup()  # GPIO-Pins zurücksetzen
    print("pin "+str(pin)+"was set")


# Beispielaufruf:
# pulse_pin(17, 0.5)  # Schaltet GPIO 17 für 0.5 Sekunden an


def change_jalousine(jalousineName: string, percentage: float):
    # set variables
    jalousineNumb = 0
    percentageDifference = 0.00
    dir = False
    dirString = ""
    pinNumb = 0


    for i, name in enumerate(jalousineNames):
        if jalousineName == name:
                jalousineNumb = i
                break
    if jalousineName not in jalousineNames:
        print("Jalousie nicht gefunden!")
        return

    # set difference between old and new percentage
    if currentPercentages[jalousineNumb] >= percentage:
        percentageDifference = currentPercentages[jalousineNumb] - percentage
    else:
        percentageDifference = percentage - currentPercentages[jalousineNumb]

    # set durationtime between old and new percentage
    print(percentageDifference)
    print(jalousineDurationTimes[jalousineNumb])
    durationTime = jalousineDurationTimes[jalousineNumb] * (percentageDifference/100)



    # set direction to move direction
    if percentage < currentPercentages[jalousineNumb]:
        dir = False
        dirString = "down"
        print("set directiont to:" + str(dirString))
    elif percentage > currentPercentages[jalousineNumb]:
        dir = True
        dirString = "up"
        print("set directiont to:" + str(dirString))
    else:
        print("same position at direction calculation")


    # set pin to set calculating pin for upmoving and downmoving
    if dir == True:
        pinNumb = jalousineNumb
        print("set jalousine " + str(jalousineNames[jalousineNumb]) + " to " + str(percentage) + " pin = " + str(pinNumb))
    else:
        pinNumb = jalousineNumb+1
        print("set jalousine " + str(jalousineNames[jalousineNumb]) + " to " + str(percentage) + " direction: " + str(dirString) + " pin: " + str(pinNumb))

    # set pin at chosen position foe 0.1 seconds
    pulse_pin(pinNumb, 0.01)
    print("pin :"+str(pinNumb)+"was set first time moving "+(dirString)+"wards durationTime: "+str(durationTime))

    # set timer as long as jalousine is moving
    time.sleep(durationTime)

    #set to false
    pulse_pin(jalousineNumb, 0.01)
    print("pin :"+str(pinNumb)+"was set second time stopping moving "+(dirString)+"wards")



def on_message(client, userdata, msg):
    print(f"Empfangenes Topic: {msg.topic}, Nachricht: {msg.payload.decode()}")
    msgTopic = msg.topic
    jalIndex = 4000
    jalName = ""
    jalState = int(msg.payload.decode().split(".")[0])
    if msgTopic[:8]== "Jalousie":
        jalIndex = msgTopic[-1]
        jalName = jalousineNames[jalIndex]
        print("jalousine: "+jalIndex)

        change_jalousine(jalName,jalState/100)
    #change_jalousine()

client = mqtt.Client()
client.on_message = on_message

client.connect("192.168.178.144", 1883, 60)

# Alle Topics abonnieren (Wildcard #)
client.subscribe("#")

client.loop_forever()









