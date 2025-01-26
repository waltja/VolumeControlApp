import serial
import serial.tools.list_ports
import threading
import time


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
                self.send_data(volumes)
                while True:
                    if self.serial.in_waiting > 0:
                        print(self.serial.readline().decode('utf-8'))
                        if self.serial.readline().decode('utf-8').count('true') > 0:
                            break
                        else:
                            self.send_data('false')
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
                        self.callback(f'Received: {data}')
                    try:
                        data = eval(data)
                        if len(data) == 6 and data != self.volumes:
                            self.volumes = data
                    except NameError as e:
                        self.log(f"Serial exception: {e}")
            except serial.SerialException as e:
                self.log(f"Serial exception: {e}")
                self.serial.close()
                self.serial = None

    def send_data(self, data):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(f"{data}\n".encode('utf-8'))
                self.log(f"Sent: {data}")
            except serial.SerialException as e:
                self.log(f"Failed to send data: {e}")

    def get_logs(self):
        return self.logs
