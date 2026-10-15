import http.server
import socketserver
import json
import urllib.parse
import os
import webbrowser
from qa_engine import MineExplosionQAEngine
from chat_agent import MineSafetyChatAgent

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

engine = MineExplosionQAEngine()
chat_agent = MineSafetyChatAgent()

class AppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                body = json.loads(post_data) if post_data else {}
            except Exception as e:
                body = {}

            message = body.get("message", "").strip()
            persona = body.get("persona", "auto")
            history = body.get("history", [])
            api_key = body.get("apiKey", "")
            provider = body.get("provider", "offline")

            import importlib
            import chat_agent
            importlib.reload(chat_agent)
            agent_instance = chat_agent.MineSafetyChatAgent()

            if not message:
                res = {"error": "No message provided"}
            else:
                res = agent_instance.chat(message, persona=persona, history=history, api_key=api_key, provider=provider)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            return

        if parsed.path == "/api/export-plan":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                body = json.loads(post_data) if post_data else {}
            except Exception:
                body = {}

            mine_name = body.get("mine_name", "Colliery")
            content = body.get("content", "# Revisit Plan")

            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            filename = f"revisit_plan_{mine_name.lower().replace(' ', '_')}.md"
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/chat":
            # Allow quick testing of chat via GET ?q=...&persona=...
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0]
            persona = query_params.get("persona", ["auto"])[0]
            if not q:
                res = {"error": "No query provided"}
            else:
                import importlib
                import chat_agent
                importlib.reload(chat_agent)
                agent_instance = chat_agent.MineSafetyChatAgent()
                res = agent_instance.chat(q, persona=persona)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            return

        if parsed.path == "/api/mines":
            agent_inst = MineSafetyChatAgent()
            mines = agent_inst.get_all_mines()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(mines, ensure_ascii=False).encode('utf-8'))
            return

        if parsed.path == "/api/ask":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0]
            if not q:
                res = {"error": "No query provided"}
            else:
                res = engine.ask(q)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
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
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
            return

        if parsed.path == "/":
            self.path = "/index.html"

        return super().do_GET()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server():
    with ThreadedTCPServer(("", PORT), AppHandler) as httpd:
        print(f"\n" + "=" * 65)
        print(f"  COAL MINE EXPLOSIONS & SAFETY ANALYTICS DASHBOARD + CHAT AGENT")
        print(f"  URL: http://localhost:{PORT}")
        print(f"  Chat API: http://localhost:{PORT}/api/chat")
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
