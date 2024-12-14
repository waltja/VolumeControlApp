import serial_comms
import volume_control


def callback(data):
    print(data)


def run_background_task():
    app_names = ["spotify.exe", "discord.exe", "opera.exe", "vlc.exe", "notepad.exe", "zoom.exe"]
    app_volumes = [20, 100, 20, 100, 100, 100]

    comms = serial_comms.SerialHandler(callback=callback)
    controller = volume_control.VolumeController()

    # Initialize Serial Communication
    while True:
        if comms.connect_to_feather(app_volumes):
            comms.start()
            break

    # Start Volume Control
    controller.volume_control_loop(comms, app_names)


if __name__ == "__main__":
    run_background_task()
