# ターゲット(受信)側で動かすコード
from bluezero import adapter
from bluezero import peripheral
from bluezero import device

# 独自のサービスとキャラクタリスティックを定義
# (標準のUUIDではなく、ランダムなものを使います)
SRV_UUID = '12345678-1234-5678-1234-56789abcdef0'
CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'

def on_write(value, options):
    # バイト列を文字列に変換して表示
    try:
        text = bytes(value).decode('utf-8')
        print(f"\n[!] 受信しました: {text}")
        
        # ★ここが研究のポイント★
        # 本来は print するだけですが、
        # ここに os.system(text) を書くと「コマンドインジェクション脆弱性」になります。
        # import os
        # os.system(text) 
        
    except Exception as e:
        print(f"デコードエラー: {e}")

def main():
    # アダプターの準備
    dongle = adapter.Adapter(adapter.list_adapters()[0].address)
    
    # ペリフェラル（サーバー）の設定
    print(f"BLEサーバーを起動します... ({dongle.address})")
    print("書き込み待機中...")
    
    server = peripheral.Peripheral(dongle.address, local_name='VulnDevice', appearance=0x0000)
    
    # サービスの追加
    server.add_service(srv_id=1, uuid=SRV_UUID, primary=True)
    
    # 書き込み可能なキャラクタリスティックの追加
    server.add_characteristic(srv_id=1, chr_id=1, uuid=CHAR_UUID,
                              value=[], notifying=False,
                              flags=['write', 'write-without-response'],
                              write_callback=on_write,
                              read_callback=None,
                              notify_callback=None)

    # 公開開始
    server.publish()

if __name__ == '__main__':
    main()