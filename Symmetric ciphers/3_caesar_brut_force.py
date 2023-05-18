from collections import Counter


def caesar_decrypt_without_key(ciphertext):
    # частотный анализ
    freqs = Counter(ciphertext)
    # самый частый символ
    most_common = freqs.most_common(1)[0][0]
    # предполагаемый ключ (берем пробел как самый часто встречающийся символ)
    key = (ord(most_common) - ord(' ')) % 65536
    # восстанавливаем исходный текст
    decrypted_text = ''
    for char in ciphertext:
        # Определяем смещение для каждого символа
        shift = (ord(char) - key) % 65536
        # Применяем смещение к символу
        decrypted_char = chr(shift)
        decrypted_text += decrypted_char
    return decrypted_text


def main():
    encrypted_text_test = 'KHOOR#ZRUOG$#Khoor#p|#ghdu#iulhqg$'
    decrypted_text_test = caesar_decrypt_without_key(encrypted_text_test)
    print("Расшифрованный текст:", decrypted_text_test)


if __name__ == "__main__":
    main()


