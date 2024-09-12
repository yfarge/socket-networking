from argparse import ArgumentParser
import socket
import os

parser = ArgumentParser(prog="http_server1")
parser.add_argument('port', type=int)

args = vars(parser.parse_args())
PORT = args["port"]


def receive_request(sock: socket.socket):
    data = b''
    while b'\r\n\r\n' not in data:
        chunk = sock.recv(1024)
        if not chunk:
            break
        data += chunk

    return data.decode('ascii')


def parse_headers(headers: str):
    headers_lines = headers.splitlines()
    request_line = headers_lines[0].split(' ')
    headers_dict = {}

    for line in headers_lines:
        if ':' in line:
            field, value = line.split(':', maxsplit=1)
            headers_dict[field] = value

    return request_line, headers_dict


def send_file(sock: socket.socket, filename: str) -> None:
    file_path = os.path.realpath(os.getcwd() + filename)
    if not os.path.exists(file_path):
        response = (
            'HTTP/1.0 404 Not Found\r\n'
            'Content-Type: text/html\r\n'
            '\r\n'
            '<html><body>404 Not Found</body></html>'
        )
    elif not (file_path.endswith('.htm') or file_path.endswith('.html')):
        response = (
            'HTTP/1.0 403 Forbidden\r\n'
            'Content-Type: text/html\r\n'
            '\r\n'
            '<html><body>403 Forbidden</body></html>'
        )
    else:
        with open(file_path) as file:
            data = file.read()

        response = (
            'HTTP/1.0 200 OK\r\n'
            'Content-Type: text/html\r\n'
            'Content-Length: {}\r\n'
            '\r\n'
            '{}'
        ).format(len(data), data)

    sock.sendall(response.encode('ascii'))


def create_server(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(('', port))
        server.listen()
        try:
            while True:
                client, address = server.accept()
                request_data = receive_request(client)
                request_line, headers_dict = parse_headers(request_data)
                method, path, _ = request_line
                match method:
                    case 'GET':
                        send_file(client, path)
                    case _:
                        response = (
                            'HTTP/1.0 400 Bad Request\r\n'
                            'Content-Type: text/html\r\n'
                            '\r\n'
                            '<html><body>400 Bad Request</body></html>'
                        )
                        client.sendall(response.encode('ascii'))
                client.close()
        except KeyboardInterrupt:
            server.close()


create_server(PORT)
