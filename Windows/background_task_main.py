import asyncio
import time
from serial_comms import SerialHandler
import volume_control

def callback(call):
    print(call)


app_names = ["Spotify.exe", "Discord.exe", "opera.exe", "vlc.exe", "notepad.exe", "zoom.exe"]
app_volumes = [40, 100, 20, 100, 100, 100]

comms = SerialHandler(callback=callback, volumes=app_volumes)
controller = volume_control.VolumeController()

async def innit_comms(comms):
    # Initialize Serial Communication
    while True:
        if await comms.connect():
            comms.start_thread()
            break

if __name__ == "__main__":

    asyncio.run(innit_comms(comms))

    # controller.volume_control_loop(comms, app_names, callback=callback)

    while True:
        if not comms.running:
            comms.stop_thread()
            print('Comms thread exited, restarting')
        if not controller.running:
            comms.stop_thread()
            print('Comms thread exited, restarting')

