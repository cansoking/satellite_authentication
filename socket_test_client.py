import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

host = socket.gethostname()

port = 12345

while True:
    inp = input("发送的消息：").strip()
    s.sendto(inp.encode(), (host, port))
    if inp == 'exit':
        break

s.close()

# s.connect((host, port))
# print(s.recv(1024))
# s.close()
