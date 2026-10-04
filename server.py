import http.server
import socketserver
import json
import urllib.parse
import os
import webbrowser
from qa_engine import MineExplosionQAEngine

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

engine = MineExplosionQAEngine()

class AppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/ask":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0]
            if not q:
                res = {"error": "No query provided"}
            else:
                res = engine.ask(q)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            return

        if parsed.path == "/api/data":
            conn = engine.get_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT * FROM cause_taxonomy ORDER BY fatal_incidents DESC")
            causes = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT company, COUNT(*) as count, SUM(killed) as deaths FROM recent_incidents GROUP BY company ORDER BY deaths DESC")
            companies = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM recent_incidents ORDER BY year DESC")
            recent = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM historical_disasters ORDER BY killed DESC")
            historical = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM courts_of_inquiry ORDER BY inq_no ASC")
            inquiries = [dict(r) for r in cur.fetchall()]

            conn.close()

            payload = {
                "causes": causes,
                "companies": companies,
                "recent": recent,
                "historical": historical,
                "inquiries": inquiries
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
            return

        if parsed.path == "/":
            self.path = "/index.html"

        return super().do_GET()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), AppHandler) as httpd:
        print(f"\n" + "=" * 65)
        print(f"  COAL MINE EXPLOSIONS & SAFETY ANALYTICS DASHBOARD RUNNING")
        print(f"  URL: http://localhost:{PORT}")
        print(f"=" * 65)
        print("  Press Ctrl+C in terminal to stop server.\n")
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == '__main__':
    run_server()
