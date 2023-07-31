from gmssl.sm3 import sm3_hash
from gmssl import func


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
