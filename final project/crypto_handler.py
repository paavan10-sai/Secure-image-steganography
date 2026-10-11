
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256, HMAC
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def derive_keys(password, salt=None):
    if not password:
        raise ValueError("Password cannot be empty.")

    if salt is None:
        salt = get_random_bytes(16)

    password_bytes = password.encode("utf-8")

    master_key = PBKDF2(
        password_bytes,
        salt,
        dkLen=32,
        count=200_000,
        hmac_hash_module=SHA256
    )

    aes_key = SHA256.new(master_key + b"AES-v1").digest()
    hmac_key = SHA256.new(master_key + b"HMAC-v1").digest()

    embedding_master = PBKDF2(
        password_bytes,
        b"secure-stego-position-v1",
        dkLen=32,
        count=100_000,
        hmac_hash_module=SHA256
    )

    embedding_key = SHA256.new(
        embedding_master + b"TEXTURE-POSITION-v1"
    ).digest()

    return aes_key, hmac_key, embedding_key


def encrypt_message(message, aes_key):
    if not isinstance(message, str) or not message:
        raise ValueError("Message cannot be empty.")

    iv = get_random_bytes(16)
    data = message.encode("utf-8")

    padding = 16 - len(data) % 16
    data += bytes([padding]) * padding

    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return iv, cipher.encrypt(data)


def decrypt_message(iv, ciphertext, aes_key):
    if len(iv) != 16 or not ciphertext or len(ciphertext) % 16:
        raise ValueError("Invalid encrypted payload.")

    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    data = cipher.decrypt(ciphertext)

    padding = data[-1]

    if not 1 <= padding <= 16:
        raise ValueError("Incorrect password or corrupted payload.")

    if data[-padding:] != bytes([padding]) * padding:
        raise ValueError("Incorrect password or corrupted payload.")

    return data[:-padding].decode("utf-8")


def generate_hmac(data, hmac_key):
    h = HMAC.new(hmac_key, digestmod=SHA256)
    h.update(data)
    return h.digest()


def verify_hmac(data, received_hmac, hmac_key):
    h = HMAC.new(hmac_key, digestmod=SHA256)
    h.update(data)

    try:
        h.verify(received_hmac)
        return True
    except ValueError:
        return False