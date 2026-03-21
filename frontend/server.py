"""Simple static file server for the frontend on port 6060."""
import http.server
import socketserver
import os

PORT = 6060
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Frontend running at http://localhost:{PORT}")
    httpd.serve_forever()
