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
        self._handler = None # handler for non command messages

        self.auto_help=auto_help
        if self.auto_help:
            self.add_command("/help", self._auto_help_obj)

    def add_command(self, text: str, command: object, args: list = []) -> bool:
        self.commands.append([text, command, args])

    def set_handler(self, _handler: object) -> bool:
        self._handler = _handler

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

    def send_message(self, chat_id, text, inline_keyboard=None):
        """
        keyboard = [
            [{"text": "Button 1", "callback_data": "button_1"}],
            [{"text": "Button 2", "callback_data": "button_2"}]
        ]
        commands:
        switch_inline_query
        switch_inline_query_current_chat
        ]"""
        message_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if inline_keyboard:
            payload["reply_markup"] = json.dumps({"inline_keyboard": inline_keyboard})

        req = requests.post(message_url, json=payload)
        if req.status_code!=200:
            return
        return True

    def send_document(self, chat_id, file_path, caption="", inline_keyboard=None):
        message_url = f"https://api.telegram.org/bot{self.token}/sendDocument"
        files = {
            'document': open(file_path, 'rb')
        }
        data = {
            "chat_id": chat_id,
            "caption": caption
        }
        if inline_keyboard:
            data["reply_markup"] = json.dumps({"inline_keyboard": inline_keyboard})

        req = requests.post(message_url, files=files, data=data)
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
        message_content = last_message["message"]
        chat_id = str(message_content["chat"]["id"])
        update_id =last_message["update_id"]
        sender = message_content["from"]["first_name"]
        sender_is_bot = message_content["from"]["is_bot"]

        photo_id = ""
        if "text" in message_content:
            sender_text = message_content["text"]
        else:
            if "photo" in message_content:
                photo_id = message_content["photo"][-1]["file_id"]
                if "caption" in message_content:
                    sender_text = message_content["caption"]
                else:
                    sender_text = ""

        sender_text = sender_text.strip()
        if sender_text:
            if sender_text[0]=="@":
                sender_text=sender_text.split(" ",1)[-1]

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
                return

        # it's a non command message
        if self._handler:
            self._handler(chat_id, sender_text, photo_id)

    def get_file_path(self, file_id):
        url = f"https://api.telegram.org/bot{self.token}/getFile"
        response = requests.get(url, params={"file_id": file_id})
        file_path = response.json()["result"]["file_path"]
        return file_path

    def download_file(self, file_path, local_filename):
        url = f'https://api.telegram.org/file/bot{self.token}/{file_path}'
        response = requests.get(url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=128):
                f.write(chunk)

    def _auto_help_obj(self, chat_id, cmd):
        msg = ""
        for _command in self.commands:
            cmd_text = _command[0]
            if cmd_text.startswith("/_"): # internal commands
                continue
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
