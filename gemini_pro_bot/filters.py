import os
from telegram import Update
from telegram.ext.filters import UpdateFilter
from dotenv import load_dotenv

load_dotenv()

AUTHORIZED_USERS = [i.strip() for i in os.getenv("AUTHORIZED_USERS", "").split(",") if i.strip()]
class AuthorizedUserFilter(UpdateFilter):
    def filter(self, update: Update):
        if not AUTHORIZED_USERS:
            return True
        return update.message.from_user.username in AUTHORIZED_USERS or str(update.message.from_user.id) in AUTHORIZED_USERS