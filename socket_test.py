import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

host = socket.gethostname()

port = 12345

s.bind((host, port))

# udp data
while True:
    recv = s.recvfrom(1024)
    data = recv[0].strip().decode()
    ip_port = recv[1]
    print(f"本机（{host}:{port}）收到来自客户端（{ip_port[0]}:{ip_port[1]}）的消息：{data}")
    # data = data.strip().decode()
    if data == "exit":
        print("客户端主动断开连接！")
        break

s.close()

# s.listen(5)
#
# while True:
#     c, addr = s.accept()
#     print("ip address: ", addr)
#     c.send(b"test message")
#     c.close()
