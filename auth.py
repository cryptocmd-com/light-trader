from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash


hashed_passwords = {}


auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if (username in hashed_passwords and
            check_password_hash(
                hashed_passwords.get(username), password)):
        return username


def setup_auth(cleartext_passwords: dict):
    global hashed_passwords
    hashed_passwords = {
        username: generate_password_hash(password)
        for username, password in cleartext_passwords.items()
    }
    return auth
