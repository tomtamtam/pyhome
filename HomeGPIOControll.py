import string
import time
import paho.mqtt.client as mqtt
import threading
import smbus

I2C_ADDRESSES = [0x25, 0x26, 0x27]

# Register-Adressen des MCP23017
IODIRA = 0x00  # Pin-Richtung für Port A
IODIRB = 0x01  # Pin-Richtung für Port B
GPIOA = 0x12   # Ausgang für Port A
GPIOB = 0x13   # Ausgang für Port B

bus = smbus.SMBus(1)  # I2C Bus 1 für Raspberry Pi

pin_states = {addr: {"A": 0x00, "B": 0x00} for addr in I2C_ADDRESSES}

def set_pin_direction(address):
    bus.write_byte_data(address, IODIRA, 0x00)
    bus.write_byte_data(address, IODIRB, 0x00)

def set_pin_state(address, port, pin):
    global pin_states
    if port == "A":
        pin_states[address]["A"] |= (1 << pin)
        bus.write_byte_data(address, GPIOA, pin_states[address]["A"])
    elif port == "B":
        pin_states[address]["B"] |= (1 << pin)
        bus.write_byte_data(address, GPIOB, pin_states[address]["B"])

def clear_all_pins():
    for address in I2C_ADDRESSES:
        pin_states[address]["A"] = 0x00
        pin_states[address]["B"] = 0x00
        bus.write_byte_data(address, GPIOA, 0x00)
        bus.write_byte_data(address, GPIOB, 0x00)
    print("Alle Pins wurden auf LOW gesetzt.")

def get_pin_details(pin_number):
    if 0 <= pin_number < 48:
        board_index = pin_number // 16
        local_pin = pin_number % 16
        address = I2C_ADDRESSES[board_index]
        if local_pin < 8:
            return address, "A", local_pin
        else:
            return address, "B", local_pin - 8
    else:
        return None, None, None

jalousineNames = ["zimmerTom", "zimmerElla", "schlafZimmer", "wohnZimmerGarten", "WohnZimmerStraße", 
                  "hauswirtschaftsraum", "kücheGarten", "kücheStraße", "büroGarten", "büroStraße"]

jalousineDurationTimes = [3] * len(jalousineNames)
currentPercentages = [0.00] * len(jalousineNames)

percentage_lock = threading.Lock()

def pulse_pin(pin: int, duration: float = 0.1):
    pin_number = int(pin)
    address, port, pin = get_pin_details(pin_number)
    if address is not None:
        set_pin_state(address, port, pin)
        print(f"Pin {pin_number} (Board {hex(address)}) - {port}{pin} wurde gesetzt.")
        time.sleep(duration)
        if port == "A":
            pin_states[address]["A"] &= ~(1 << pin)
            bus.write_byte_data(address, GPIOA, pin_states[address]["A"])
        elif port == "B":
            pin_states[address]["B"] &= ~(1 << pin)
            bus.write_byte_data(address, GPIOB, pin_states[address]["B"])
        print(f"Pin {pin_number} (Board {hex(address)}) - {port}{pin} wurde zurückgesetzt.")
    else:
        print("Ungültige Eingabe! Zahl muss zwischen 0 und 47 sein.")

def change_jalousine(jalousineName: string, percentage: float):
    if jalousineName not in jalousineNames:
        print("Jalousie nicht gefunden!")
        return

    jalousineNumb = jalousineNames.index(jalousineName)
    print(f"Jalousie {jalousineName} hat Index {jalousineNumb}")

    if jalousineNumb < 0 or jalousineNumb >= len(currentPercentages):
        print(f"Ungültiger Index {jalousineNumb} für Jalousie {jalousineName}")
        return

    with percentage_lock:
        percentageDifference = abs(currentPercentages[jalousineNumb] - percentage)

    durationTime = jalousineDurationTimes[jalousineNumb] * (percentageDifference / 100)

    with percentage_lock:
        if percentage < currentPercentages[jalousineNumb]:
            dirString = "down"
            pinNumb = jalousineNumb + 1
        elif percentage > currentPercentages[jalousineNumb]:
            dirString = "up"
            pinNumb = jalousineNumb
        else:
            print("Jalousie bereits in der gewünschten Position")
            return

    pulse_pin(pinNumb, durationTime)
    print(f"Jalousie {jalousineNames[jalousineNumb]} wird auf {percentage}% gestellt. Richtung: {dirString}, Pin: {pinNumb}, Dauer: {durationTime} Sekunden")
    time.sleep(durationTime)
    pulse_pin(pinNumb, 0.01)

    with percentage_lock:
        currentPercentages[jalousineNumb] = percentage
    save_list("/home/homeserver/homeserver/currentPercentages.txt", currentPercentages)

def on_message(client, userdata, msg):
    msgPayload = msg.payload.decode()
    print(f"Empfangenes Topic: {msg.topic}, Nachricht: {msgPayload}")

    if msg.topic == "Jalousinen":
       if msgPayload == "getPercentages":
            message = "\n".join(map(str, currentPercentages))  # Werte als String mit Zeilenumbrüchen
            print(f"Gesendete Nachricht: {repr(message)} ({type(message)})")
            client.publish("Jalousinen", message)
            print(f"Gesendet: {message}")
            return


        

    if msg.topic.startswith("Jalousie"):
        try:
            jalState = int(msgPayload.split(".")[0])  # Diese Zeile wird jetzt nur ausgeführt, wenn es kein "getPercentages" ist
        except ValueError:
            print(f"Fehler: Ungültige Nachricht empfangen: {msgPayload}")
        return
        try:
            jalIndex = int(msg.topic[-1])  # Extrahiert die letzte Ziffer aus dem Topic-Namen
            if 1 <= jalIndex <= len(jalousineNames):
                jalName = jalousineNames[jalIndex - 1]
                threading.Thread(target=change_jalousine, args=(jalName, jalState)).start()
            else:
                print(f"Ungültiger Index {jalIndex} im Topic {msg.topic}")
        except (ValueError, IndexError) as e:
            print(f"Fehler im Topic {msg.topic}: {e}")


def load_list_from_file(file_path):
    loaded_list = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                item = line.strip()
                try:
                    item = int(item)
                except ValueError:
                    try:
                        item = float(item)
                    except ValueError:
                        pass
                loaded_list.append(item)
        print("Datei erfolgreich geladen.")
        return loaded_list
    except FileNotFoundError:
        print(f"Fehler: Die Datei '{file_path}' wurde nicht gefunden.")
        return None
    except Exception as e:
        print(f"Fehler beim Lesen der Datei: {e}")
        return None

def save_list(file_path, file):
    with open(file_path, 'w') as f:
        for item in file:
            f.write(f"{item}\n")
    print("Datei erfolgreich gespeichert.")

for addr in I2C_ADDRESSES:
    set_pin_direction(addr)

if __name__ == "__main__":
    loaded_data = load_list_from_file("/home/homeserver/homeserver/currentPercentages.txt")
    if loaded_data is None:
        print("Fehler beim Laden der Datei! Setze default Werte.")
        currentPercentages = [0.00] * len(jalousineNames)
    else:
        currentPercentages = loaded_data

    print(currentPercentages)

    client = mqtt.Client()
    client.on_message = on_message
    client.connect("192.168.178.144", 1883, 60)
    client.subscribe("#")
    client.loop_forever()
