import tkinter as tk
import ttkbootstrap as boot
import threading
import os
import json
import time
import requests

from pynetgear import Netgear
from tkinter import messagebox
from io import BytesIO
from PIL import Image, ImageTk


def get_theme():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)
        if "theme" in config:
            return config["theme"]
        else:
            return "flatly"
    return "flatly"


class App(boot.Window):
    def __init__(self):
        super().__init__(title="Netgear Assistant")
        self.geometry("425x400")
        self.resizable(False, False)
        boot.Style(theme=get_theme())

        self.session = None
        self.create_widgets()
        self.create_menu()

    def create_widgets(self):

        self.entry = boot.Entry(self, width=52)

        if self.get_admin_password():
            self.entry.insert(0, self.get_admin_password())
        else:
            self.entry.insert(0, "Enter your admin password")

        self.entry.grid(row=0, column=0, padx=10, pady=10)

        self.button = boot.Button(
            self,
            text="Login",
            bootstyle="success",
            command=threading.Thread(target=self.login, daemon=True).start,
        )
        self.button.grid(row=0, column=1, padx=10, pady=10)

        self.label = boot.Label(self, text="Attached Devices")
        self.label.grid(row=1, column=0, padx=10, sticky="w")

        self.tree = boot.Treeview(self)
        self.tree["columns"] = ("name", "ip")
        self.tree.column("#0", width=0, stretch="no")
        self.tree.column("name", anchor=boot.CENTER)
        self.tree.column("ip", anchor=boot.CENTER)
        self.tree.heading("name", text="Name", anchor=boot.CENTER)
        self.tree.heading("ip", text="IP Address", anchor=boot.CENTER)
        self.tree.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.reboot_button = boot.Button(
            self,
            text="Reboot Router",
            bootstyle="danger",
            command=threading.Thread(target=self.reboot_router, daemon=True).start,
        )
        self.reboot_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.status_var = tk.StringVar()
        self.status_var.set("Status:    Not Connected")
        self.status = boot.Label(self, textvariable=self.status_var)
        self.status.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    def create_menu(self):
        self.menu = boot.Menu(self)
        self.file_menu = boot.Menu(self.menu, tearoff=0)
        self.about_menu = boot.Menu(self.menu, tearoff=0)

        self.file_menu.add_command(
            label="Exit",
            command=self.destroy,
        )
        self.menu.add_cascade(label="File", menu=self.file_menu)

        self.about_menu.add_command(label="Router Info", command=self.get_info)
        self.about_menu.add_command(label="System Info", command=self.system_info)
        self.about_menu.add_command(
            label="Speed Test",
            command=threading.Thread(target=self.speed_test, daemon=True).start,
        )

        self.about_menu.add_separator()
        self.about_menu.add_command(
            label="Check Firmware Update",
            command=threading.Thread(
                target=self.check_firmware_update, daemon=True
            ).start,
        )

        self.menu.add_cascade(label="Device", menu=self.about_menu)

        self.theme_menu = boot.Menu(self.menu, tearoff=0)
        self.theme_menu.add_command(
            label="Default",
            command=lambda: self.set_theme("flatly"),
        )
        self.theme_menu.add_command(
            label="Darkly",
            command=lambda: self.set_theme("darkly"),
        )
        self.theme_menu.add_command(
            label="Superhero",
            command=lambda: self.set_theme("superhero"),
        )
        self.theme_menu.add_command(
            label="Vapor",
            command=lambda: self.set_theme("vapor"),
        )
        self.theme_menu.add_command(
            label="Solar",
            command=lambda: self.set_theme("solar"),
        )

        self.menu.add_cascade(label="Theme", menu=self.theme_menu)
        self.config(menu=self.menu)

    def set_theme(self, theme):
        if not os.path.exists("config.json"):
            messagebox.showerror(
                "Error",
                "Configuration file not found, please login to create one",
            )
            return
        else:
            boot.Style().theme_use(theme)
            with open("config.json", "r") as f:
                config = json.load(f)
            config["theme"] = theme
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

    def login(self):
        self.status_var.set("Logging in...")
        netgear = Netgear(password=self.entry.get())
        login = netgear.login()
        if login:
            self.status_var.set("Logged in successfully")
            self.session = netgear

            self.entry.config(state="disabled")
            self.button.config(state="disabled")

            self.status_var.set("Populating attached devices...")
            self.populate_tree()
            self.status_var.set("Connected")

            self.create_config()

        else:
            messagebox.showerror("Error", "Invalid Password")

    def populate_tree(self):
        if self.session:
            devices = self.session.get_attached_devices()
            for device in devices:
                self.tree.insert("", "end", values=(device.name, device.ip))
        else:
            messagebox.showerror("Error", "Not Connected")

    def get_info(self):
        if self.session:
            info = self.session.get_info()
            data = []
            for key, value in info.items():
                data.append(f"{key}: {value}")
            messagebox.showinfo("Info", "\n".join(data))

        else:
            messagebox.showerror("Error", "Not Connected")

    def check_firmware_update(self):
        if self.session:
            update = self.session.check_new_firmware()
            self.status_var.set(f"Checking for firmware update...")
            if update:
                current_version = update["CurrentVersion"]
                new_version = update["NewVersion"]
                release_note = update["ReleaseNote"]

                text = f"Current Version: {current_version}\n New Version: {new_version}\n Release Note: {release_note}"

                messagebox.showinfo("Firmware Update", text)
        else:
            messagebox.showerror("Error", "Not Connected")

    def reboot_router(self):
        if self.session:
            self.status_var.set("Rebooting...")
            self.session.reboot()
            self.status_var.set("Rebooted, wait for router to restart")
        else:
            messagebox.showerror("Error", "Not Connected")

    def test(self):
        self.session.check_ethernet_link

    def create_config(self):
        password = self.entry.get()

        if os.path.exists("config.json"):

            with open("config.json", "r") as f:
                config = json.load(f)

            if config["password"] == password:
                pass
            else:

                with open("config.json", "w") as f:
                    json.dump({"password": password}, f, indent=4)
        else:

            with open("config.json", "w") as f:
                json.dump({"password": password}, f, indent=4)

    def get_admin_password(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
            return config["password"]
        else:
            return None

    def system_info(self):
        if self.session:
            info = self.session.get_system_info()
            data = []
            for key, value in info.items():
                data.append(f"{key}: {value}")
            messagebox.showinfo("Info", "\n".join(data))
        else:
            messagebox.showerror("Error", "Not Connected")

    def speed_test(self):
        if self.session:
            self.speed_test_running = True
            self.after(1000, threading.Thread(target=self.update_speed_test).start)
            self.session.set_speed_test_start()
            results = self.session.get_speed_test_result()

            self.speed_test_window = boot.Toplevel(self)
            self.speed_test_window.title("Speed Test")
            self.speed_test_window.geometry("300x150")
            self.speed_test_window.resizable(False, False)

            self.speed_test_tree = boot.Treeview(self.speed_test_window)
            self.speed_test_tree["columns"] = ("Download", "Upload", "Ping")
            self.speed_test_tree.column("#0", width=0, stretch=boot.NO)
            self.speed_test_tree.column("Download", anchor=boot.CENTER, width=100)
            self.speed_test_tree.column("Upload", anchor=boot.CENTER, width=100)
            self.speed_test_tree.column("Ping", anchor=boot.CENTER, width=100)

            self.speed_test_tree.heading("#0", text="", anchor=boot.CENTER)
            self.speed_test_tree.heading(
                "Download", text="Download", anchor=boot.CENTER
            )
            self.speed_test_tree.heading("Upload", text="Upload", anchor=boot.CENTER)
            self.speed_test_tree.heading("Ping", text="Ping", anchor=boot.CENTER)

            self.copy_button = boot.Button(
                self.speed_test_window,
                text="Copy Results",
                command=lambda: self.copy_to_clipboard(results),
            )
            self.copy_button.pack(side=boot.BOTTOM, pady=5)

            self.speed_test_tree.insert(
                "",
                "end",
                values=(
                    results["NewOOKLADownlinkBandwidth"],
                    results["NewOOKLAUplinkBandwidth"],
                    results["AveragePing"],
                ),
            )
            self.speed_test_tree.pack()

            self.status_var.set("Speed test completed")
            self.speed_test_running = False

        else:
            messagebox.showerror("Error", "Not Connected")

    def copy_to_clipboard(self, results):
        text = f"Download: {results['NewOOKLADownlinkBandwidth']}\nUpload: {results['NewOOKLAUplinkBandwidth']}\nPing: {results['AveragePing']}"
        self.clipboard_clear()
        self.clipboard_append(text)

    def update_speed_test(self):

        count = 0
        while self.speed_test_running:
            self.status_var.set(f"Speed test running... {count} seconds elapsed")
            time.sleep(1)
            count += 1


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()
        exit()
