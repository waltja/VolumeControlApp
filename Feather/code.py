import board
import digitalio
import analogio
import touchio
import usb_cdc
import time

# Define the Fader and Touch Sense (slide potentiometer motor position)
fader = analogio.AnalogIn(board.A0)
touch = touchio.TouchIn(board.A3)

# Define Fader Motor
motor_fwd = digitalio.DigitalInOut(board.SDA)
motor_fwd.direction = digitalio.Direction.OUTPUT
motor_fwd.value = False
motor_bwd = digitalio.DigitalInOut(board.SCL)
motor_bwd.direction = digitalio.Direction.OUTPUT
motor_bwd.value = False

# Define buttons (6 switches) and setup as inputs with pull-up resistors
buttons = [
    digitalio.DigitalInOut(board.D5),
    digitalio.DigitalInOut(board.D6),
    digitalio.DigitalInOut(board.D9),
    digitalio.DigitalInOut(board.D10),
    digitalio.DigitalInOut(board.D11),
    digitalio.DigitalInOut(board.D12)
]
for button in buttons:
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP

# Define button LEDs and setup as outputs with pull-down resistors
button_leds = [
    digitalio.DigitalInOut(board.D4),
    digitalio.DigitalInOut(board.TX),
    digitalio.DigitalInOut(board.RX),
    digitalio.DigitalInOut(board.MISO),
    digitalio.DigitalInOut(board.MOSI),
    digitalio.DigitalInOut(board.SCK)
]
for led in button_leds:
    led.direction = digitalio.Direction.OUTPUT
    led.value = False

# Serial communication setup
serial = usb_cdc.data

# Default volumes for each app
app_volumes = [20, 30, 40, 50, 60, 70]

# Track the current app and fader setpoint
current_app = 3
button_leds[current_app].value = True
set_point = 50
set_low = 4
set_high = 95
set_var = 1

def read_fader():
    """Read and scale the fader value (0-255)."""
    return int((fader.value/65535 - set_low/100) * (100 + set_low + (100 - set_high)))

def motor_forward():
    motor_fwd.value = True
    motor_bwd.value = False

def motor_backward():
    motor_fwd.value = False
    motor_bwd.value = True

def motor_stop():
    motor_fwd.value = motor_bwd.value = False

def read_buttons():
    """Read the state of all buttons and return the index of the pressed one."""
    for i, button in enumerate(buttons):
        if button.value:  # Button pressed (active low)
            return i
    return None  # No button pressed

def send_volumes():
    """Send current app_volumes over serial"""
    global app_volumes
    if serial and serial.connected:
        serial.reset_output_buffer()
        serial.write(f"{app_volumes}sack\r\n".encode())

def send_data(data):
    if serial and serial.connected:
        serial.reset_output_buffer()
        serial.write(f"{data}\r\n".encode())


def innit():
    """Wait for a 'start' command and initialize app volumes."""
    global app_volumes, serial
    while True:
        if serial and serial.connected:
            print("Waiting for start signal...")
            while True:
                if serial.in_waiting > 0:
                    command = serial.readline().decode().strip()

                    # Parse initialization volumes from the command
                    try:
                        app_volumes = eval(command)  # Extract volumes
                        if len(app_volumes) != 6:
                            raise ValueError(f"Expected 6 volume values, got {len(app_volumes)}")
                        print(f"Start signal received. Initialized volumes: {app_volumes}")
                        send_volumes()
                        return
                    except Exception as e:
                        print(f"Error parsing volumes: {e}")
                        print("Retrying...")
                else:
                    send_data('ack')
                time.sleep(0.5)
        else:
            print('No serial connection')
            print("Retrying...\n")
            time.sleep(5)
            serial = usb_cdc.data


"""----------------------------------------------------------------------------------------"""

"""
# Wait for the start signal and initialize volumes
innit()

fast_interval = 0.01
slow_interval = 0.1
last_fast = last_slow = time.monotonic()

# ----Main Loop----
while True:

    now = time.monotonic()

    # FAST TASKS
    if now - last_fast >= fast_interval:
        last_fast = now

        # Read buttons and if any are active and new, reset set_point and update current_app
        for idx, button in enumerate(buttons):
            if not button.value:  # pressed (active low)
                if idx != current_app:
                    # switch LED
                    button_leds[current_app].value = False
                    button_leds[idx].value = True
                    current_app = idx
                    set_point = app_volumes[current_app]
                    print(f"App→{current_app}, set_point={set_point}")
                break

        # If current position is not set_point, set motor to move towards
        pos = read_fader()
        if not touch.value:
            if pos < set_point:
                motor_forward()
            elif pos > set_point:
                motor_backward()
        else:
            motor_stop()

    # SLOW TASKS
    if now - last_slow >= slow_interval:
        last_slow = now

        pos = read_fader() + set_low
        # if user moved the fader off the motor’s target:
        if pos != set_point:
            set_point = pos
            app_volumes[current_app] = pos
            # send updated list back to PC
            if serial and serial.connected:
                send_volumes()
            print("Sent new volumes:", app_volumes)
    
    time.sleep(0.001)
"""


while True:
    # if not serial.connected:
    #     print('Connections lost, retrying\n')
    #     innit()
    # # send_volumes()
    # # print('Sent Periodic')
    print()
    print(str(read_fader()))
    # print(str(touch.value))
    print(read_buttons())
    # for button in buttons:
    #     print(str(button.value))
    print()
    # time.sleep(0.5)  # Avoid flooding the serial connection

    new = read_buttons()
    if new != current_app and new is not None:
        # switch LED
        button_leds[current_app].value = False
        button_leds[new].value = True
        current_app = new
        set_point = app_volumes[current_app]
        print(f"App→{current_app}, set_point={set_point}")

    pos = read_fader()
    if not touch.value:
        if pos+set_var < set_point:
            motor_forward()
        elif pos-set_var > set_point:
            motor_backward()
        else:
            motor_stop()
    else:
        motor_stop()
