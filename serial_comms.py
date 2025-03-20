import serial
import serial.tools.list_ports
import threading
import time
import json


class SerialHandler:
    def __init__(self, baudrate=115200, callback=None):
        self.baudrate = baudrate
        self.callback = callback
        self.serial = None
        self.running = False
        self.thread = None
        self.logs = []
        self.volumes = []

    def log(self, message):
        self.logs.append(message)

    def list_available_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def connect_to_feather(self, volumes):
        available_ports = self.list_available_ports()
        for port in available_ports:
            try:
                self.serial = serial.Serial(port, self.baudrate, timeout=1)
                self.log(f"Connected to Feather on port {port}")

                # Send a reset command
                self.serial.write(b'reset\n')

                while True:
                    if self.serial.in_waiting > 0:
                        data = self.serial.readline().decode('utf-8').strip()
                        self.log(f"Received: {data}")
                        if self.callback:
                            self.callback(data)
                        try:
                            parsed_volumes = eval(data)
                            if len(parsed_volumes) == 6 and parsed_volumes != self.volumes:
                                self.volumes = parsed_volumes
                        except Exception as e:
                            self.log(f"Serial exception: {e}")
                    time.sleep(1)
                return True
            except serial.SerialException as e:
                self.log(f"Failed to connect on port {port}: {e}")
        self.serial = None
        time.sleep(1)
        return False

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.listen_for_data, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.serial:
            self.serial.close()
            self.serial = None

    def listen_for_data(self):
        while self.running:
            if not self.serial or not self.serial.is_open:
                self.log("No connection. Scanning for available COM ports...")
                if not self.connect_to_feather():
                    time.sleep(5)  # Retry every 5 seconds
                    continue
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.readline().decode('utf-8').strip()
                    self.log(f"Received: {data}")
                    if self.callback:
                        self.callback(data)
                    try:
                        parsed_volumes = eval(data)
                        if len(parsed_volumes) == 6 and parsed_volumes != self.volumes:
                            self.volumes = parsed_volumes
                    except Exception as e:
                        self.log(f"Serial exception: {e}")
            except serial.SerialException as e:
                self.log(f"Serial exception: {e}")
                self.serial.close()
                self.serial = None

    def send_data(self, data):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(json.dumps(data).encode('utf-8'))
                self.log(f"Sent: {data}")
            except serial.SerialException as e:
                self.log(f"Failed to send data: {e}")

    def get_logs(self):
        return self.logs


available_ports = [port.device for port in serial.tools.list_ports.comports()]
print(available_ports)
for port in available_ports:
    try:
        serials = serial.Serial(port, 115200, timeout=1)
        break
    except Exception:
        pass
while True:
    if serials.in_waiting > 0:
        data = serials.readline().decode('utf-8').strip()
        print(data)
