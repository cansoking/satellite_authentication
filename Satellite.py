from secret_key_dictionary import *


# 卫星基类
class Satellite(object):
    def __str__(self):
        return f"IDKey: {self.__id_key}\n" \
               f"RID: {self.__rid}\n" \
               f"TID: {self.__tid}\n" \
               f"GID: {self.__gid}\n" \
               f"IP: {self.__socket_ip_address}\n" \
               f"PORT: {self.__socket_port}"

    def __init__(self):
        # 身份信息密钥
        self.__id_key = ID_KEY
        # 卫星真实身份
        self.__rid = ''
        # 卫星临时身份
        self.__tid = ''
        # 卫星群组身份
        self.__gid = ''
        # socket IP地址
        self.__socket_ip_address = ''
        # socket port端口号
        self.__socket_port = ''

    def set_rid(self, rid):
        self.__rid = rid

    def set_gid(self, gid):
        self.__gid = gid

    def get_ip(self):
        return self.__socket_ip_address

    def set_ip(self, ip_address):
        self.__socket_ip_address = ip_address

    def get_port(self):
        return self.__socket_port

    def set_port(self, port):
        self.__socket_port = port


# 地球同步轨道卫星GEO类
class GEO(Satellite):
    pass


# 低地球轨道卫星LEO类
class LEO(Satellite):
    pass
