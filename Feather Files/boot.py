import usb_cdc
import time


usb_cdc.enable(console=True, data=True)

# Send a reset command
usb_cdc.write(b'reset\n')

# Add a small delay here
time.sleep(1)  # Wait for 1 seconds to allow the PC side to respond and clear its state
