import random


class MessageEncryption:
    def __init__(self, key: int):
        self.secret_key = key

    def encryptor(self, message: str) -> str:
        """Шифрует сообщение ключом secret_key"""
        return "".join([chr(ord(message[el]) ^ self.secret_key) for el in range(len(message))])

    def encrypt_message(self, msg: dict) -> dict:
        """Шифрует сообщение ключом secret_key"""
        data = msg.copy()
        for k, v in data.items():
            data[k] = self.encryptor(v)
        return data




class DHKeyExchange:
    def __init__(self, a: int, p: int, g: int):
        self.private_key = a  # приватный ключ
        self.pub_key1 = p     # публичный ключ
        self.pub_key2 = g     # публичный ключ


    def check_pub_sert(self, key):
        """Проверка публичного ключа, хранящегося на сервере,
        на соответствие ключу, переданному клиентом """
        with open('sert.txt', 'r') as f:
            keys = f.readlines()
            for el in keys:
                if key == el:
                    return True
                else:
                    return False

    @property
    def partial_key(self):
        """Возвращает частичный ключ"""
        return self.pub_key2 ** self.private_key % self.pub_key1

    def generate_full_key(self, partial_key: int):
        """Возвращает полный приватный ключ"""
        return partial_key ** self.private_key % self.pub_key1

    @property
    def auth_keys(self):
        """Получение элементов для передачи на сторону сервера"""
        return self.pub_key1, self.pub_key2, self.partial_key