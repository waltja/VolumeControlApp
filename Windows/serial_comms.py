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
        self.dead = False

    def send_data(self, data):
        """Sends 'data' over current serial port"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(f"{data}\r\n".encode())
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
            if 'PermissionError' in str(e):
                return False
            self.callback(f"Failed to connect on port {port}: {e}")
            return False

        # Looks for incoming data and checks if it is "ack" signal and then if it contains "sack"
        try:
            await asyncio.wait_for(_wait_for_marker(ser, b"ack", 5.0), 10)
            await asyncio.to_thread(ser.write, f"{self.volumes}\r\n".encode())
            await asyncio.wait_for(_wait_for_marker(ser, b"sack", 5.0), 10)
            self.serial = ser
            return True
        except asyncio.TimeoutError:
            self.callback(f"Handshake timed out on {port}")
            await asyncio.to_thread(ser.close)
            return False

    def start_thread(self):
        """Begins the thread for func 'data_loop'"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.data_loop, daemon=True)
            self.thread.start()

    def stop_thread(self):
        """Ends the thread for func 'data_loop'"""
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

    def check_connection(self):
        """Sends a check to the feather, if NACK set 'dead' flag"""
        data = 'ack'
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(f"{data}\r\n".encode())
                self.callback(f"Sent: {data}")
            except serial.SerialException as e:
                self.callback(f"Failed to send data: {e}")


    def data_loop(self):
        """Listens for an incoming line and if it is new, adjust volumes"""
        last = time.monotonic()
        while self.running:
            if not self.serial or not self.serial.is_open or self.dead:
                self.callback("No connection or connections lost, rescanning COM ports.")
                if not asyncio.run(self.connect()):
                    time.sleep(2)  # Retry every 5 seconds
                    continue
            if time.monotonic() - last > 15:
                last = time.monotonic()
                self.dead = True
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.readline().decode().strip()
                    if data.count('sack') > 0:
                        data.replace('sack', '')
                        last = time.monotonic()
                    self.callback(f"{data}")
                    try:
                        data = eval(data)
                        if len(data) == 6 and data != self.volumes:
                            self.volumes = data
                    except NameError as e:
                        self.callback(f"Serial exception: {e}")
            except serial.SerialException as e:
                self.callback(f"Serial exception: {e}")
                self.running = False
            time.sleep(0.1)