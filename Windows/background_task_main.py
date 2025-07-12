import time

import serial_comms
import volume_control


def callback(call):
    print(call)


def run_background_task():
    app_names = ["Spotify.exe", "Discord.exe", "opera.exe", "vlc.exe", "notepad.exe", "zoom.exe"]
    app_volumes = [20, 100, 20, 100, 100, 100]

    comms = serial_comms.SerialHandler(callback=callback)
    controller = volume_control.VolumeController()

    # Initialize Serial Communication
    while True:
        if comms.connect(app_volumes):
            print('Yippepepepepepepe')
            comms.start()
            break


    # Start Volume Control
    controller.volume_control_loop(comms, app_names, callback=callback)


from pycaw.api.audioclient import ISimpleAudioVolume

if __name__ == "__main__":
    run_background_task()
