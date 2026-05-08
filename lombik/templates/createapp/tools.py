def genflash(message: str, category: str):
    """
    Accepted categories:
    - bug
    - error
    - warning
    - ok
    - safe
    - win
    - timeout
    - wait
    - announce
    - upload
    - save
    - delete
    - thumbsup
    - thumbsdown
    - chat
    """    

    cats = {
    'bug':     {'icon': 'bug-outline', 'class': 'text-amber-400'},
    'error':   {'icon': 'alert-circle-outline', 'class': 'text-red-400'},
    'warning': {'icon': 'warning-outline', 'class': 'text-amber-400'},
    'ok':      {'icon': 'checkmark-circle-outline', 'class': 'text-green-400'},
    'safe':    {'icon': 'shield-checkmark-outline', 'class': 'text-teal-400'},
    'win':     {'icon': 'medal-outline', 'class': 'text-sky-400'},
    'timeout':     {'icon': 'alarm-outline', 'class': 'text-amber-400'},
    'wait':     {'icon': 'hourglass-outline', 'class': 'text-amber-400'},
    'announce':     {'icon': 'megaphone-outline', 'class': 'text-teal-400'},
    'upload':     {'icon': 'cloud-upload-outline', 'class': 'text-white'},
    'save':     {'icon': 'save-outline', 'class': 'text-sky-400'},
    'delete':     {'icon': 'trash-outline', 'class': 'text-red-400'},
    'thumbsup':     {'icon': 'thumbs-up-outline', 'class': 'text-green-400'},
    'thumbsdown':     {'icon': 'thumbs-down-outline', 'class': 'text-red-400'},
    'chat':     {'icon': 'chatbubble-ellipses-outline', 'class': 'text-sky-400'},
}
    if category not in cats:
        raise ValueError("Invalid category")

    return {
        "text": message,
        "icon": cats[category]['icon'],
        "icon_class": cats[category]['class'],
    }, category