def extend_key_to_length(string1, string2):
    if len(string1) >= len(string2):
        return string1[:len(string2)]
    else:
        q, r = divmod(len(string2), len(string1))
        return string1 * q + string1[:r]


def vernam_encrypt_decrypt(text, key):
    encrypted_text = ""
    full_key = extend_key_to_length(key, text)
    if len(full_key) != len(text):
        raise ValueError("Длина ключа должна быть равна длине текста!")
    else:
        for i in range(len(text)):
            char = text[i]
            # Выполняем операцию XOR над символом текста и символом ключа
            encrypted_char = chr(ord(char) ^ ord(full_key[i]))
            encrypted_text += encrypted_char
        return encrypted_text



def main():
    test_key = 'dsfslkfwoeo429msdaqw!@#'
    test_text = 'Hello, World!'
    encrypted_text = vernam_encrypt_decrypt(test_text, test_key)
    decrypted_text = vernam_encrypt_decrypt(encrypted_text, test_key)
    print("Зашифрованный текст:", encrypted_text)
    print("Исходный текст:", decrypted_text)


if __name__ == "__main__":
    main()

