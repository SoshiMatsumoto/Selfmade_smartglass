import logging
import os
from bluezero import peripheral

# --- 設定 ---
# スマートグラスのサービスUUID（適当な値）
SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'
# 通知書き込み用のCharacteristic UUID
CHAR_UUID    = '12345678-1234-5678-1234-56789abcdef1'

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartGlass")

def on_write_request(value, options):
    """
    スマホからデータが書き込まれた時に呼ばれる関数
    """
    # 受信データ(bytes)を文字列に変換
    try:
        decoded_text = bytes(value).decode('utf-8')
    except:
        decoded_text = "(decode error)"
    
    logger.info(f"通知を受信しました: {decoded_text}")

    # =================================================================
    # 【ここが脆弱性！】
    # 受信したテキストをサニタイズ(無害化)せず、そのままOSコマンドに埋め込んでいる。
    # 開発者の意図: echoコマンドを使ってログや画面に表示したいだけ。
    # =================================================================
    
    # 想定しているコマンド: echo "Notification: [受信テキスト]"
    command = f'echo "Notification: {decoded_text}"'
    
    logger.info(f"[SYSTEM] 実行するコマンド: {command}")
    
    # OSコマンドの実行 (ここで攻撃コードが走る)
    os.system(command)

def main():
    logger.info("スマートグラス(Bluetooth Server)を起動します...")
    
    # Bluetoothペリフェラル(周辺機器)の作成
    glass_device = peripheral.Peripheral(
        adapter_address=list(peripheral.Adapter.available())[0].address,
        local_name='SmartGlass_Demo', # スマホからはこの名前で見える
        appearance=960 # アイコン(ウェアラブルPC等のコード)
    )

    # サービスの追加
    glass_device.add_service(srv_id=1, uuid=SERVICE_UUID, primary=True)

    # Characteristicの追加 (書き込み可能)
    glass_device.add_characteristic(
        srv_id=1,
        chr_id=1,
        uuid=CHAR_UUID,
        value=[],
        notifying=False,
        flags=['write', 'write-without-response'], # 書き込みを許可
        write_callback=on_write_request # 書き込まれたらこの関数を呼ぶ
    )

    # アドバタイズ(発信)開始
    glass_device.publish()

if __name__ == '__main__':
    main()