from ui import AppUI
from serial_comms import SerialHandler
from volume_control import VolumeController


def main():
    volume_controller = VolumeController()
    app_ui = AppUI(None)

    def handle_serial_data(data):
        print(f"Serial data received: {data}")
        try:
            app_ui.update_serial_output(data)
            app_volumes = eval(data)
            if isinstance(app_volumes, dict):
                volume_controller.update_volumes(app_volumes)
        except Exception as e:
            print(f"Error parsing serial data: {e}")

    serial_handler = SerialHandler("COM4", 9600, callback=handle_serial_data)
    app_ui.serial_handler = serial_handler

    app_ui.open_startup_window()
    try:
        app_ui.run()
    except KeyboardInterrupt:
        print("Exiting program.")
    # finally:
    #     serial_handler.stop()


if __name__ == "__main__":
    main()
