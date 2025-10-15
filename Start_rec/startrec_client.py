import asyncio
from bleak import BleakScanner, BleakClient

# サーバー側（スマートグラス役）で設定したUUIDと全く同じものを指定します
REC_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
REC_CONTROL_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# 送信するコマンド
COMMAND_TO_SEND = "START_REC"
# 録画を停止したい場合は、ここを "STOP_REC" に変更してください

async def main():
    print("スマートグラス役のデバイスを探しています...")

    # 指定したサービスUUIDを持つデバイスをスキャンして探す
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: REC_SERVICE_UUID in ad.service_uuids
    )

    if device is None:
        print(f"🛑 目的のデバイスが見つかりませんでした。")
        return

    print(f"✅ デバイスを発見しました: {device.name} ({device.address})")

    # `async with`を使うと、接続と切断が自動的に管理されて安全です
    async with BleakClient(device) as client:
        if client.is_connected:
            print(f"デバイスに接続しました。コマンドを送信します...")
            
            # コマンドをバイト形式にエンコードして書き込む
            await client.write_gatt_char(REC_CONTROL_UUID, COMMAND_TO_SEND.encode("utf-8"))
            
            print(f"✅ コマンド '{COMMAND_TO_SEND}' を送信しました。")
        else:
            print("🛑 デバイスへの接続に失敗しました。")

if __name__ == "__main__":
    asyncio.run(main())