import sys
import socket
from urllib.parse import urlparse
import ssl

# get urls_file name from command line
if len(sys.argv) != 2:
    print('Usage: monitor urls_file')
    sys.exit()

# text file to get list of urls
urls_file = sys.argv[1]

# server, port, and path should be parsed from url
with open(urls_file, 'r') as f:
    urls = f.readlines()

for url in urls:
    url = url.strip()
    if not url:
        continue

    print(f"URL: {url}")

    parsed = urlparse(url)

    host = parsed.hostname
    path = parsed.path

    sock = None
    # create client socket, connect to server
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        if parsed.scheme == 'https':
            context = ssl.create_default_context()
            port = 443
            sock = context.wrap_socket(sock, server_hostname=host)
        else:
            port = 80
        
        sock.connect((host, port))

        # send http request
        request = f'GET {path} HTTP/1.0\r\n'
        request += f'Host: {host}\r\n'
        request += '\r\n'

        sock.send(request.encode())

        # receive http response
        response = b''
        while True:
            data = sock.recv(4096)
            response += data
            if not data:
                break
            

        response_text = response.decode('utf-8', errors='ignore')
        status_line = response_text.split('\r\n')[0]
        status = status_line.split(' ', 1)[1]

        print(f"Status: {status}")

    except Exception as e:
        print('Status: Network Error')

    if sock:
        sock.close()