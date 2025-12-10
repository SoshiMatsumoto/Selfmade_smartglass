from bluedot.btcomm import BluetoothServer
from signal import pause
import subprocess

# === 受信時のコールバック関数 ===
def data_received(data):
    print(f"[Recv] コマンドを受信しました: {data}")
    
    if data == "LED_ON":
        print(" -> LEDを点灯させる処理をここに書く")
    elif data == "auth_start":
        print(" -> 認証処理など")

# === クライアント接続時のコールバック ===
def client_connected():
    print("[Info] Centralが接続しました")

def client_disconnected():
    print("[Info] Centralが切断しました")

# === Main ===
print("Peripheral (Server) started. Waiting for connection...")
print("OSのAgent機能により、ペアリング要求には自動応答します")

# BluetoothServerを作成
# これによりRFCOMMまたはL2CAPサーバが立ち上がりますが、
# bluedotは裏でBlueZのAgentもうまく処理してくれるため、Just Worksの検証に便利です。
# ※今回は簡易化のためClassic/BLEハイブリッドのような挙動になりますが、
#   ペアリングの検証としては機能します。
s = BluetoothServer(
    data_received, 
    when_client_connects=client_connected, 
    when_client_disconnects=client_disconnected,
    encoding='utf-8' # 文字列として受け取る
)

try:
    pause()
except KeyboardInterrupt:
    print("\nServer stopped")