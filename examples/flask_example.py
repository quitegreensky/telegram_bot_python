'''
Note: This example won't work on local host. You will need a static ip address or a domain
'''

from flask import Flask, request
from telegram_bot_python.telegram_bot import TelegramBot

server_url = "myserver.com"

# initializing bot
mybot = TelegramBot("mytoken", "users_db.json", auto_help=True)

# introducing our webhook endpoint to telegram servers
mybot.setWebhook(f"{server_url}/webhook")

# defining a callback object for /hello command
def hello_callback(chat_id, cmd):
    mybot.send_message(chat_id, "hello")

# binding hello_callback object to /hello command
mybot.add_command("/hello", hello_callback)

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    update = request.json
    mybot.update(update)
    return "done"

if __name__=="__main__":
    app.run()