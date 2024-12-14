import board
import digitalio
import analogio
import usb_cdc
import time

# Define the potentiometer (slide potentiometer motor position)
potentiometer = analogio.AnalogIn(board.A0)

# Define buttons (6-step switches)
buttons = [
    digitalio.DigitalInOut(board.D22),
    digitalio.DigitalInOut(board.D24),
    digitalio.DigitalInOut(board.D26),
    digitalio.DigitalInOut(board.D28),
    digitalio.DigitalInOut(board.D30),
    digitalio.DigitalInOut(board.D32)
]

# Setup buttons as inputs with pull-up resistors
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
pot_value = 0
last_pot_value = -1


def read_potentiometer():
    """Read and scale the potentiometer value (0-255)."""
    return int((potentiometer.value / 65535) * 255)


def set_potentiometer_to_app_value(app_index):
    """Simulate setting the potentiometer value to the app's stored volume."""
    global pot_value
    if app_index is not None:
        pot_value = app_volumes[app_index]


def read_buttons():
    """Read the state of all buttons and return the index of the pressed one."""
    for i, button in enumerate(buttons):
        if not button.value:  # Button pressed (active low)
            return i
    return None  # No button pressed


def send_serial_data():
    """Send data over USB serial in JSON format."""
    global app_volumes
    if serial and serial.connected:
        serial.write(f"{app_volumes}\n".encode("utf-8"))


def wait_for_start_signal():
    """Wait for a 'start' command and initialize app volumes."""
    global app_volumes
    if serial and serial.connected:
        print("Waiting for start signal...")
        while True:
            if serial.in_waiting > 0:
                command = serial.readline().decode('utf-8').strip()
                if command.lower().startswith("start"):
                    # Parse initialization volumes from the command
                    try:
                        app_volumes = eval(command[5:])  # Extract volumes after 'start'
                        if len(app_volumes) != 6:
                            raise ValueError("Expected exactly 6 volume values.")
                        print(f"Start signal received. Initialized volumes: {app_volumes}")
                        return
                    except Exception as e:
                        print(f"Error parsing volumes: {e}")
                        print("Retrying...")


# Wait for the start signal and initialize volumes
wait_for_start_signal()

# Main Loop
while True:
    # Read the currently active button
    new_app = read_buttons()

    # If the active app changes, update potentiometer value
    if new_app != current_app and new_app is not None:
        current_app = new_app
        set_potentiometer_to_app_value(current_app)
        print(f"Switched to app {current_app}. Potentiometer set to {pot_value}.")

    # Read potentiometer value
    pot_value = read_potentiometer()

    # Only send data if the app or pot value changes
    if current_app != last_app or pot_value != last_pot_value:
        send_serial_data()
        last_app = current_app
        last_pot_value = pot_value

    time.sleep(0.1)  # Avoid flooding the serial connection
