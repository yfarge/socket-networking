from typing import Dict, Optional
from urllib.parse import urlparse
from argparse import ArgumentParser
import socket
import sys

parser = ArgumentParser(
    prog='a simple curl clone', description='Implements the GET method')

parser.add_argument('url')
args = parser.parse_args()

MAXMIMUM_REDIRECTS = 10


def parse_headers(headers: str) -> (int, Dict[str, str]):
    header_lines = headers.splitlines()
    status_code = int(header_lines[0].split(' ', 2)[1])

    header_dict = {}
    for line in header_lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            header_dict[key.strip()] = value.strip()

    return status_code, header_dict


def receive_response(sock: socket.socket) -> str:
    response = b''
    while True:
        data = sock.recv(1024)
        if not data:
            break
        response += data

    return response.decode('ascii')


def send_request(host: str, port: int, request: str) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(request.encode('ascii'))
        response = receive_response(s)

    return response


def fetch_url(url: str) -> Optional[str]:
    parsed_url = urlparse(url)

    host = parsed_url.hostname
    port = parsed_url.port or 80
    netloc = parsed_url.netloc
    path = parsed_url.path or '/'
    scheme = parsed_url.scheme

    if scheme != 'http':
        print(f"This client only supports HTTP: {scheme}", file=sys.stderr)
        sys.exit(1)

    request = f'GET {path} HTTP/1.0\r\n'
    request += f'Host: {netloc}\r\n\r\n'
    response = send_request(host, port, request)
    headers, body = response.split("\r\n\r\n")
    status_code, header_dict = parse_headers(headers)

    content_type = header_dict.get('Content-Type')
    if content_type and not content_type.startswith('text/html'):
        print("This client only supports 'text/html'", file=sys.stderr)
        sys.exit(1)

    match status_code:
        case 200:
            print(body)
            sys.exit(0)
        case status_code if status_code in (301, 302):
            if 'Location' in header_dict:
                redirect_url = header_dict.get('Location')
                print(f"Redirected to {redirect_url}")
                return redirect_url
        case status_code if status_code >= 400:
            print(body)
            sys.exit(1)


def get(url: str):
    redirect_count = MAXMIMUM_REDIRECTS
    while redirect_count:
        url = fetch_url(url)
        redirect_count -= 1
    print("Maximum number of redirects reached.", file=sys.stderr)
    sys.exit(1)


get(args.url)
