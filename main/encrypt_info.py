import os 

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from passlib.hash import ldap_pbkdf2_sha256
import toml

class CreateHash():
    
    def create_hash(self, passphrase):
        pass_hash = ldap_pbkdf2_sha256.hash(passphrase)
        return pass_hash
    
config_path = os.environ.get('CONFIG_PATH', 'config.toml')
with open(config_path) as f:  
    config = toml.load(f)
encryption_key = os.environ.get('ENCRIPTION_KEY', config['KEY'])
cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

class CreateEncrypt():
    

    def create_encrypt(self, secret):
        secret_hash = cipher.encrypt(secret.encode()).decode()
        return secret_hash



