import secrets


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_short_code(length: int = 7) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
