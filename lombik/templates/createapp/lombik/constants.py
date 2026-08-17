from zoneinfo import available_timezones
from lombik.utils import get_countries

RESET_TOKEN_EXPIRY_MINUTES = 30
PASSWORD_LOCKOUT_ATTEMPTS = 5
PASSWORD_LOCKOUT_MINUTES = 10
USER_STATUSES = ("active", "inactive", "deleted")
USER_ROLES = ("user", "admin", "superuser", "system")
ADMIN_ROLES = ("admin", "superuser")
TOKEN_BYTES = 32
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
IMAGE_COMPRESSION_OVER_BYTES = 2 * 1024 * 1024 # 2MB 
IRREGULAR = {
    "child": "children",
    "person": "people",
    "man": "men",
    "woman": "women",
    "mouse": "mice",
    "goose": "geese",
    "tooth": "teeth",
    "foot": "feet",
    "ox": "oxen",
    "louse": "lice",
    "sheep": "sheep",
    "deer": "deer",
    "fish": "fish",
    "series": "series",
    "species": "species",
    "knife": "knives",
    "wife": "wives",
    "life": "lives",
    "leaf": "leaves",
    "wolf": "wolves",
    "calf": "calves",
    "half": "halves",
    "loaf": "loaves",
    "thief": "thieves",
    "shelf": "shelves",
    "self": "selves",
    "elf": "elves",
    "hero": "heroes",
    "potato": "potatoes",
    "tomato": "tomatoes",
    "echo": "echoes",
    "torpedo": "torpedoes",
    "veto": "vetoes",
    "photo": "photos",
    "piano": "pianos",
    "halo": "halos",
    "memo": "memos",
    "logo": "logos",
    "video": "videos",
    "studio": "studios",
}
TIMEZONES = available_timezones()
COUNTRIES = get_countries()