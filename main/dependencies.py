from main.encrypt_info import CreateEncrypt, CreateHash
from database.task import AddDatabase, AddLogger

def get_hasher():
    return CreateHash()

def get_encrypt():
    return CreateEncrypt()

def get_db():
    return AddDatabase()

def get_log():
    return AddLogger()
