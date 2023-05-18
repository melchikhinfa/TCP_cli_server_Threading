def caesar_encrypt(text, key):
    encrypted_text = ""
    for char in text:
        # Определяем смещение для каждого символа
        shift = (ord(char) + key) % 65536
        # Применяем смещение к символу
        encrypted_char = chr(shift)
        encrypted_text += encrypted_char
    return encrypted_text

def caesar_decrypt(encrypted_text, key):
    decrypted_text = ""
    for char in encrypted_text:
        # Определяем смещение для каждого символа
        shift = (ord(char) - key) % 65536
        # Применяем смещение к символу
        decrypted_char = chr(shift)
        decrypted_text += decrypted_char
    return decrypted_text


def main():
    text = "HELLO WORLD! Hello my dear friend!"
    caesar_key = 3

    # Шифрование текста с помощью обобщенного шифра Цезаря
    encrypted_caesar = caesar_encrypt(text, caesar_key)
    print("Зашифрованный текст с помощью шифра Цезаря:", encrypted_caesar)

    # Дешифрование текста, зашифрованного обобщенным шифром Цезаря
    decrypted_caesar = caesar_decrypt(encrypted_caesar, caesar_key)
    print("Расшифрованный текст с помощью шифра Цезаря:", decrypted_caesar)


if __name__ == "__main__":
    main()
