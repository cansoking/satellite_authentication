from GroundStation import GroundAuthenticationServer
from Satellite import LEO, GEO

gas = GroundAuthenticationServer()

leo = LEO()
geo = GEO()

# 添加在轨卫星
gas.system_initialization.orbit_management.add_satellite(leo)
gas.system_initialization.orbit_management.add_satellite(geo)

# 初始化信息
gas.system_initialization.start_initialization()

print(gas.system_initialization.orbit_management.get_satellite(0).__str__())
