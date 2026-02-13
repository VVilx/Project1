import sys
import socket
from urllib.parse import urlparse
import ssl
import re

# get urls_file name from command line
if len(sys.argv) != 2:
    print('Usage: monitor urls_file')
    sys.exit()

# text file to get list of urls
urls_file = sys.argv[1]

# server, port, and path should be parsed from url
with open(urls_file, 'r') as f:
    urls = f.readlines()


def fetch_url(url):
    parsed = urlparse(url)
    host = parsed.hostname
    path = parsed.path if parsed.path else '/'

    sock = None
    try:
        # create client socket, connect to server
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
            if not data:
                break
            response += data

        response_text = response.decode('utf-8', errors='ignore')
        parts = response_text.split('\r\n\r\n', 1)
        headers = parts[0]
        body = parts[1] if len(parts) > 1 else ''

        status_line = headers.split('\r\n')[0]
        status = status_line.split(' ', 1)[1]

        return status, headers, body

    except:
        return "Network Error", None, None

    finally:
        if sock:
            sock.close()


for url in urls:
    url = url.strip()
    if not url:
        continue

    print(f"URL: {url}")

    status, headers, body = fetch_url(url)
    print(f"Status: {status}")

    # Follow URL redirection
    if status.startswith("301") or status.startswith("302"):
        if headers:
            for line in headers.split('\r\n'):
                if line.lower().startswith("location:"):
                    redirected_url = line.split(":", 1)[1].strip()
                    print(f"Redirected URL: {redirected_url}")

                    new_status, _, _ = fetch_url(redirected_url)
                    print(f"Status: {new_status}")
                    break

    # Fetch referenced object (images only)
if body and "<img" in body.lower() and "inet.cs.fiu.edu" in url:
    matches = re.findall(r'<img[^>]+src=["\']?([^"\'>]+)', body, re.IGNORECASE)

    for img_url in matches:

        # ignore embedded base64 images
        if img_url.startswith("data:"):
            continue

        if img_url.startswith("http"):
            full_img_url = img_url
        else:
            parsed = urlparse(url)
            full_img_url = f"{parsed.scheme}://{parsed.hostname}{img_url}"

        print(f"Referenced URL: {full_img_url}")

        img_status, _, _ = fetch_url(full_img_url)
        print(f"Status: {img_status}")





