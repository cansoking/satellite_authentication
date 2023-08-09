import socket
import time
from threading import Thread

from secret_key_dictionary import *
from GMCrypto import hmac_sm3_256
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
from satellite_utils import generate_random_id
from gmssl import func


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

    # 计算函数
    def _function_tid(self, t_tid, rid):
        """
        计算TID
        :return: TID
        """

        message = bytes(t_tid + rid, 'utf8')
        # 初始化SM4
        csm4 = CryptSM4()
        csm4.set_key(self._id_key, SM4_ENCRYPT)
        tid = csm4.crypt_ecb(message)  # bytes类型
        # 转为16进制字符返回
        return tid.hex()

    def _function_ak(self, t_auth):
        return hmac_sm3_256(self._main_key.decode(), t_auth)

    def _function_tk(self, auth_key, rand):
        return hmac_sm3_256(auth_key, rand)

    def _function_mac(self, key, msg):
        mac_sm4 = CryptSM4()
        mac_sm4.set_key(key, SM4_ENCRYPT)
        mac = mac_sm4.crypt_cbc(key, msg)
        return mac

    def _function_ck(self, auth_key, rand):
        return hmac_sm3_256(auth_key, rand)

    def _function_res(self, ck, rand):
        return hmac_sm3_256(ck, rand)

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
        self.__auth_token = None
        self.__xres = None
        self.__ck = None
        self.__xtid = None
        self.__auth_key = None
        self.__rand = None
        self.__geo_socket = None
        self.__access_queue = []

    def access_authentication(self, satellite):
        pass

    def pre_calculate(self, ac_time, rid):
        """
        认证预计算
        :param ac_time: 下次接入时间
        """
        # 计算信息
        self.__xtid = self._function_tid(str(ac_time), rid)
        self.__auth_key = self._function_ak(str(ac_time))
        self.__ck = self._function_ck(self.__auth_key, self.__rand)
        self.__xres = self._function_res(self.__ck, self.__rand)
        # 计算新Token和CK
        rand = generate_random_id()
        self.__ck = self._function_ck(self.__auth_key, rand)
        tk = self._function_tk(self.__auth_key, rand)
        # 计算MAC
        mac = self._function_mac(bytes(self.__auth_key, 'utf8'),
                                 bytes(rand + str(ac_time) + self._gid, 'utf8'))
        # 组合Token
        t_token_xor_tk = func.list_to_bytes(func.xor(bytes(str(ac_time), 'utf8'), bytes(tk, 'utf8')))
        self.__auth_token = bytes(rand, 'utf8') + t_token_xor_tk + bytes(self._gid, 'utf8') + mac

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

            rcv = self.__geo_socket.recvfrom(1024)
            recv_data = rcv[0].strip().decode()
            tcc_ip_port = rcv[1]
            command = recv_data.split('&')[0]
            content = recv_data.split('&')[1]
            while True:
                if command == 'close':
                    break
                if command == 'join' or command == 'sjoin':
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
                                # 计算auth key
                                auth_key = self._function_ak(t_auth)
                                # 生成随机数
                                rand = generate_random_id()
                                self.__rand = rand
                                # 计算TK
                                tk = self._function_tk(auth_key, rand)
                                # 获取t_token
                                t_token = str(int(time.time()))
                                # 计算MAC
                                mac = self._function_mac(bytes(auth_key, 'utf8'),
                                                         bytes(rand + t_token + self._gid, 'utf8'))
                                # 组合Token
                                t_token_xor_tk = func.list_to_bytes(func.xor(bytes(t_token, 'utf8'), bytes(tk, 'utf8')))
                                auth_token = bytes(rand, 'utf8') + t_token_xor_tk + bytes(self._gid, 'utf8') + mac
                                # 返回Token给LEO
                                self.__geo_socket.sendto(auth_token, (ip_port[0], int(ip_port[1])))
                                print(f"[GEO-{self._rid}] 返回Token到<{ip_port[0]}:{ip_port[1]}> Token内容：{auth_token}")
                                # 计算会话密钥CK 和 预期认证相应XRES， GEO自己存储
                                self.__ck = self._function_ck(auth_key, rand)
                                self.__xres = self._function_res(self.__ck, rand)
                                # 准备接收RES
                                self.__geo_socket.settimeout(0.5)
                                res = self.__geo_socket.recvfrom(1024)[0].strip().decode()
                                print(f"[GEO-{self._rid}] 接受到RES：{res}")
                                # 验证RES
                                if self.__xres == res:
                                    print(f"[GEO-{self._rid}] RES校验成功 本方完成身份认证")
                                    # 发送接入成功认证给TCC
                                    self.__access_queue.pop()
                                    self.__geo_socket.sendto(b'faa', (tcc_ip_port[0], int(tcc_ip_port[1])))
                                    # 修改超时
                                    self.__geo_socket.settimeout(100)
                                    break
                                else:
                                    print(f"[GEO-{self._rid}] RES校验失败")
                                # 交换信息
                            else:
                                print(f"[GEO-{self._rid}] 验证失败 #rid或时间戳不符合要求")
                                break
                        elif len(data) == 96:
                            # 提取内容
                            tid = data[:32]
                            res = data[32:]
                            print(f"tid: {tid}, xtid: {self.__xtid}")
                            print(f"res: {res}, xres: {self.__xres}")
                            # 比较预计算内容
                            if tid == self.__xtid and res == self.__xres:
                                print(f"[GEO-{self._rid}] 预计算TID和RES校验成功 本方完成身份认证")
                                # 返回预计算Token给LEO
                                self.__geo_socket.sendto(self.__auth_token, (ip_port[0], int(ip_port[1])))
                                print(f"[GEO-{self._rid}] 返回预计算Token到<{ip_port[0]}:{ip_port[1]}> Token内容：{self.__auth_token}")
                            else:
                                print(f"[GEO-{self._rid}] 预计算TID和RES校验失败")
                        # recv = self.__geo_socket.recvfrom(1024)
                recv_data = self.__geo_socket.recvfrom(1024)[0].strip().decode()
                command = recv_data.split('&')[0]
                content = recv_data.split('&')[1]

        thread_tcc = Thread(target=processing_threading_method)
        thread_tcc.start()


# 低地球轨道卫星LEO类
class LEO(Satellite):

    def __init__(self):
        super().__init__()
        self.__res = None
        self.__rand = None
        self.__ck = None
        self.__auth_key = None
        self.__tid = None
        self.__leo_socket = None

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
                if command == 'sjoin':
                    for satellite in self._authentication_table:
                        if satellite['rid'] == content:
                            # 轨道摄动选项
                            is_perturbation = False
                            if is_perturbation:
                                pass
                            else:
                                # 没发生轨道摄动
                                # 发送星间切换认证请求给GEO
                                self.switching_access_authentication(satellite['rid'])
                            break

                recv_data = self.__leo_socket.recvfrom(1024)[0].strip().decode()
                command = recv_data.split('&')[0]
                content = recv_data.split('&')[1]

        thread_object = Thread(target=processing_tcc_method)
        thread_object.start()

    def pre_calculate(self, ac_time):
        """
        认证预计算
        :param ac_time: 下次接入时间
        """
        # 计算信息
        self.__tid = self._function_tid(str(ac_time), self._rid)
        self.__auth_key = self._function_ak(str(ac_time))
        self.__ck = self._function_ck(self.__auth_key, self.__rand)
        self.__res = self._function_res(self.__ck, self.__rand)

    def switching_access_authentication(self, rid):
        """
        切换接入认证
        :param rid: 接入的卫星ID
        """
        # 发送TID和RES给GEO
        for satellite in self._authentication_table:
            if satellite['rid'] == rid:
                msg = self.__tid + self.__res
                self.__leo_socket.sendto(msg.encode(), (satellite['ip'], int(satellite['port'])))
                print(f"[LEO-{self._rid}] 发送切换接入请求到<{satellite['ip']}:{satellite['port']}> 密文内容：{msg}")
                # 设置超时，此处超时0.5s，规定Token返回时间
                self.__leo_socket.settimeout(0.5)
                recv_data = self.__leo_socket.recvfrom(1024)[0].strip()
                print(f"[LEO-{self._rid}] 接受到Token：{recv_data}")
                # 提取rand, mac, t_token_xor_tk, gid
                rand = recv_data[:5].decode()
                mac = recv_data[-32:]
                t_token_xor_tk = recv_data[5:-37]
                gid = recv_data[-37:-32].decode()
                # 验证Token合法性
                # 计算TK
                tk = self._function_tk(self.__auth_key, rand)
                # 恢复T_Token
                t_token = func.list_to_bytes(func.xor(t_token_xor_tk, bytes(tk, 'utf8'))).decode()
                # 新鲜性认证
                if time.time() - int(t_token) < 1:
                    # 通过认证
                    print(f"[LEO-{self._rid}] T_Token新鲜性验证成功 准备下一步校验")
                    # 计算XMAC
                    xmac = self._function_mac(bytes(self.__auth_key, 'utf8'), bytes(rand + t_token + gid, 'utf8'))
                    # 校验MAC
                    if xmac == mac:
                        print(f"[LEO-{self._rid}] MAC校验成功 本方完成身份认证")
                        # 计算CK 和 RES
                        ck = self._function_ck(self.__auth_key, rand)
                    else:
                        print(f"[LEO-{self._rid}] MAC校验失败")
                else:
                    print(f"[LEO-{self._rid}] T_Token新鲜性验证失败")

    def access_authentication(self, rid):
        """
        初次接入认证
        :param rid: 接入的卫星ID
        """

        # 计算TID
        tid = self._function_tid(str(int(time.time())), self._rid)
        # 设置超时，此处超时100s，预防假节点
        self.__leo_socket.settimeout(100)
        # 发送TID
        for satellite in self._authentication_table:
            if satellite['rid'] == rid:
                self.__leo_socket.sendto(tid.encode(), (satellite['ip'], int(satellite['port'])))
                print(f"[LEO-{self._rid}] 发送接入请求到<{satellite['ip']}:{satellite['port']}> 密文内容：{tid}")
                # 设置超时，此处超时0.5s，规定Token返回时间
                self.__leo_socket.settimeout(0.5)
                recv_data = self.__leo_socket.recvfrom(1024)[0].strip()
                print(f"[LEO-{self._rid}] 接受到Token：{recv_data}")
                # 提取rand, mac, t_token_xor_tk, gid
                rand = recv_data[:5].decode()
                self.__rand = rand
                mac = recv_data[-32:]
                t_token_xor_tk = recv_data[5:-37]
                gid = recv_data[-37:-32].decode()
                # 验证Token合法性
                # 生成AuthKey
                t_auth = str(int(time.time()))
                auth_key = self._function_ak(t_auth)
                # 计算TK
                tk = self._function_tk(auth_key, rand)
                # 恢复T_Token
                t_token = func.list_to_bytes(func.xor(t_token_xor_tk, bytes(tk, 'utf8'))).decode()
                # 新鲜性认证
                if time.time() - int(t_token) < 1:
                    # 通过认证
                    print(f"[LEO-{self._rid}] T_Token新鲜性验证成功 准备下一步校验")
                    # 计算XMAC
                    xmac = self._function_mac(bytes(auth_key, 'utf8'), bytes(rand + t_token + gid, 'utf8'))
                    # 校验MAC
                    if xmac == mac:
                        print(f"[LEO-{self._rid}] MAC校验成功 本方完成身份认证")
                        # 计算CK 和 RES
                        ck = self._function_ck(auth_key, rand)
                        res = self._function_res(ck, rand)
                        # 返回RES给GEO
                        self.__leo_socket.sendto(res.encode(), (satellite['ip'], int(satellite['port'])))
                        print(f"[LEO-{self._rid}] 发送RES到<{satellite['ip']}:{satellite['port']}> RES内容：{res}")
                        # !!!!!!!!!!!! 省略认证信息交换过程，从初始认证中记录需要认证信息
                        # 修改超时
                        self.__leo_socket.settimeout(100)
                    else:
                        print(f"[LEO-{self._rid}] MAC校验失败")
                else:
                    print(f"[LEO-{self._rid}] T_Token新鲜性验证失败")
