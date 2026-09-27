import os
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler

mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("text/css", ".css")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def translate_path(self, path):
        # Strip query string and fragment so assets with ?auto=format load correctly
        clean_path = path.split('?', 1)[0].split('#', 1)[0]
        translated = super().translate_path(clean_path)
        if os.path.isdir(translated):
            idx = os.path.join(translated, "index.html")
            if os.path.exists(idx):
                return idx
        elif not os.path.exists(translated):
            idx = translated + "/index.html"
            if os.path.exists(idx):
                return idx
        return translated

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_GET(self):
        clean_path = self.path.split('?', 1)[0].split('#', 1)[0]
        query_string = self.path.split('?', 1)[1] if '?' in self.path else ''

        # Handle Prismic Mock API requests
        try:
            import prismic_mock
            code, ct, body = prismic_mock.handle_prismic_query(clean_path, query_string)
            if code is not None:
                self.send_response(code)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        except Exception as e:
            print("Prismic mock error:", e)

        if clean_path in ('/', ''):
            self.send_response(302)
            self.send_header('Location', '/en/')
            self.end_headers()
            return
        super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_POST(self):
        # Respond 200 OK to beacon/analytics POST requests
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

def run(port=8085):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Agrumea Farm server running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8085
    run(port)
