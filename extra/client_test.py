import socket

def Main():
    host = '192.168.0.3'
    port = 4005

    server = ('192.168.0.3', 4000)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((host, port))
    print(s)

    message = input('-> ')
    while message != 'q':
        s.sendto(message.encode('utf-8'), server)
        data, addr = s.recvfrom(1024)
        data = data.decode('utf-8')
        print('Received from server: ' + data)
        message = input('-> ')
    s.close()

Main()