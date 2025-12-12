import pexpect
import time
import sys
import subprocess

# ============================
# 設定
# ============================
TARGET_MAC = "E4:5F:01:F2:6D:21"

def pair_with_bluetoothctl():
    print(f"[Info] {TARGET_MAC} に bluetoothctl 経由でペアリングを要求します...")

    # bluetoothctl を起動
    child = pexpect.spawn("bluetoothctl")
    # child.logfile = sys.stdout.buffer # デバッグ用

    try:
        # 1. プロンプト待ち
        child.expect("#", timeout=5)
        
        # 2. Agentリセット（念のため）
        child.sendline("agent on")
        child.sendline("default-agent")
        
        # 3. キャッシュ削除（重要）
        print("[Action] キャッシュ削除...")
        child.sendline(f"remove {TARGET_MAC}")
        time.sleep(1)

        # 4. スキャン開始（相手を見つけるため）
        print("[Action] スキャン開始...")
        child.sendline("scan on")
        
        # ターゲットが見つかるまで待つパターン
        # (すでにキャッシュにある場合やすぐ見つかる場合に対応)
        try:
            child.expect(f"Device {TARGET_MAC}", timeout=10)
            print("[Info] ターゲット発見！")
        except:
            print("[Info] ターゲットが見つかったか、既にリストにあるようです。")

        # 5. ペアリング実行（これが本命のコマンド）
        print("[Action] ペアリング要求 (pair)...")
        child.sendline("scan off") # 混線防止
        child.sendline(f"pair {TARGET_MAC}")

        # 6. 結果判定
        # 成功すると "Pairing successful" が出る
        # Just Worksなので、パスキー入力などは求められず勝手に進むはず
        index = child.expect(["Pairing successful", "Failed", "Authentication Failed"], timeout=15)
        
        if index == 0:
            print("\n[SUCCESS] ペアリング成功しました！ (Paired: yes)\n")
        else:
            print(f"\n[Failed] ペアリング失敗: {child.before.decode()}")

        # 7. 終了
        child.sendline("quit")
        child.close()

    except pexpect.TIMEOUT:
        print("\n[Error] タイムアウトしました。相手のアドバタイズを確認してください。")
        print(f"直前の出力:\n{child.before.decode()}")
    
    except Exception as e:
        print(f"\n[Error] エラー: {e}")

if __name__ == '__main__':
    pair_with_bluetoothctl()