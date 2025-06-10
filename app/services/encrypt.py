
from cryptography.fernet import Fernet

from app.core.config import settings

cipher = Fernet(settings.KEY)


class CreateEncrypt():
    def create_encrypt(self, secret):
        secret_hash = cipher.encrypt(secret.encode()).decode()
        return secret_hash
