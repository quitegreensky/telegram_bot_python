from telegram_bot_python.telegram_bot import TelegramBot

token = "mytoken"

# initializing bot
mybot = TelegramBot(token, "users.json", True)

# defining a callback object for /hello command
def hello_callback(chat_id, cmd):
    mybot.send_message(chat_id, "hello")

# binding hello_callback object to /hello command
mybot.add_command("/hello", hello_callback)

if __name__=="__main__":
    mybot.run_bot(5)
