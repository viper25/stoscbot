import os
from datetime import datetime
from pyrogram import Client

test_mode = True
mode = os.environ.get("MODE")
if mode == "PRO":
    test_mode = False

app = Client("STOSCBOT_Laptop", plugins=dict(root="plugins"), test_mode=test_mode)


def run():
    app.start_time = datetime.now()
    print(f"Version: {app.APP_VERSION} on {app.SYSTEM_VERSION}")
    app.run()
