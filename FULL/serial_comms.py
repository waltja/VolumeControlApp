import threading
import serial
import serial.tools.list_ports as list_ports


class SerialHandler:
    def __init__(self, port, baudrate, callback=None):
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.serial = None
        self.running = False
        self.thread = None

    def start(self):
        """Start the serial communication thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.listen_to_serial, daemon=True)
            self.thread.start()

    def stop(self):
        """Stop the serial communication thread."""
        self.running = False
        if self.thread:
            self.thread.join()
        self.serial.close()

    def connect(self):
        """Attempt to connect to the first available COM port."""
        ports = list(list_ports.comports())
        if ports.count(self.port) > 0:
            try:
                self.serial = serial.Serial(self.port, baudrate=9600, timeout=1)
                print(f"Connected to {self.port}")
            except Exception as e:
                print(f"Failed to connect to {self.port}: {e}")
        else:
            print("No COM ports available.")

    def is_connected(self):
        """Check if the serial port is connected."""
        return self.serial is not None

    def list_comports(self):
        """Lists currently available COM ports"""
        return list_ports.comports()

    def listen_to_serial(self):
        """Continuously listen for incoming serial data."""
        while self.running:
            if self.serial.in_waiting > 0:
                try:
                    data = self.serial.readline().decode('utf-8').strip()
                    if self.callback:
                        self.callback(data)
                except Exception as e:
                    print(f"Error reading from serial: {e}")

    def send_serial_data(self, data):
        """Send data to the serial port."""
        try:
            if self.serial.is_open:
                self.serial.write(f"{data}\n".encode('utf-8'))
        except Exception as e:
            print(f"Error sending data: {e}")
