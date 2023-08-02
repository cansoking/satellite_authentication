import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

host = socket.gethostname()

port = 12345

s.bind((host, 14223))

# 设置超时
s.settimeout(2)

while True:
    inp = input("发送的消息：").strip()
    s.sendto(inp.encode(), (host, port))
    try:
        recv = s.recvfrom(1024)
        data = recv[0].strip().decode()
        print(f"收到回复消息：{data}")
    except socket.timeout:
        print("接收超时，没有收到回复消息")
        continue
    if inp == 'exit':
        break

s.close()

# s.connect((host, port))
# print(s.recv(1024))
# s.close()
