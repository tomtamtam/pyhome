import string
#import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt

# Liste der Jalousienamen und deren Dauerzeiten
jalousineNames = ["zimmerTom", "zimmerElla", "schlafZimmer", "badBraun", "wohnZimmerGarten", "WohnZimmerStraße", "hauswirtschaftsraum", "kücheGarten", "kücheStraße", "büroGarten", "büroStraße"]
jalousineDurationTimes = [20, 40, 40, 10, 60, 10, 10, 10, 10, 40, 10]
currentPercentages = [100.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]

# Funktion zum Simulieren des GPIO-Pulsierens
def pulse_pin(pin: int, duration: float = 0.1):
    #GPIO.setmode(GPIO.BCM)  # BCM-Nummerierung verwenden
    #GPIO.setup(pin, GPIO.OUT)

    #GPIO.output(pin, GPIO.HIGH)
    #time.sleep(duration)
    #GPIO.output(pin, GPIO.LOW)

    #GPIO.cleanup()  # GPIO-Pins zurücksetzen
    print(f"Pin {pin} wurde für {duration} Sekunden aktiviert")

# Funktion zum Ändern der Jalousienposition
def change_jalousine(jalousineName: string, percentage: float):
    # Variablen initialisieren
    jalousineNumb = 0
    percentageDifference = 0.00
    dir = False
    dirString = ""
    pinNumb = 0

    # Finde den Index der Jalousine in der Liste
    if jalousineName not in jalousineNames:
        print("Jalousie nicht gefunden!")
        return
    else:
        jalousineNumb = jalousineNames.index(jalousineName)

    # Berechne die Differenz zwischen alter und neuer Position
    percentageDifference = abs(currentPercentages[jalousineNumb] - percentage)

    # Berechne die Dauer der Bewegung
    durationTime = jalousineDurationTimes[jalousineNumb] * (percentageDifference / 100)

    # Bestimme die Richtung der Bewegung
    if percentage < currentPercentages[jalousineNumb]:
        dir = False
        dirString = "down"
    elif percentage > currentPercentages[jalousineNumb]:
        dir = True
        dirString = "up"
    else:
        print("Jalousie bereits in der gewünschten Position")
        return

    # Setze die Pin-Nummer basierend auf der Richtung
    if dir:
        pinNumb = jalousineNumb
    else:
        pinNumb = jalousineNumb + 1

    # Aktiviere den Pin für die Bewegung
    pulse_pin(pinNumb, 0.01)
    print(f"Jalousie {jalousineNames[jalousineNumb]} wird auf {percentage}% gestellt. Richtung: {dirString}, Pin: {pinNumb}, Dauer: {durationTime} Sekunden")

    # Warte, bis die Bewegung abgeschlossen ist
    time.sleep(durationTime)

    # Deaktiviere den Pin, um die Bewegung zu stoppen
    pulse_pin(pinNumb, 0.01)
    print(f"Jalousie {jalousineNames[jalousineNumb]} hat die gewünschte Position erreicht.")

    # Aktualisiere die aktuelle Position der Jalousine
    currentPercentages[jalousineNumb] = percentage

# Callback-Funktion für MQTT-Nachrichten
def on_message(client, userdata, msg):
    print(f"Empfangenes Topic: {msg.topic}, Nachricht: {msg.payload.decode()}")
    msgTopic = msg.topic
    jalIndex = 40000
    jalName = ""
    jalState = int(msg.payload.decode().split(".")[0])

    if msgTopic[:8] == "Jalousie":
        try:
            jalIndex = int(msgTopic[-1])  # Konvertiere den letzten Teil des Topics in einen Integer
            jalName = jalousineNames[jalIndex]
            print(f"Jalousine: {jalIndex}")

            change_jalousine(jalName, jalState / 100)
        except (ValueError, IndexError):
            print("Ungültiger Index oder Konvertierungsfehler im Topic")

# MQTT-Client initialisieren und verbinden
client = mqtt.Client()
client.on_message = on_message

client.connect("192.168.178.144", 1883, 60)

# Alle Topics abonnieren (Wildcard #)
client.subscribe("#")

# Endlosschleife für die MQTT-Kommunikation
client.loop_forever()