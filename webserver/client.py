import socket

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", 9999))
        print(sock.recv(1024).decode())
        while True:
            command = input("> ")
            sock.send(f"{command}".encode())
            print(sock.recv(1024).decode())
