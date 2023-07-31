import uuid


def generate_random_id(id_length=5, inclusive_character=None):
    """
    生成随机id，最大长度为8位
    :param id_length: 生成id的长度
    :param inclusive_character: 用于生成id的字符数组
    :return: 最终生成的id
    """

    if inclusive_character is None:
        inclusive_character = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    if id_length > 8:
        id_length = 8

    u_id = str(uuid.uuid4()).replace("-", '')
    final_id = ''
    for i in range(id_length):
        val = int(u_id[i * 4:i * 4 + 4], 16)
        final_id += inclusive_character[val % len(inclusive_character)]
    return final_id
