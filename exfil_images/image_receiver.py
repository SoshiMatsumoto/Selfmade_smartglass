import os
import sys
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import cgi
import io

# 設定
PORT = 8000
SAVE_DIR = "/home/matsupi1/bt_attack/Selfmade_smartglass/exfil_images/Assets"

class ImageReceiverHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """POSTリクエストの処理"""
        if self.path == '/upload':
            try:
                # Content-Typeの取得
                content_type = self.headers.get('Content-Type')
                
                if not content_type or 'multipart/form-data' not in content_type:
                    self.send_error(400, "Content-Type must be multipart/form-data")
                    return
                
                # マルチパートデータのパース
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={
                        'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': content_type,
                    }
                )
                
                # ファイルフィールドの取得
                if 'file' not in form:
                    self.send_error(400, "No file field in request")
                    return
                
                file_item = form['file']
                
                if not file_item.file:
                    self.send_error(400, "Empty file")
                    return
                
                original_filename = file_item.filename or "unknown.mp4"
                _, ext = os.path.splitext(original_filename)
                if not ext:
                    ext = ".mp4" # 拡張子がない場合のデフォルト
                
                # ファイル名の生成（タイムスタンプ付き）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_filename = f"{timestamp}{ext}"
                filepath = os.path.join(SAVE_DIR, save_filename)
                
                # ディレクトリが存在しない場合は作成
                os.makedirs(SAVE_DIR, exist_ok=True)
                
                # ファイル保存
                with open(filepath, 'wb') as f:
                    shutil.copyfileobj(file_item.file, f)
                
                file_size = os.path.getsize(filepath)
                
                # ログ出力
                print(f"[SUCCESS] 画像を受信しました")
                print(f"  - ファイル名: {save_filename}")
                print(f"  - サイズ: {file_size} bytes ({file_size/1024:.2f} KB)")
                print(f"  - 保存先: {filepath}")
                print(f"  - 時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 60)
                
                # 成功レスポンス
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Fole received successfully')
                
            except Exception as e:
                print(f"[ERROR] エラーが発生しました: {e}")
                self.send_error(500, f"Server error: {str(e)}")
        else:
            self.send_error(404, "Not Found")
    
    def log_message(self, format, *args):
        """アクセスログのカスタマイズ"""
        client_ip = self.client_address[0]
        print(f"[ACCESS] {client_ip} - {format % args}")

def run_server():
    """サーバーの起動"""
    print("=" * 60)
    print("画像受信サーバーを起動します")
    print(f"ポート: {PORT}")
    print(f"保存先: {SAVE_DIR}")
    print("=" * 60)
    
    # 保存ディレクトリの作成
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, ImageReceiverHandler)
    
    print(f"\n[READY] サーバーがポート {PORT} で待機中...")
    print("Ctrl+C で終了\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[STOP] サーバーを停止します")
        httpd.shutdown()
        sys.exit(0)

if __name__ == '__main__':
    run_server()