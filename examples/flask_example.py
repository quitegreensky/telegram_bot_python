'''
Note: This example won't work on local host. You will need a static ip address or a domain
'''

from flask import Flask, request
from telegram_bot_python.telegram_bot import TelegramBot

server_url = "myserver.com"

# initializing bot
mybot = TelegramBot("mytoken", "users_db.json", auto_help=True)

# introducing our webhook endpoint to telegram servers
secret = "mysecret1234"
mybot.setWebhook(f"{server_url}/webhook/{secret}")

# defining a callback object for /hello command
def hello_callback(chat_id, cmd):
    mybot.send_message(chat_id, "hello")

def regular_message_handler(*args):
    chat_id, text, photo = args
    if photo:
        photo_path = mybot.get_file_path(photo)
        mybot.download_file(photo_path, "photo.jpg")
    print(text)

# binding hello_callback object to /hello command
mybot.add_command("/hello", hello_callback)
mybot.set_handler("regular", regular_message_handler)
mybot.activate_handler("regular")

# init menu after adding all commands
mybot.init_menu()

app = Flask(__name__)

@app.route(f"/webhook/{secret}", methods=["GET", "POST"])
def webhook():
    update = request.json
    mybot.update(update)
    return "done"

if __name__=="__main__":
    app.run()