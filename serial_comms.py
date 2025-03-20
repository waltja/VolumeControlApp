import serial
import serial.tools.list_ports
import threading
import time
import json


def list_available_ports():
    return [port.device for port in serial.tools.list_ports.comports()]


class SerialHandler:
    def __init__(self, baudrate=115200, callback=None):
        self.baudrate = baudrate
        self.callback = callback
        self.serial = None
        self.running = False
        self.thread_listen = None
        self.thread_app = None
        self.current_app = None
        self.logs = []
        self.values = []

    def connect_to_feather(self):
        available_ports = list_available_ports()
        for port in available_ports:
            try:
                self.serial = serial.Serial(port, self.baudrate, timeout=1)
                # Send a reset command
                self.serial.write(b'reset\n')

                while True:
                    if self.serial.in_waiting > 0:
                        data = self.serial.readline().decode('utf-8').strip()
                        if self.callback:
                            self.callback(data)
                        try:
                            parsed_volumes = eval(data)
                            if len(parsed_volumes) == 6:
                                self.values = parsed_volumes
                                break
                        except Exception as e:
                            self.callback(e)
                    else:
                        self.send_data('true')
                    time.sleep(1)
                return True
            except serial.SerialException as e:
                self.callback(e)
        self.serial = None
        return False

    def start(self):
        if not self.running:
            self.running = True
            self.thread_listen = threading.Thread(target=self.listen_for_data, daemon=True)
            self.thread_app = threading.Thread(target=self.set_current_app, daemon=True)
            self.thread_listen.start()
            self.thread_app.start()

    def stop(self):
        self.running = False
        if self.thread_listen:
            self.thread_listen.join()
        if self.thread_app:
            self.thread_app.join()
        if self.serial:
            self.serial.close()
            self.serial = None

    def listen_for_data(self):
        while self.running:
            if not self.serial or not self.serial.is_open:
                self.callback("No connection. Scanning for available COM ports...")
                if not self.connect_to_feather():
                    time.sleep(5)  # Retry every 5 seconds
                    continue
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.readline().decode('utf-8').strip()
                    if self.callback:
                        self.callback(data)
                    try:
                        parsed_volumes = eval(data)
                        if len(parsed_volumes) == 6:
                            self.values = parsed_volumes
                    except Exception as e:
                        self.log(f"Serial exception: {e}")
            except serial.SerialException as e:
                self.callback(e)
                self.serial.close()
                self.serial = None


    def set_current_app(self):
        while self.running:
            self.current_app = self.values.index(True, 1)-1

    def send_data(self, data):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(json.dumps(data).encode('utf-8'))
                self.callback(f"Sent: {data}")
            except serial.SerialException as e:
                self.callback(f"Failed to send data: {e}")

