import socket
import time
from threading import Thread

from secret_key_dictionary import *
from GMCrypto import hmac_sm3_256
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT


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
        # 星间认证主密钥
        self._main_key = MAIN_KEY
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

    def get_rid(self):
        return self._rid

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
        self.__access_queue = []

    def access_authentication(self, satellite):
        pass

    def start_satellite(self):
        """
        启动卫星运行线程
        """

        print(f"[GEO-{self._rid}] 启动成功，在轨运行中·····")

        self.__geo_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.__geo_socket.bind((self._socket_ip_address, int(self._socket_port)))

        # 定义线程函数
        def processing_threading_method():
            """
            TCC指令处理线程
            """

            print(f"[GEO-{self._rid}] 开始监听消息")

            recv_data = self.__geo_socket.recvfrom(1024)[0].strip().decode()
            command = recv_data.split('&')[0]
            content = recv_data.split('&')[1]
            while True:
                if command == 'close':
                    break
                if command == 'join':
                    # 将卫星rid加入接入队列
                    self.__access_queue.append(content)
                    # 开始接入请求
                    while len(self.__access_queue) != 0:
                        recv = self.__geo_socket.recvfrom(1024)
                        data = recv[0].strip().decode()
                        ip_port = recv[1]
                        print(f"[GEO-{self._rid}] 接收到来自<{ip_port[0]}:{ip_port[1]}>的接入请求 密文内容：{data}")

                        # 判断是否初次接入（判断有没有RES）
                        if len(data) == 32:
                            # 解密TID
                            csm4 = CryptSM4()
                            csm4.set_key(self._id_key, SM4_DECRYPT)
                            d_data = csm4.crypt_ecb(bytes.fromhex(data))  # bytes类型
                            print(f"[GEO-{self._rid}] 从({data})得到解密内容({d_data})")
                            d_data = d_data.decode()
                            t_tid = d_data[:-5]
                            leo_rid = d_data[-5:]
                            if leo_rid == self.__access_queue[0] and time.time() - int(t_tid) < 1:
                                print(f"[GEO-{self._rid}] 验证成功 准备接入")
                                # 返回Token给LEO
                                t_auth = str(int(time.time()))
                            else:
                                print(f"[GEO-{self._rid}] 验证失败 #rid或时间戳不符合要求")
                                break
                        elif len(data) == 64:
                            pass
                        recv = self.__geo_socket.recvfrom(1024)
                recv_data = self.__geo_socket.recvfrom(1024)[0].strip().decode()
                command = recv_data.split('&')[0]
                content = recv_data.split('&')[1]

        thread_tcc = Thread(target=processing_threading_method)
        thread_tcc.start()


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
        message = bytes(t_tid + self._rid, 'utf8')
        # 初始化SM4
        csm4 = CryptSM4()
        csm4.set_key(self._id_key, SM4_ENCRYPT)
        tid = csm4.crypt_ecb(message)  # bytes类型
        # 转为16进制字符返回
        return tid.hex()

    def start_satellite(self):
        """
        启动卫星运行线程
        """

        print(f"[LEO-{self._rid}] 启动成功，在轨运行中·····")

        self.__leo_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.__leo_socket.bind((self._socket_ip_address, int(self._socket_port)))

        # 定义线程函数
        def processing_tcc_method():
            print(f"[LEO-{self._rid}] 开始监听消息")
            recv_data = self.__leo_socket.recvfrom(1024)[0].strip().decode()
            command = recv_data.split('&')[0]
            content = recv_data.split('&')[1]
            while True:
                if command == 'close':
                    break
                if command == 'join':
                    for satellite in self._authentication_table:
                        if satellite['rid'] == content:
                            # 发送接入请求
                            self.access_authentication(satellite['rid'])
                            break
                recv_data = self.__leo_socket.recvfrom(1024)[0].strip().decode()
                command = recv_data.split('&')[0]
                content = recv_data.split('&')[1]

        thread_object = Thread(target=processing_tcc_method)
        thread_object.start()

    def access_authentication(self, rid):
        """
        接入认证
        :param rid: 接入的卫星ID
        :param satellite: 接入的卫星对象
        """

        # 计算TID
        tid = self.__function_tid()
        # 设置超时，此处超时100s，预防假节点
        self.__leo_socket.settimeout(100)
        # 发送TID
        for satellite in self._authentication_table:
            if satellite['rid'] == rid:
                self.__leo_socket.sendto(tid.encode(), (satellite['ip'], int(satellite['port'])))
                print(f"[LEO-{self._rid}] 发送接入请求到<{satellite['ip']}:{satellite['port']}> 密文内容：{tid}")
