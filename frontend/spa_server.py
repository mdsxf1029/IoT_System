#!/usr/bin/env python3
"""
SPA Server - 支持Vue Router的静态文件服务器
"""
import http.server
import socketserver
import os
from urllib.parse import unquote

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    """处理SPA路由的HTTP请求处理器"""
    
    def do_GET(self):
        # 解码URL并移除查询参数
        path = unquote(self.path).split('?')[0]
        
        # 构建文件路径
        file_path = os.path.join(os.getcwd(), path.lstrip('/'))
        
        # 如果是文件且存在，正常返回
        if os.path.isfile(file_path):
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        
        # 否则返回 index.html (支持 Vue Router 的 history 模式)
        self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == '__main__':
    PORT = 5173
    
    # 切换到 dist 目录
    os.chdir('dist')
    
    # 启动服务器
    with socketserver.TCPServer(("", PORT), SPAHandler) as httpd:
        print(f"SPA Server running at http://0.0.0.0:{PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
