import string
import time
import paho.mqtt.client as mqtt
import threading

# Liste der Jalousienamen und deren Dauerzeiten
jalousineNames = ["zimmerTom", "zimmerElla", "schlafZimmer", "wohnZimmerGarten", "WohnZimmerStraße", "hauswirtschaftsraum", "kücheGarten", "kücheStraße", "büroGarten", "büroStraße"]
jalousineDurationTimes = [0,3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
currentPercentages = [0,0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]

# Lock für Thread-sichere Zugriffe auf currentPercentages
percentage_lock = threading.Lock()

# Funktion zum Simulieren des GPIO-Pulsierens
def pulse_pin(pin: int, duration: float = 0.1):
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
        print(f"Jalousie {jalousineName} hat Index {jalousineNumb}")

    # Überprüfe, ob der Index gültig ist
    if jalousineNumb < 0 or jalousineNumb >= len(currentPercentages):
        print(f"Ungültiger Index {jalousineNumb} für Jalousie {jalousineName}")
        return

    # Berechne die Differenz zwischen alter und neuer Position
    with percentage_lock:
        percentageDifference = abs(currentPercentages[jalousineNumb] - percentage)

    # Berechne die Dauer der Bewegung
    durationTime = jalousineDurationTimes[jalousineNumb] * (percentageDifference / 100)

    # Bestimme die Richtung der Bewegung
    with percentage_lock:
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

    with percentage_lock:
        currentPercentages[jalousineNumb] = percentage
    save_list("/home/tom/currentPercentages.txt", currentPercentages)

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
            if jalIndex < 1 or jalIndex > len(jalousineNames):
                print(f"Ungültiger Index {jalIndex} im Topic {msgTopic}")
                return
            jalName = jalousineNames[jalIndex - 1]  # Index um 1 verringern, da Python bei 0 beginnt
            print(f"Jalousine: {jalIndex} ({jalName})")

            # Starte die Jalousienbewegung in einem separaten Thread
            threading.Thread(target=change_jalousine, args=(jalName, jalState)).start()
        except (ValueError, IndexError) as e:
            print(f"Fehler im Topic {msgTopic}: {e}")

# Funktion um die state datei zu loaden
def load_list_from_file(file_path):
    """
    Lädt den Inhalt einer Textdatei in eine Liste (Array).

    :param file_path: Der Pfad zur Textdatei.
    :return: Eine Liste mit dem Inhalt der Datei.
    """
    loaded_list = []  # Hier wird der Inhalt der Datei gespeichert

    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Entferne Leerzeichen und Zeilenumbrüche
                item = line.strip()
                # Versuche, den Wert in eine Zahl umzuwandeln (falls möglich)
                try:
                    item = int(item)  # Oder float(item), falls es sich um Dezimalzahlen handelt
                except ValueError:
                    try:
                        item = float(item)  # Versuche, den Wert in eine Dezimalzahl umzuwandeln
                    except ValueError:
                        pass  # Behalte den Wert als String, falls keine Konvertierung möglich ist
                loaded_list.append(item)
        print("Datei erfolgreich geladen.")
        return loaded_list
    except FileNotFoundError:
        print(f"Fehler: Die Datei '{file_path}' wurde nicht gefunden.")
        return None
    except Exception as e:
        print(f"Fehler beim Lesen der Datei: {e}")
        return None

# Funktion um die state datei zu speichern
def save_list(file_path, file):
    my_list = file

    with open(file_path, 'w') as file:
        for item in my_list:
            file.write(f"{item}\n")

    print("Datei erfolgreich gespeichert.")

# Main Methode
if __name__ == "__main__":
    # Load state file
    currentPercentages = load_list_from_file("/home/tom/currentPercentages.txt")
    print(currentPercentages)

    # MQTT-Client initialisieren und verbinden
    client = mqtt.Client()
    client.on_message = on_message

    client.connect("192.168.178.144", 1883, 60)

    # Alle Topics abonnieren (Wildcard #)
    client.subscribe("#")

    # Endlosschleife für die MQTT-Kommunikation
    client.loop_forever()