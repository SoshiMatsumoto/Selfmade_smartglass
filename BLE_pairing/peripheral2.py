import subprocess
import time
from bluezero import adapter
from bluezero import peripheral

# 独自のサービスとキャラクタリスティック
SRV_UUID = '12345678-1234-5678-1234-56789abcdef0'
CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'

def on_write(value, options):
    try:
        text = bytes(value).decode('utf-8')
        print(f"\n[!] 受信しました: {text}")
        
        # ★研究用: 脆弱性ポイント★
        # import os
        # os.system(text) 
        
    except Exception as e:
        print(f"デコードエラー: {e}")

def main():
    # 1. アダプターの設定（これは永続するので run でOK）
    subprocess.run(["bluetoothctl", "power", "on"])
    subprocess.run(["bluetoothctl", "pairable", "on"])
    subprocess.run(["bluetoothctl", "discoverable", "on"]) # 発見可能にする

    # 2. Agentの設定（プロセスを維持する必要があるため Popen を使用）
    print("Agent(NoInputNoOutput)を設定中...")
    bt_agent = subprocess.Popen(
        ["bluetoothctl"], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.DEVNULL, # ログが邪魔なら捨てる
        text=True
    )
    
    # bluetoothctl にコマンドを打ち込む
    try:
        bt_agent.stdin.write("agent NoInputNoOutput\n")
        bt_agent.stdin.write("default-agent\n")
        bt_agent.stdin.flush()
        # 少し待って設定を反映させる
        time.sleep(1)
    except Exception as e:
        print(f"Agent設定エラー: {e}")

    # 3. アダプターの準備
    try:
        dongle = adapter.Adapter(adapter.list_adapters()[0])
        print(f"BLEサーバーを起動します... ({dongle.address})")
    except Exception:
        print("Bluetoothアダプターが見つかりません")
        bt_agent.terminate()
        return

    # 4. ペリフェラルの設定
    server = peripheral.Peripheral(dongle.address, local_name='VulnDevice', appearance=0x0000)
    server.add_service(srv_id=1, uuid=SRV_UUID, primary=True)
    server.add_characteristic(srv_id=1, chr_id=1, uuid=CHAR_UUID,
                              value=[], notifying=False,
                              flags=['write', 'write-without-response'],
                              write_callback=on_write,
                              read_callback=None,
                              notify_callback=None)

    # 5. 公開開始
    print("書き込み待機中... (Ctrl+Cで終了)")
    try:
        server.publish()
    except KeyboardInterrupt:
        print("\n終了処理中...")
    finally:
        # 終わる時は agent も閉じる
        bt_agent.terminate()

if __name__ == '__main__':
    main()