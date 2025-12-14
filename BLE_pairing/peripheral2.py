from bluezero import adapter
from bluezero import peripheral
from bluezero import device
from bluezero import local_agent  # 追加: エージェント用モジュール

# 独自のサービスとキャラクタリスティックを定義
SRV_UUID = '12345678-1234-5678-1234-56789abcdef0'
CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'

# I/O Capabilityの設定
# 研究内容に合わせて変更してください:
# - 'NoInputNoOutput' : 画面なし・ボタンなし (Just Works) -> 自動接続向け
# - 'KeyboardDisplay' : 画面あり・キーボードあり (Numeric Comparison等) -> セキュリティ検証向け
# - 'DisplayOnly'     : 画面のみ
IO_CAPABILITY = 'NoInputNoOutput' 

def on_write(value, options):
    # バイト列を文字列に変換して表示
    try:
        text = bytes(value).decode('utf-8')
        print(f"\n[!] 受信しました: {text}")
        
    except Exception as e:
        print(f"デコードエラー: {e}")

def main():
    # アダプターの準備
    try:
        # アダプターが複数ある場合や特定のアダプターを使う場合は修正してください
        dongle = adapter.Adapter(adapter.list_adapters()[0])
    except IndexError:
        print("Bluetoothアダプターが見つかりません。")
        return

    print(f"使用アダプター: {dongle.address}")

    # --- 追加部分: エージェント(I/O Capability)の設定 ---
    print(f"エージェントを構成中... Capability: {IO_CAPABILITY}")
    agent = local_agent.Agent(capability=IO_CAPABILITY)

    # ペアリング時のコールバック（必要に応じて実装）
    # NoInputNoOutput(Just Works)の場合は通常呼ばれませんが、念のため定義しておくと安全です
    def request_confirmation(device, passkey):
        print(f"ペアリング確認: {device} Passkey: {passkey}")
        # Yesを選択したとみなす
        return

    agent.request_confirmation = request_confirmation
    
    # エージェントの起動（登録）
    # 注意: publish()の前に実行する必要があります
    agent.start()
    print("エージェント起動完了")
    # ---------------------------------------------------

    # ペリフェラル（サーバー）の設定
    print(f"BLEサーバーを準備中... Local Name: VulnDevice")
    
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

    # 公開開始 (ここでメインループに入ります)
    print("アドバタイズ開始。接続待機中...")
    try:
        server.publish()
    except KeyboardInterrupt:
        print("\n終了します。")
    finally:
        # 終了処理（必要であれば）
        pass

if __name__ == '__main__':
    main()