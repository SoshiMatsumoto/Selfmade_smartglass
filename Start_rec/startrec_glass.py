import asyncio
import subprocess

from bleak import BleakServer

# BluetoothサービスとキャラクタリスティックのユニークなID（UUID）を定義します
# 必要であれば、オンラインのUUIDジェネレータで自分だけのIDを作成することもできます
REC_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
REC_CONTROL_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# 録画プロセスを格納するためのグローバル変数
recording_process = None

def handle_write_request(sender, data):
    """
    クライアント（スマホなど）がデータを書き込むたびに呼び出される関数
    """
    global recording_process
    command = data.decode("utf-8").strip()
    print(f"受信したコマンド: {command}")

    # --- 録画開始 ---
    if command == "START_REC":
        if recording_process is None:
            print("✅ 録画を開始します...")
            # rpicam-vidで動画を撮影するコマンド
            # -t 0 は停止されるまで無制限に撮影するという意味
            # -o は出力ファイル名
            cmd = ["rpicam-vid", "-t", "0", "-o", "my_video.h264"]
            
            # Popenを使い、コマンドをバックグラウンドで実行します
            # これにより、録画中もPythonスクリプトは他の処理を続けられます
            recording_process = subprocess.Popen(cmd)
            print(f"録画を開始しました。プロセスID: {recording_process.pid}")
        else:
            print("⚠️ すでに録画が実行中です。")

    # --- 録画停止 ---
    elif command == "STOP_REC":
        if recording_process is not None:
            print("🛑 録画を停止します...")
            # rpicam-vidのプロセスを正常に終了させます
            recording_process.terminate()
            recording_process = None
            print("録画を停止しました。")
        else:
            print("⚠️ 現在、録画は実行されていません。")


async def main():
    """
    BLEサーバーをセットアップして実行するメイン関数
    """
    async with BleakServer() as server:
        await server.add_service_for_characteristic(
            REC_CONTROL_UUID,
            ["write"], # 書き込み可能に設定
            handle_write_request
        )
        print("📹 BLEカメラ制御サービスを実行中です。接続を待っています...")
        await asyncio.Event().wait()


if __name__ == "__main__":
    # このスクリプトを実行したときにmain関数を呼び出す
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Ctrl+Cでスクリプトを終了したときの処理
        print("\nスクリプトが停止されました。")
        if recording_process is not None:
            recording_process.terminate()
            print("録画プロセスをクリーンアップしました。")