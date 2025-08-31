import threading
import time
from pycaw.pycaw import AudioUtilities


class VolumeController:
    def __init__(self, serial_handler=None, app_names=None, callback=None):
        self.sessions = AudioUtilities.GetAllSessions()
        self.running = False
        self.thread = None
        self.serial_handler = serial_handler
        self.app_names = app_names
        self.callback = callback
        self.errors = 0

    def refresh_sessions(self):
        """Refresh the session manager to detect new apps."""
        self.sessions = AudioUtilities.GetAllSessions()

    def set_volume(self, app_name, volume):
        """Set the volume for a specific app."""
        for session in self.sessions:
            if session.Process and session.Process.name() == app_name:
                try:
                    volume_device = session.SimpleAudioVolume
                    volume_device.SetMasterVolume(volume / 100, None)
                    print(f"Set volume for {app_name} to {volume}%")
                    return True
                except Exception as e:
                    print(f"Error setting volume for {app_name}: {e}")
        print(f"App {app_name} not found.")
        if self.errors > 10:
            self.refresh_sessions()
            self.errors = 0
        else:
            self.errors += 1
        return False

    def update_volumes(self, app_volumes):
        """Update volumes for a list of apps."""
        for app_name, volume in zip(self.app_names, app_volumes):
            if not self.set_volume(app_name, volume):
                print(f"Failed to update volume for {app_name}.")
                self.refresh_sessions()

    def start_thread(self):
        """Begins the thread for func 'volume_loop' """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.volume_loop, daemon=True)
            self.thread.start()

    def stop_thread(self):
        """Ends the thread for func 'volume_loop' """
        self.running = False
        if self.thread:
            self.thread.join()

    # Main loop to process volume updates
    def volume_loop(self):
        """Continuously checks for new data from serial_comm and updates app volumes."""
        app_volumes = self.serial_handler.volumes
        self.update_volumes(app_volumes)
        while self.running:
            # Check for incoming serial data
            if app_volumes != self.serial_handler.volumes:
                try:
                    for ax, app in enumerate(self.app_names):
                        if app_volumes[ax] is not self.serial_handler.volumes[ax]:
                            app_volumes[ax] = self.serial_handler.volumes[ax]
                            self.set_volume(app, app_volumes[ax])
                except Exception as e:
                    self.callback(f"Error updating serial data: {e}")
            time.sleep(0.01)  # Small delay to prevent busy-waiting

