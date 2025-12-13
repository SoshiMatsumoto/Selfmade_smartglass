import pexpect
import sys

target_mac = "E4:5F:01:F2:6D:21"

print("Start bluetoothctl...")
# Bluetoothctl を起動
child = pexpect.spawn('bluetoothctl', encoding='utf-8')

# ログを画面に表示
child.logfile = sys.stdout

try:
    # プロンプト表示を待つ
    child.expect('#')

    # スキャン開始
    print("Start scan...")
    child.sendline('scan on')

    # ターゲットのMACアドレスが表示されるのを待つ．（timeout after 30s）
    index = child.expect([f"Device {target_mac}", pexpect.TIMEOUT], timeout=30)

    if index == 0:
        print(f"\n{target_mac} is discovered!!! Try to connect...")
        child.sendline('scan off') # スキャン停止コマンド
        child.expect('#')

        child.sendline(f'pair {target_mac}')

        # 接続（ペアリング）成功／失敗のメッセージを待つ
        i = child.expect(["Pairing successful", "Paired: yes", "Failed to pair", pexpect.TIMEOUT], timeout=15)

        if i == 0 or i == 1:
            print("\n>>> Pairing Successful! <<<")
        else:
            print("\n>>> Fail to connect. <<<")
    else:
        print("\nTime is out:The target devise was not found.")

    # 終了の処理
    child.sendline('quit')
    child.close()

except Exception as e:
    print(f"Error: {e}")

