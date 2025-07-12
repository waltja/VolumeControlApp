import serial
import serial.tools.list_ports
import threading
import time
import asyncio


def list_available_ports():
    """Find all available ports and return them"""
    return [port.device for port in serial.tools.list_ports.comports()]


async def _wait_for_marker(ser, marker, timeout):
    """Wait up to `timeout` seconds for a line containing `marker`."""
    end = asyncio.get_event_loop().time() + timeout
    while True:
        if asyncio.get_event_loop().time() > end:
            raise asyncio.TimeoutError()
        if await asyncio.to_thread(lambda: ser.in_waiting > 0):
            line = await asyncio.to_thread(ser.readline)
            if marker in line:
                return
        await asyncio.sleep(0.05)


class SerialHandler:
    def __init__(self, baudrate=115200, callback=None, volumes=None):
        self.baudrate = baudrate
        self.callback = callback
        self.serial = serial.Serial()
        self.volumes = volumes
        self.running = False
        self.thread = None

    def send_data(self, data):
        """Sends 'data' over current serial port"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(f"{data}\n".encode())
                self.callback(f"Sent: {data}")
            except serial.SerialException as e:
                self.callback(f"Failed to send data: {e}")

    async def handshake(self, port):
        """Attempts to initiate a connection with a waiting feather module"""
        # Attempts to create new serial connections
        try:
            ser = await asyncio.to_thread(serial.Serial, port, self.baudrate, timeout=1)
            self.callback(f"Connected to device on port {port}")
        except Exception as e:
            self.callback(f"Failed to connect on port {port}: {e}")
            return False

        # Looks for incoming data and checks if it is "ack" signal and then if it contains "sack"
        try:
            await asyncio.wait_for(_wait_for_marker(ser, b"ack", 5.0), 10)
            await asyncio.to_thread(ser.write, f"{self.volumes}\n".encode())
            await asyncio.wait_for(_wait_for_marker(ser, b"sack", 5.0), 10)
        except asyncio.TimeoutError:
            self.callback(f"Handshake timed out on {port}")
            await asyncio.to_thread(ser.close)
            return False

    def start_thread(self):
        """Begins the thread for func 'listen_for_data'"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.listen_for_data, daemon=True)
            self.thread.start()

    def stop_thread(self):
        """Ends the thread for func 'listen_for_data'"""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.serial:
            self.serial.close()

    async def connect(self):
        """Connect to every Serial device and listen for feather "ack" signal"""
        available_ports = list_available_ports()

        # Cycles every available port until one is open and connects
        for port in available_ports:
            try:
                ok = await asyncio.wait_for(self.handshake(port), timeout=10.0)
            except asyncio.TimeoutError:
                continue
            if ok:
                self.callback(f"Connect success on port {port}!")
                return  True

        # If all ports are exhausted, exit
        return False

    def listen_for_data(self):
        """Listens for an incoming line and if it is new, adjust volumes"""
        while self.running:
            if not self.serial or not self.serial.is_open:
                self.callback("No connection. Scanning for available COM ports...")
                if not self.connect():
                    time.sleep(5)  # Retry every 5 seconds
                    continue
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.readline().decode('utf-8').strip().replace('sack', '')
                    self.callback(f"{data}")
                    try:
                        data = eval(data)
                        if len(data) == 6 and data != self.volumes:
                            self.volumes = data
                    except NameError as e:
                        self.callback(f"Serial exception: {e}")
            except serial.SerialException as e:
                self.callback(f"Serial exception: {e}")
                self.stop_thread()
