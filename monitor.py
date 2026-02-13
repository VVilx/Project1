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
# function to fetch URL and return status, headers, body
def fetch(url):
    parsed = urlparse(url)
    host = parsed.hostname
    path = parsed.path if parsed.path else '/'
    port = 443 if parsed.scheme == 'https' else 80

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        if parsed.scheme == 'https':
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=host)
        sock.connect((host, port))

        # send simple HTTP GET
        sock.send(f'GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n'.encode())

        # receive http response
        response = b''
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data

        text = response.decode('utf-8', errors='ignore')
        headers, _, body = text.partition('\r\n\r\n')
        status = headers.split('\r\n')[0].split(' ', 1)[1]
        return status, headers, body


    except:
        return "Network Error", None, None

    finally:
            sock.close()


with open(urls_file, 'r') as f:
    for url in f:
        url = url.strip()
        if not url:
            continue

    print(f"URL: {url}")
    status, headers, body = fetch(url)
    print(f"Status: {status}")

    if status.startswith("301") or status.startswith("302"):
        if headers:
            for line in headers.splitlines():
                if line.lower().startswith("location:"):
                    redirect = line.split(":", 1)[1].strip()
                    print(f"Redirected URL: {redirect}")
                    r_status, _, _ = fetch(redirect)
                    print(f"Status: {r_status}")
                    break

        if body and "inet.cs.fiu.edu" in url:
            import re
            for img in re.findall(r'<img[^>]+src=["\']?([^"\'>]+)', body, re.IGNORECASE):
                if img.startswith("data:"):  # skip embedded images
                    continue
                full_img = img if img.startswith("http") else f"{parsed.scheme}://{parsed.hostname}{img}"
                print(f"Referenced URL: {full_img}")
                img_status, _, _ = fetch(full_img)
                print(f"Status: {img_status}")