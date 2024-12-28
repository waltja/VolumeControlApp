import board
import digitalio
import analogio
import usb_cdc
import time

app_volumes = []
set_point = 0

# Define the Fader potentiometer (slide potentiometer motor position)
fader_potentiometer = analogio.AnalogIn(board.A0)

# Define Fader Motor
fader_motor = digitalio.DigitalInOut(board.D5)
fader_motor.direction = digitalio.Direction.OUTPUT

def read_fader():
    """Read and scale the potentiometer value (0-255)."""
    return int((fader_potentiometer.value / 65535) * 255)

def set_fader_to_app(app_index):
    """Simulate setting the potentiometer value to the app's stored volume."""
    global set_point
    if app_index is not None:
        set_point = app_volumes[app_index]


switch_wait_time = 5
last_switch = 0
app = 0
while True:
    now = time.monotonic()

    if now - last_switch > switch_wait_time:
        set_fader_to_app(app)
        if app < 5:
            app += 1
        else:
            app = 0

    if read_fader() != set_point:
        pass # set output based on position + distance (PID loop)



