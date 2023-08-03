from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
from gmssl.sm3 import sm3_hash
from gmssl import func
import secrets


# 使用sm3实现的hmac函数
def hmac_sm3_256(key, msg):
    key = bytes(key, 'utf-8')
    msg = bytes(msg, 'utf-8')

    if len(key) > 64:
        key = sm3_hash(func.bytes_to_list(key))
        key = bytes.fromhex(key)

    key = key + b'\x00' * (64 - len(key))
    o_key_pad = func.list_to_bytes(func.xor(key, b'\x5c' * 64))
    i_key_pad = func.list_to_bytes(func.xor(key, b'\x36' * 64))

    return sm3_hash(func.bytes_to_list(o_key_pad + bytes.fromhex(sm3_hash(func.bytes_to_list(i_key_pad + msg)))))



# random_key = secrets.token_bytes(16)
# print(random_key)
# key = random_key
# message = b'msasdasdasdg'
#
# csm4 = CryptSM4()
#
# csm4.set_key(key, SM4_ENCRYPT)
# encrypt_value = csm4.crypt_ecb(message)  # bytes类型
# print(encrypt_value)
# csm4.set_key(key, SM4_DECRYPT)
# decrypt_value = csm4.crypt_ecb(encrypt_value)  # bytes类型
# print(decrypt_value)
