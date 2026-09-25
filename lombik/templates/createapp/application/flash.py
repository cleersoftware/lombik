from flask import flash


class Flash:
    _categories = {
        "bug": {
            "icon": "bug-outline",
            "icon_class": "text-amber-400",
        },
        "error": {
            "icon": "alert-circle-outline",
            "icon_class": "text-red-400",
        },
        "warning": {
            "icon": "warning-outline",
            "icon_class": "text-amber-400",
        },
        "ok": {
            "icon": "checkmark-circle-outline",
            "icon_class": "text-green-400",
        },
        "safe": {
            "icon": "shield-checkmark-outline",
            "icon_class": "text-teal-400",
        },
        "win": {
            "icon": "medal-outline",
            "icon_class": "text-sky-400",
        },
        "timeout": {
            "icon": "alarm-outline",
            "icon_class": "text-amber-400",
        },
        "wait": {
            "icon": "hourglass-outline",
            "icon_class": "text-amber-400",
        },
        "announce": {
            "icon": "megaphone-outline",
            "icon_class": "text-teal-400",
        },
        "upload": {
            "icon": "cloud-upload-outline",
            "icon_class": "text-white",
        },
        "save": {
            "icon": "save-outline",
            "icon_class": "text-sky-400",
        },
        "delete": {
            "icon": "trash-outline",
            "icon_class": "text-red-400",
        },
        "thumbsup": {
            "icon": "thumbs-up-outline",
            "icon_class": "text-green-400",
        },
        "thumbsdown": {
            "icon": "thumbs-down-outline",
            "icon_class": "text-red-400",
        },
        "chat": {
            "icon": "chatbubble-ellipses-outline",
            "icon_class": "text-sky-400",
        },
    }

    @classmethod
    def _send(cls, message: str, category: str):
        if category not in cls._categories:
            raise ValueError(f"Unknown flash category '{category}'.")

        flash(
            {
                "text": message,
                "icon": cls._categories[category]["icon"],
                "icon_class": cls._categories[category]["icon_class"],
            },
            category,
        )

    @classmethod
    def bug(cls, message: str):
        cls._send(message, "bug")

    @classmethod
    def error(cls, message: str):
        cls._send(message, "error")

    @classmethod
    def warning(cls, message: str):
        cls._send(message, "warning")

    @classmethod
    def ok(cls, message: str):
        cls._send(message, "ok")

    @classmethod
    def safe(cls, message: str):
        cls._send(message, "safe")

    @classmethod
    def win(cls, message: str):
        cls._send(message, "win")

    @classmethod
    def timeout(cls, message: str):
        cls._send(message, "timeout")

    @classmethod
    def wait(cls, message: str):
        cls._send(message, "wait")

    @classmethod
    def announce(cls, message: str):
        cls._send(message, "announce")

    @classmethod
    def upload(cls, message: str):
        cls._send(message, "upload")

    @classmethod
    def save(cls, message: str):
        cls._send(message, "save")

    @classmethod
    def delete(cls, message: str):
        cls._send(message, "delete")

    @classmethod
    def thumbsup(cls, message: str):
        cls._send(message, "thumbsup")

    @classmethod
    def thumbsdown(cls, message: str):
        cls._send(message, "thumbsdown")

    @classmethod
    def chat(cls, message: str):
        cls._send(message, "chat")