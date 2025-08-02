import asyncio
import time
from serial_comms import SerialHandler
import volume_control

def callback(call):
    print(call)

app_names = ["Spotify.exe", "Discord.exe", "opera.exe", "vlc.exe", "notepad.exe", "zoom.exe"]
app_volumes = [40, 100, 20, 50, 50, 50]

comms = SerialHandler(volumes=app_volumes, callback=callback)
controller = volume_control.VolumeController(serial_handler=comms, app_names=app_names, callback=callback)

async def innit():
    # Initialize Serial Communication
    while True:
        if await comms.connect():
            comms.start_thread()
            break

if __name__ == "__main__":

    asyncio.run(innit())

    controller.running = True
    controller.volume_loop()

