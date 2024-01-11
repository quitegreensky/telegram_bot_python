from telegram_bot_python.telegram_bot import TelegramBot

token = "mytoken"

# initializing bot
mybot = TelegramBot(token, "users.json", True)

# defining a callback object for /hello command
def hello_callback(chat_id, cmd):
    mybot.send_message(chat_id, "hello")

def regular_message_handler(*args):
    text, photo = args
    if photo:
        photo_path = mybot.get_file_path(photo)
        mybot.download_file(photo_path, "photo.jpg")
    print(text)

# binding hello_callback object to /hello command
mybot.add_command("/hello", hello_callback)
mybot.add_handler(regular_message_handler)

if __name__=="__main__":
    mybot.run_bot(5)
