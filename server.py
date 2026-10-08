#!/usr/bin/env python3
"""Proxy + static server for stock-app.
Endpoints:
  /proxy/mis?ex_ch=...   -> mis.twse.com.tw real-time
  /proxy/twse            -> openapi.twse.com.tw STOCK_DAY_ALL
  /proxy/tpex            -> tpex.org.tw mainboard_quotes
  /*                     -> static files from this directory
"""
import json, os, sys, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
MIME = {'.html':'text/html;charset=utf-8', '.js':'application/javascript',
        '.css':'text/css', '.json':'application/json; charset=utf-8'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass   # silence request log

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        path, qs = p.path, p.query

        if path == '/proxy/mis':
            ex_ch = urllib.parse.parse_qs(qs).get('ex_ch', [''])[0]
            url = ('https://mis.twse.com.tw/stock/api/getStockInfo.jsp'
                   f'?json=1&delay=0&ex_ch={urllib.parse.quote(ex_ch, safe="|._-")}')
            self._proxy(url, extra={
                'Referer': 'https://mis.twse.com.tw/',
                'Cookie': '',
            })
        elif path == '/proxy/twse':
            self._proxy('https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL')
        elif path == '/proxy/tpex':
            self._proxy('https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes')
        elif path == '/proxy/inst_foreign':
            self._proxy('https://openapi.twse.com.tw/v1/fund/MI_QFIIS')
        elif path == '/proxy/inst_trust':
            self._proxy('https://openapi.twse.com.tw/v1/fund/TWT93U')
        elif path == '/proxy/inst_dealer':
            self._proxy('https://openapi.twse.com.tw/v1/fund/MI_PROPRIETARY')
        elif path == '/proxy/otc_foreign':
            self._proxy('https://www.tpex.org.tw/openapi/v1/tpex_qfii_trn')
        elif path == '/proxy/otc_trust':
            self._proxy('https://www.tpex.org.tw/openapi/v1/tpex_trust_fund_trn')
        elif path == '/proxy/otc_dealer':
            self._proxy('https://www.tpex.org.tw/openapi/v1/tpex_dealer_trn')
        elif path == '/proxy/margin':
            self._proxy('https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_d')
        elif path == '/proxy/otc_margin':
            self._proxy('https://www.tpex.org.tw/openapi/v1/tpex_margin_trn')
        else:
            self._static(path)

    def _proxy(self, url, extra=None):
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 Chrome/120 Safari/537.36'),
            'Accept': 'application/json, text/plain, */*',
        }
        if extra:
            headers.update(extra)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as r:
                body = r.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json;charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self._json_err(500, str(e))

    def _static(self, path):
        rel = path.lstrip('/')
        fp = os.path.join(BASE, rel) if rel else os.path.join(BASE, 'index.html')
        if os.path.isdir(fp):
            fp = os.path.join(fp, 'index.html')
        if not os.path.isfile(fp):
            self.send_error(404); return
        ext = os.path.splitext(fp)[1].lower()
        ctype = MIME.get(ext, 'application/octet-stream')
        with open(fp, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _json_err(self, code, msg):
        body = json.dumps({'error': msg}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f'Serving at http://localhost:{port}')
    ThreadingHTTPServer(('', port), Handler).serve_forever()
