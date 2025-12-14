import http.server
import socketserver
import json
import os
from datetime import datetime
import markdown2

PORT = 8000
LOG_FILE = 'Health_and_Fitness/check-in-log.md'
CONTENT_DIR = 'Health_and_Fitness/'

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            data = self.get_log_data()
            self.wfile.write(json.dumps(data).encode())

        elif self.path.startswith('/content/'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            filename = self.path.split('/')[-1]
            md_file_path = os.path.join(CONTENT_DIR, filename)

            if os.path.exists(md_file_path):
                with open(md_file_path, 'r') as f:
                    md_content = f.read()
                    html_content = markdown2.markdown(md_content, extras=["tables"])
                    self.wfile.write(html_content.encode())
            else:
                self.send_error(404, "File not found")

        else:
            # Serve files from the 'Health_and_Fitness/generated_html' directory
            # and the root directory
            if self.path.startswith('/generated_html'):
                 self.path = 'Health_and_Fitness' + self.path
            
            # If the path is empty, serve the main graph page
            if self.path == '/' or self.path == '':
                self.path = '/Health_and_Fitness/generated_html/index.html'

            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def get_log_data(self):
        """
        Reads and parses the check-in log file.
        """
        labels = []
        weight_data = []
        bodyfat_data = []

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()[2:]  # Skip header and separator

                for line in lines:
                    if line.strip().startswith('| 20'):
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 4:
                            date_str = parts[1]
                            weight = float(parts[2]) if parts[2] not in ['None', 'N/A'] else None
                            bodyfat = float(parts[3]) if parts[3] not in ['None', 'N/A'] else None
                            
                            labels.append(date_str)
                            weight_data.append(weight)
                            bodyfat_data.append(bodyfat)
        
        return {'labels': labels, 'weight': weight_data, 'bodyfat': bodyfat_data}

Handler = MyHttpRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()