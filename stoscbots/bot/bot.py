from datetime import datetime
from pyrogram import Client
import os

client = Client(session_name="stoscbot", bot_token=os.environ.get('STOSC_TELEGRAM_BOT_TOKEN'))

# ----------------------------------------------------------------------------------------------------------------------
# import http.server
# import socketserver
# import os

# from threading import Thread

# Handler=http.server.SimpleHTTPRequestHandler
# with socketserver.TCPServer(("", 8000), Handler) as httpd:
#     print("Serving Dummy site at port", 8000)
#     thread = Thread(target=lambda: httpd.serve_forever,daemon=True)
#     thread.start()

   
# ----------------------------------------------------------------------------------------------------------------------

    
def run():
    client.start_time = datetime.now()
    client.run()