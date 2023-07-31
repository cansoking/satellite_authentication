import socket

from satellite_utils import generate_random_id


class GroundAuthenticationServer:
    """
    地面认证服务器包括系统初始化模块和组网认证模块两部分
    """

    def __init__(self):
        # 模块初始化
        self.system_initialization = self.__SystemInitialization()
        self.networking_authentication = self.__NetworkingAuthentication()

    class __SystemInitialization:
        """
        系统初始化模块用于对卫星的认证系统进行初始化，
        包括轨道管理子模块、身份信息管理子模块，密钥管理子模块三部分；
        """

        def __init__(self):
            self.identity_information_management = self.__IdentityInformationManagement()
            self.key_management = self.__KeyManagement()
            self.orbit_management = self.__OrbitManagement()

        def start_initialization(self):
            """
            启动初始化，由地面认证服务器向在轨卫星生成和发送身份信息
            """

            # 获取在轨卫星数量
            num_satellites = self.orbit_management.get_num_satellites()
            # 生成身份信息
            satellites_information = self.identity_information_management.generate_identity_information(num_satellites)
            # 分发身份信息
            for i in range(num_satellites):
                satellite = self.orbit_management.get_satellite(i)
                info = satellites_information[i]
                satellite.set_ip(info['ip'])
                satellite.set_port(info['port'])
                satellite.set_rid(info['rid'])
                satellite.set_gid(info['gid'])

        class __IdentityInformationManagement:
            """
            身份信息管理子模块负责为在轨卫星生成和分发身份信息并为全网卫星维护一张身份信息表，
            该表中包含有每个卫星的 ID 、GID 、SSID 等，
            用于协助在轨卫星进行认证信息的查询和更新
            """

            def __init__(self):
                pass

            def generate_identity_information(self, num_satellites):
                """
                生成卫星身份信息
                :param num_satellites: 需要生成信息的卫星数量
                :return: 卫星身份信息
                """

                satellites_information = []
                for i in range(num_satellites):
                    # 生成RID
                    cur_sate_info = {'rid': generate_random_id(),
                                     'gid': generate_random_id(),
                                     'port': generate_random_id(),
                                     'ip': "127.0.0.1"}
                    satellites_information.append(cur_sate_info)
                return satellites_information

        class __KeyManagement:
            """
            密钥管理子模块负责为在轨卫星生成两两共享的认证主密钥、更新在轨卫星的星地会话密钥等密钥管理工作
            """
            pass

        class __OrbitManagement:
            """
            轨道管理子模块
            """

            def __init__(self, orbiting_satellites=None):
                self.__orbiting_satellites = orbiting_satellites
                if orbiting_satellites is None:
                    self.__orbiting_satellites = []

            def add_satellite(self, satellite):
                self.__orbiting_satellites.append(satellite)

            def get_satellite(self, index):
                return self.__orbiting_satellites[index]

            def get_num_satellites(self):
                return len(self.__orbiting_satellites)

    class __NetworkingAuthentication:
        """
        组网认证模块只在 L2L-AKA 星间组网认证方案中有效，主要负责协助在轨卫星进行身份认证
        """
        pass
