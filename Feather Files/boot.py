import usb_cdc
import time

if usb_cdc.data:
    usb_cdc.enable(data=True)

    # Send a reset command
    usb_cdc.write(b'reset\n')

    # Add a small delay here
    time.sleep(2)  # Wait for 2 seconds to allow the PC side to respond and clear its state
