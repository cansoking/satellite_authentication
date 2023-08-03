import time

from GroundStation import GroundAuthenticationServer
from Satellite import LEO, GEO


if __name__ == "__main__":
    gas = GroundAuthenticationServer()

    leo = LEO()
    geo = GEO()

    # 添加在轨卫星
    gas.system_initialization.orbit_management.add_satellite(leo)
    gas.system_initialization.orbit_management.add_satellite(geo)

    # 初始化信息
    gas.system_initialization.start_initialization()
    gas.system_initialization.startup_satellites()

    # 模拟G2L首次身份认证
    # time.sleep(3)
    # gas.system_initialization.orbit_management.get_satellite(0).access_authentication(geo)
    gas.system_initialization.orbit_management.G2L_AKA(leo, geo)
    # gas.system_initialization.orbit_management.G2L_AKA(leo, geo)

    # print(gas.system_initialization.orbit_management.get_satellite(0).__str__())
