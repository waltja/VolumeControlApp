import board
import digitalio
import analogio
import usb_cdc
import time
import json

# Define the Fader potentiometer (slide potentiometer motor position)
fader_potentiometer = analogio.AnalogIn(board.A0)

# Define Fader Capacitive Touch Sensor
fader_touch = analogio.AnalogIn(board.A3)

# Define Fader Motor
fader_motor = digitalio.DigitalInOut(board.D5)
fader_motor.direction = digitalio.Direction.OUTPUT

# Define buttons (6-step switches)
buttons = [
    digitalio.DigitalInOut(board.D12),
    digitalio.DigitalInOut(board.D11),
    digitalio.DigitalInOut(board.D10),
    digitalio.DigitalInOut(board.D9),
    digitalio.DigitalInOut(board.D8),
    digitalio.DigitalInOut(board.D7)
]

# Define button LEDs
button_leds = [
    digitalio.DigitalInOut(board.GP18),
    digitalio.DigitalInOut(board.GP19),
    digitalio.DigitalInOut(board.GP20),
    digitalio.DigitalInOut(board.GP00),
    digitalio.DigitalInOut(board.GP01),
    digitalio.DigitalInOut(board.GP06)
]

# Setup button LEDs as outputs
for led in button_leds:
    led.direction = digitalio.Direction.OUTPUT

# Initialize buttons as inputs with pull-up resistors
for button in buttons:
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP

# Serial communication setup
serial = usb_cdc.data

# Default volumes for each app
app_volumes = []

# Track the current app and potentiometer value
current_app = None
last_app = -1
set_point = 0
last_pot_value = -1


def read_fader():
    """Read and scale the potentiometer value (0-255)."""
    return int((fader_potentiometer.value / 65535) * 255)


def set_fader_to_app_value(app_index):
    """Simulate setting the potentiometer value to the app's stored volume."""
    global set_point
    if app_index is not None:
        set_point = app_volumes[app_index]


def read_buttons():
    """Read the state of all buttons and return the index of the pressed one."""
    for i, button in enumerate(buttons):
        if not button.value:  # Button pressed (active low)
            return i
    return None  # No button pressed


def send_serial_data_volumes():
    """Send data over USB serial in JSON format."""
    global app_volumes
    if serial and serial.connected:
        serial.write(json.dumps(app_volumes).encode("utf-8"))


def send_data(data):
    if serial and serial.connected:
        serial.write(data.encode("utf-8"))


def wait_for_start_signal():
    """Wait for a 'start' command and initialize app volumes."""
    global app_volumes, serial
    while True:
        if serial and serial.connected:
            print("Waiting for start signal...")
            while True:
                if serial.in_waiting > 0:
                    command = serial.readline().decode('utf-8').strip()
                    if command == 'false':
                        continue
                    # Parse initialization volumes from the command
                    try:
                        app_volumes = eval(command)  # Extract volumes
                        if len(app_volumes) != 6:
                            raise ValueError("Expected exactly 6 volume values.")
                        print(f"Start signal received. Initialized volumes: {app_volumes}")
                        send_data('true')
                        return
                    except Exception as e:
                        print(f"Error parsing volumes: {e}")
                        print("Retrying...")
                        send_data('false')
        else:
            print('No serial connection')
            print("Retrying...\n")
            time.sleep(5)


# Wait for the start signal and initialize volumes
wait_for_start_signal()

n = 0
# Main Loop
while True:
    # Read the currently active button
    new_app = read_buttons()

    # If the active app changes, update potentiometer value
    if new_app != current_app and new_app is not None:
        current_app = new_app
        set_fader_to_app_value(current_app)
        print(f"Switched to app {current_app}. Fader set to {set_point}.")

    # Read potentiometer value
    set_point = read_fader()

    # Only send data if the app or pot value changes
    if n == 6:
        if serial.connected and serial.in_waiting > 0:
            command = serial.readline().decode('utf-8').strip()
            print(command)
            if 'false' in command:
                send_data('true')
        elif not serial.connected:
            print('Connection lost')
            wait_for_start_signal()
        n = 0

    if n % 2 == 0:
        send_serial_data_volumes()
        print('Sent Periodic')
        last_app = current_app
        last_pot_value = set_point


    n += 1
    time.sleep(1)  # Avoid flooding the serial connection