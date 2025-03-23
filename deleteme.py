from app.utils.security_helpers import get_password_hash, verify_password

APP_NAME = "DELETEME"


if __name__ == '__main__':
    password = "abc"

    hash = get_password_hash(password)
    print(hash)

    r = verify_password(password, hash)
    print(r)
    # $2b$12$a9l1wVbjecqw43bP6kDhsOeTAp6we9jwqE17g5ejf6jMOP85kTv5O