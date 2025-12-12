import pexpect
import time
import sys

# ============================
# 設定
# ============================
TARGET_MAC = "E4:5F:01:F2:6D:21"

def ble_pair_and_attack():
    print(f"[Info] {TARGET_MAC} に Python経由で BLE接続します...")

    # 1. gatttool をインタラクティブモード(-I)で起動
    # -t random : これで強制的にBLE (Random Address) として振る舞います
    cmd = f"gatttool -b {TARGET_MAC} -t random -I"
    child = pexpect.spawn(cmd)

    # ログを画面に出したい場合はコメントアウトを外す
    # child.logfile = sys.stdout.buffer

    try:
        # 2. プロンプトが出るのを待つ
        child.expect(r'\[LE\]>', timeout=5)
        
        # 3. 接続コマンド送信
        print("[Action] Connecting...")
        child.sendline('connect')
        
        # "Connection successful" を待つ
        child.expect('Connection successful', timeout=5)
        print("[Success] 接続成功！ (BLE確定)")

        # 4. ペアリング（セキュリティレベル上げ）要求
        # これを送ると、相手(Target)と Just Works の儀式が始まります
        print("[Action] Pairing (Just Works)...")
        child.sendline('sec-level high')
        
        # 少し待機（ペアリング処理の時間）
        time.sleep(2)
        
        # 5. 成功確認（何かしらの反応を見る）
        # エラーが出ていなければ成功とみなす
        print("[Success] ペアリング完了（エラーなし）")

        # -------------------------------------------------
        # もしコマンドも送りたいならここで送れます
        # -------------------------------------------------
        # 例: NUSに書き込み
        # print("[Action] Sending LED_ON...")
        # child.sendline('char-write-req 0x0025 4C45445F4F4E') # 0x0025はハンドル(環境による)
        
        # 6. 終了処理
        print("[Info] 5秒後に切断します...")
        time.sleep(5)
        child.sendline('disconnect')
        child.expect('Disconnect', timeout=2)
        print("[Info] 終了")

    except pexpect.TIMEOUT:
        print("\n[Error] タイムアウトしました。")
        print("考えられる原因:")
        print("1. 相手(Target)が 'advertise on' していない")
        print("2. 距離が遠い")
        print("3. 以前のClassic接続情報が残っている (bluetoothctl remove 推奨)")
        print(f"直前の出力:\n{child.before.decode()}")
    
    except Exception as e:
        print(f"\n[Error] エラー発生: {e}")

if __name__ == '__main__':
    # 念のためキャッシュ削除コマンドをOSに投げておく
    import subprocess
    subprocess.run(["bluetoothctl", "remove", TARGET_MAC], stderr=subprocess.DEVNULL)
    
    ble_pair_and_attack()