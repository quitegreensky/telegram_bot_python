import requests
import time
import json
import threading


class TelegramBot:
    def __init__(self, token, db_file, auto_help=True) -> None:
        self.token = token
        self.db_file = db_file
        self.commands = []
        self._offset = 0

        self.auto_help=auto_help
        if self.auto_help:
            self.add_command("/help", self._auto_help_obj)

    def add_command(self, text: str, command: object, args: list = []) -> bool:
        self.commands.append([text, command, args])

    def save_js(self, dic):
        try:
            with open(self.db_file, "wt") as json_file:
                json.dump(dic, json_file)
        except Exception:
            return False
        return True

    def load_js(self):
        try:
            with open(self.db_file) as json_file:
                data = json.load(json_file)
        except Exception:
            data = {}
            with open(self.db_file, "wt") as json_file:
                json.dump(data, json_file)
        return data

    def add_new_id(self, chat_id):
        if self.is_id_exists(chat_id):
            return False
        content = self.load_js()
        content[chat_id] = {"last_update": None}
        self.save_js(content)
        return True

    def id_last_update(self, chat_id, _update_id=None):
        content = self.load_js()
        if not _update_id:
            return content[chat_id]["last_update"]
        content[chat_id]["last_update"] = _update_id
        self.save_js(content)
        return True

    def all_chat_ids(self):
        content = self.load_js()
        return content.keys()

    def is_id_exists(self, chat_id):
        content = self.load_js()
        for line in content.keys():
            if line==str(chat_id):
                return True
        return False

    def send_message(self, chat_id, text):
        message_url = f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={chat_id}&text={text}"
        req = requests.get(message_url)
        if req.status_code!=200:
            return
        return True

    def get_latest_chat_id(self, results):
        _latest = -1
        for res in results:
            chat_id = int(res["update_id"])
            if chat_id>_latest:
                _latest = chat_id
        return _latest

    def get_chat_id_from_results(self, results, chat_id):
        for res in results:
            _chat_id = int(res["update_id"])
            if _chat_id==chat_id:
                return res

    def update(self, update:list=None):
        results = update
        if not results:
            update_url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            req = requests.get(update_url)
            if req.status_code!=200:
                return
            results = req.json()["result"]
            if not results:
                return
        else:
            results = [update]

        last_chat_id = self.get_latest_chat_id(results)
        if last_chat_id <= self._offset and self._offset!=0:
            return
        self._offset = last_chat_id
        last_message = self.get_chat_id_from_results(results, self._offset)
        chat_id = str(last_message["message"]["chat"]["id"])
        update_id =last_message["update_id"]
        sender = last_message["message"]["from"]["first_name"]
        sender_is_bot = last_message["message"]["from"]["is_bot"]
        sender_text = last_message["message"]["text"]

        if sender_is_bot:
            return

        if self.is_id_exists(chat_id):
            user_update_id = self.id_last_update(chat_id)
            if user_update_id:
                if update_id<=user_update_id:
                    # already done
                    return
            self.id_last_update(chat_id, update_id)
        elif sender_text=="/start":
            self.add_new_id(chat_id)
            self.send_message(chat_id, f"Welcome {sender}. Press /help to see commands")
            self.id_last_update(chat_id, update_id)
            return
        else:
            return

        for _command in self.commands:
            cmd_text = _command[0]
            cmd_obj = _command[1]
            cmd_args = _command[2]
            if sender_text.startswith(cmd_text):
                _command_arg = sender_text[len(cmd_text)+1:]
                cmd_obj(chat_id, _command_arg, *cmd_args)

    def _auto_help_obj(self, chat_id, cmd):
        msg = ""
        for _command in self.commands:
            cmd_text = _command[0]
            if cmd_text=="/help":
                continue
            msg+=f"{cmd_text}\n"
        self.send_message(chat_id, msg)

    def run_bot(self, update_interval=1):
        self.logger("Bot started...")
        def _run_bot():
            while True:
                self.update()
                time.sleep(update_interval)
        _thread = threading.Thread(target=_run_bot)
        _thread.start()

    def logger(self, *args):
        print(*args)

    def broadcast_message(self, text):
        for _id in self.all_chat_ids():
            self.send_message(_id, text)

    def setWebhook(self, url_endpoint):
        update_url = f"https://api.telegram.org/bot{self.token}/setWebhook?url={url_endpoint}"
        req = requests.get(update_url)
        if req.status_code!=200:
            return False
        answer = req.json()
        return answer["result"]

    def deleteWebhook(self):
        update_url = f"https://api.telegram.org/bot{self.token}/deleteWebhook"
        req = requests.get(update_url)
        if req.status_code!=200:
            raise
        return req.text

# if __name__=="__main__":
#     bot = TelegramBot("1637954061:AAEDpLDQ0y4M5cQUXICkUR_0HyvYJSW7RTo", "idxs.json")
#     def help_func(chat_id, *args):
#         bot.send_message(chat_id, "help")
#     bot.add_command("/help", help_func)
#     bot.run_bot()