
from cryptography.fernet import Fernet

from app.core.config import settings

cipher = Fernet(settings.KEY)


class EncryptManager():
    def create_encrypt(self, secret):
        secret_hash = cipher.encrypt(secret.encode()).decode()
        return secret_hash

    def encode_encrypt(self, secret):
        original_secret = cipher.decrypt(secret).decode()
        return original_secret
