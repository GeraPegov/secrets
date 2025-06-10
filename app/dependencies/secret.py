from app.repositories.task import AddDatabase, AddLogger
from app.services.encrypt import CreateEncrypt
from app.services.hash import CreateHash


def get_hasher():
    return CreateHash()


def get_encrypt():
    return CreateEncrypt()


def get_db():
    return AddDatabase()


def get_log():
    return AddLogger()
