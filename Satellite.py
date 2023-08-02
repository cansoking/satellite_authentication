import socket
import time
from threading import Thread

from secret_key_dictionary import *
from GMCrypto import hmac_sm3_256


# 卫星基类
class Satellite(object):
    def __str__(self):
        return f"IDKey: {self._id_key}\n" \
               f"RID: {self._rid}\n" \
               f"TID: {self._tid}\n" \
               f"GID: {self._gid}\n" \
               f"IP: {self._socket_ip_address}\n" \
               f"PORT: {self._socket_port}\n" \
               f"TABLE: {self._authentication_table}"

    def __init__(self):
        # 认证信息表
        self._authentication_table = []
        # 身份信息密钥
        self._id_key = ID_KEY
        # 卫星真实身份
        self._rid = ''
        # 卫星临时身份
        self._tid = ''
        # 卫星群组身份
        self._gid = ''
        # socket IP地址
        self._socket_ip_address = ''
        # socket port端口号
        self._socket_port = ''

    # 子类需重写实现
    def access_authentication(self, satellite):
        pass

    # 子类需重写实现
    def start_satellite(self):
        pass

    def set_authentication_table(self, table):
        self._authentication_table = table

    def set_rid(self, rid):
        self._rid = rid

    def set_gid(self, gid):
        self._gid = gid

    def get_ip(self):
        return self._socket_ip_address

    def set_ip(self, ip_address):
        self._socket_ip_address = ip_address

    def get_port(self):
        return self._socket_port

    def set_port(self, port):
        self._socket_port = port


# 地球同步轨道卫星GEO类
class GEO(Satellite):

    def __init__(self):
        super().__init__()
        self.__geo_socket = None

    def access_authentication(self, satellite):
        pass

    def start_satellite(self):
        """
        启动卫星运行线程
        """

        print(f"GEO-{self._rid} 启动成功，在轨运行中·····")

        self.__geo_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.__geo_socket.bind((self._socket_ip_address, int(self._socket_port)))

        # 定义线程函数
        def processing_threading_method():
            print(f"[GEO-{self._rid}] 开始监听接入请求")
            # while True:
            #     pass
            recv = self.__geo_socket.recvfrom(1024)
            data = recv[0].strip().decode()
            ip_port = recv[1]
            print(f"GEO-{self._rid} 接收到来自<{ip_port[0]}:{ip_port[1]}>的接入请求 密文内容：{data}")

        thread_object = Thread(target=processing_threading_method)
        thread_object.start()


# 低地球轨道卫星LEO类
class LEO(Satellite):

    def __init__(self):
        super().__init__()
        self.__leo_socket = None

    def __function_tid(self):
        """
        计算TID
        :return: TID
        """

        t_tid = str(int(time.time()))
        tid = hmac_sm3_256(self._id_key, t_tid + self._rid)
        return tid

    def start_satellite(self):
        """
        启动卫星运行线程
        """
        self.__leo_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.__leo_socket.bind((self._socket_ip_address, int(self._socket_port)))

    def access_authentication(self, satellite):
        """
        接入认证
        :param satellite: 接入的卫星对象
        """

        # 计算TID
        tid = self.__function_tid()
        # 设置超时，此处超时100s，预防假节点
        self.__leo_socket.settimeout(100)
        # 发送TID
        self.__leo_socket.sendto(tid.encode(), (satellite.get_ip(), int(satellite.get_port())))
