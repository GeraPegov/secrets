from passlib.hash import ldap_pbkdf2_sha256


class CreateHash():
    def create_hash(self, passphrase):
        pass_hash = ldap_pbkdf2_sha256.hash(passphrase)
        return pass_hash
