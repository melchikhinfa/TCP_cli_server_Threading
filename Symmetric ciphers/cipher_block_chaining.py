def simple_encrypt_block(block):
    return ''.join(chr((ord(c) + 1) % 256) for c in block)


def simple_decrypt_block(block):
    return ''.join(chr((ord(c) - 1) % 256) for c in block)


def xor_strings(s1, s2):
    return ''.join(chr(ord(c1) ^ ord(c2)) for c1, c2 in zip(s1, s2))


def cbc_encrypt(text, iv):
    blocks = [text[i:i + 16] for i in range(0, len(text), 16)]
    ciphertext = ''
    prev_ciphertext = iv
    for block in blocks:
        ciphertext_block = simple_encrypt_block(xor_strings(block, prev_ciphertext))
        ciphertext += ciphertext_block
        prev_ciphertext = ciphertext_block
    return ciphertext


def cbc_decrypt(ciphertext, iv):
    blocks = [ciphertext[i:i+16] for i in range(0, len(ciphertext), 16)]
    text = ''
    prev_ciphertext = iv
    for block in blocks:
        plaintext_block = xor_strings(simple_decrypt_block(block), prev_ciphertext)
        text += plaintext_block
        prev_ciphertext = block
    return text

iv = 'acgsagahfjytuedf' * 16
text = 'hello world!' + ' ' * 5
ciphertext = cbc_encrypt(text, iv)
decrypted = cbc_decrypt(ciphertext, iv)

print("Plaintext:", text)
print("Ciphertext:", ciphertext)
print("Decrypted:", decrypted)