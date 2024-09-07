from typing import Dict
from urllib.parse import urlparse
from argparse import ArgumentParser
import socket
import sys

parser = ArgumentParser(
    prog='curl-clone', description='Implements the GET method')

parser.add_argument('url')
args = parser.parse_args()

CRLF = '\r\n\r\n'
REDIRECT_LIMIT = 10
CHUNK_SIZE = 4096


def parse_headers(headers: str) -> ((str, int, str), Dict[str, str]):
    lines = headers.splitlines()
    status_code = int(lines[0].split(' ', 2)[1])

    headers = {}
    for line in lines[1:]:
        key, value = line.split(':', 1)
        headers[key] = value.strip()

    return (status_code, headers)


def receive_data(socket: socket.socket) -> str:
    chunks = []
    while True:
        chunk = socket.recv(CHUNK_SIZE)
        if chunk:
            chunks.append(chunk.decode())
        else:
            break

    return "".join(chunks)


def GET(url: str):
    redirects = REDIRECT_LIMIT
    while redirects:
        url = urlparse(url)
        if url.scheme != 'http':
            print(f"This client is http only: your request is {
                  url.scheme}.", file=sys.stderr)
            return -1

        with socket.create_connection((url.hostname, url.port or 80)) as s:
            # Format Request
            msg = 'GET {0} HTTP/1.0\r\nHost: {1}{2}'
            msg = msg.format(url.path or '/', url.hostname, CRLF)

            # Send Request
            s.sendall(bytes(msg, "UTF-8"))

            # Receive Data
            data = receive_data(s)

            # Format Response
            headers, body = data.split(CRLF)
            status_code, headers = parse_headers(headers)

            # Do not process request if not 'text/html'
            if not headers["Content-Type"].startswith('text/html'):
                return -1

            # Process Response
            match status_code:
                case 200:
                    print(body)
                    return 0
                case status_code if status_code == 301 or status_code == 302:
                    url = headers["Location"]
                    redirects -= 1
                    print(f'Redirected to: {url}', file=sys.stderr)
                case status_code if status_code >= 400:
                    print(body)
                    return -1
    return -1


GET(args.url)
