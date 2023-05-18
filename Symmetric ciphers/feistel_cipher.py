def feistel_round(left, right, round_key):
    # Функция "f" может быть любой функцией, которая преобразует данные
    # В этом примере она просто XOR'ит данные с ключом раунда
    def f(data, key):
        return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(data, key))
    return right, xor_strings(left, f(right, round_key))


def feistel_encrypt(input_block, round_keys):
    # Разбиваем входные данные на две половины
    left, right = input_block[:len(input_block) // 2], input_block[len(input_block) // 2:]
    # Выполняем раунды сети Фейстеля
    for round_key in round_keys:
        left, right = feistel_round(left, right, round_key)
    # Возвращаем результат
    return right + left


def feistel_decrypt(input_block, round_keys):
    left, right = input_block[:len(input_block) // 2], input_block[len(input_block) // 2:]
    # Выполняем раунды сети Фейстеля в обратном порядке
    for round_key in reversed(round_keys):
        left, right = feistel_round(left, right, round_key)
    return right + left


def xor_strings(s1, s2):
    return ''.join(chr(ord(c1) ^ ord(c2)) for c1, c2 in zip(s1, s2))

def main():
    # Тестовые данные
    input_block = 'Hello world!' + ' ' * 5
    round_keys = ['key1key1', 'key2key2', 'key3key3', 'key4key4']
    output = feistel_encrypt(input_block, round_keys)
    print("Зашифрованный текст:", output)
    print(feistel_decrypt(output, round_keys))


if __name__ == "__main__":
    main()