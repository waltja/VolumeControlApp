import json
import sys
from tkinter import Tk, Label, Entry, Button, Frame, Listbox, SINGLE, Toplevel, messagebox

from PIL.ImageStat import Global


class AppUI:
    def __init__(self, serial_handler):
        self.serial_handler = serial_handler
        self.apps = {}  # App configurations: {"app_name.exe": volume}
        self.load_app_data()
        self.update_serial_handler()  # Ensure apps data is sent on initialization

    def load_app_data(self):
        """Loads app data from a file."""
        try:
            with open("app_config.json", "r") as file:
                self.apps = json.load(file)
        except FileNotFoundError:
            print("No configuration file found. Starting fresh.")
        except Exception as e:
            print(f"Error loading app data: {e}")

    def save_app_data(self):
        """Saves app data to a file."""
        try:
            with open("app_config.json", "w") as file:
                json.dump(self.apps, file)
        except Exception as e:
            print(f"Error saving app data: {e}")

    def update_serial_handler(self):
        """Send updated app list to the serial handler."""
        if self.serial_handler:
            self.serial_handler.send_serial_data(str(self.apps))
        print(f"App data sent to serial handler: {self.apps}")
        self.update_serial_output(f"Sent app data: {self.apps}")

    def update_serial_output(self, message):
        """Update the serial output listbox."""
        if hasattr(self, 'serial_output') and self.serial_output:
            self.serial_output.insert("end", message)
            self.serial_output.yview("end")  # Scroll to the bottom

    def add_app(self, app_name_entry, app_volume_entry, app_frame, add_window):
        """Adds a new app to the app list."""
        app_name = app_name_entry.get().strip()
        try:
            volume = int(app_volume_entry.get().strip())
            if 0 <= volume <= 100:
                self.apps[app_name] = volume
                self.save_app_data()
                self.display_apps_in_listbox(app_frame)
                self.update_serial_handler()
                add_window.destroy()  # Close the add app window
            else:
                print("Volume must be between 0 and 100.")
        except ValueError:
            print("Invalid volume. Please enter a number between 0 and 100.")

    def remove_app(self, app_name, app_frame):
        """Removes the app from the list."""
        del self.apps[app_name]
        self.save_app_data()
        self.display_apps_in_listbox(app_frame)
        self.update_serial_handler()

    def display_apps_in_listbox(self, app_frame):
        """Displays all apps in the listbox with remove buttons."""
        for widget in app_frame.winfo_children():
            widget.destroy()  # Clear previous items

        for app_name, volume in self.apps.items():
            app_row = Frame(app_frame, bd=2, relief="solid", padx=5, pady=5)  # Border around each row
            app_row.pack(fill="x", padx=5, pady=5)

            Label(app_row, text=f"{app_name}: {volume}%", anchor="w").pack(side="left", padx=5)

            remove_button = Button(app_row, text="Remove",
                                   command=lambda app_name=app_name: self.remove_app(app_name, app_frame))
            remove_button.pack(side="right", padx=5)

    def open_add_app_window(self, app_frame):
        """Opens a new window to add an app."""
        add_window = Toplevel()
        add_window.title("Add App")
        add_window.geometry("225x100")  # Set window size

        Label(add_window, text="App Name").grid(row=0, column=0, padx=5, pady=5)
        app_name_entry = Entry(add_window)
        app_name_entry.grid(row=0, column=1, padx=5, pady=5)
        Label(add_window, text="Volume").grid(row=1, column=0, padx=5, pady=5)
        app_volume_entry = Entry(add_window)
        app_volume_entry.grid(row=1, column=1, padx=5, pady=5)

        def add_app_button():
            """Adds app data from entry fields to the main listbox"""
            self.add_app(app_name_entry, app_volume_entry, app_frame, add_window)

        Button(add_window, text="Add", command=add_app_button).grid(row=2, column=1, padx=5, pady=5)

    def open_startup_window(self):
        """Opens a new window to add an app."""
        add_window = Tk()
        add_window.title("Startup")
        add_window.geometry("300x200")  # Set window size

        Label(add_window, text="COMM Ports:").grid(row=0, column=0, padx=5, pady=5)

        ports = list(self.serial_handler.list_comports())
        if ports:
            port_names = [port.device for port in ports]
        else:
            popup = messagebox.showerror(
                "Serial Ports Unavailable",
                f"No active COM ports detected.\n",
            )
            if popup == "ok":
                add_window.destroy()
                sys.exit()

        selected_port = None

        def select(port):
            global selected_port
            selected_port = port

        for port in port_names:
            app_row = Frame(add_window, padx=5, pady=5)  # Border around each row
            Label(app_row, text=f"{port}", anchor="w").pack(side="left", padx=5)

            choose_button = Button(app_row, text="Select",
                                   command=lambda port=port: select(port))
            choose_button.pack(side="right", padx=5)

        def finish():
            global selected_port
            if selected_port is None:
                print('Please select a port to connect to')
            else:
                self.serial_handler.port = selected_port
                add_window.destroy()

        Button(add_window, text="Connect", command=finish).grid(row=2, column=1, padx=5, pady=5)

    def check_serial_connection(self):
        if not self.serial_handler.is_connected():
            ports = list(self.serial_handler.list_comports())
            if ports:
                port_names = [port.device for port in ports]
            else:
                port_names = ['']
            selected_port = messagebox.askquestion(
                "Serial Port Unavailable",
                f"No active COM port detected.\nAvailable ports: {', '.join(port_names)} \n\nRetry?",
            )
            if selected_port == "yes":
                self.serial_handler.connect()

    def run(self):
        """Launches the UI"""
        root = Tk()
        root.title("Volume Controller")
        root.geometry("400x500")  # Set initial window size

        # Configure rows and columns to expand the window size
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=0)
        root.grid_rowconfigure(2, weight=1)
        root.grid_rowconfigure(3, weight=3)

        # Frame for the Listbox and Scrollbar
        app_frame = Frame(root)
        app_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=30, pady=5)

        # Display apps in the frame
        self.display_apps_in_listbox(app_frame)

        # Button to open the add app window
        Button(root, text="Add App", command=lambda: self.open_add_app_window(app_frame)).grid(row=2, column=0,
                                                                                               padx=100,
                                                                                               pady=5)

        # Serial output display
        self.serial_output = Listbox(root, height=15, width=50, selectmode=SINGLE)
        self.serial_output.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=30, pady=5)

        # Check if serial port is open and connected
        self.check_serial_connection()

        # Start the Tkinter event loop
        root.mainloop()
