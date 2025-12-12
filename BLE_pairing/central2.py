import sys
import time
from gi.repository import GLib
from pydbus import SystemBus

# ==========================================
# 設定
# ==========================================
TARGET_MAC = "E4:5F:01:F2:6D:21"  # TargetのMACアドレス

# ==========================================
# Just Works 用のエージェント定義
# ==========================================
AGENT_PATH = '/test/agent_justworks'
# ★ここが最重要：画面もキーボードもないと宣言する
AGENT_CAPABILITY = "NoInputNoOutput" 

AGENT_INTERFACE = '''
<node>
  <interface name='org.bluez.Agent1'>
    <method name='Release'/>
    <method name='RequestPinCode'>
      <arg type='o' name='device' direction='in'/>
      <arg type='s' name='pincode' direction='out'/>
    </method>
    <method name='DisplayPinCode'>
      <arg type='o' name='device' direction='in'/>
      <arg type='s' name='pincode' direction='in'/>
    </method>
    <method name='RequestPasskey'>
      <arg type='o' name='device' direction='in'/>
      <arg type='u' name='passkey' direction='out'/>
    </method>
    <method name='DisplayPasskey'>
      <arg type='o' name='device' direction='in'/>
      <arg type='u' name='passkey' direction='in'/>
      <arg type='q' name='entered' direction='in'/>
    </method>
    <method name='RequestConfirmation'>
      <arg type='o' name='device' direction='in'/>
      <arg type='u' name='passkey' direction='in'/>
    </method>
    <method name='RequestAuthorization'>
      <arg type='o' name='device' direction='in'/>
    </method>
    <method name='AuthorizeService'>
      <arg type='o' name='device' direction='in'/>
      <arg type='s' name='uuid' direction='in'/>
    </method>
    <method name='Cancel'/>
  </interface>
</node>
'''

class JustWorksAgent(object):
    """
    ペアリング要求に対して全て自動でYESと答えるエージェント
    """
    dbus = AGENT_INTERFACE
    
    def Release(self): 
        print("[Agent] Release")

    # Just Worksではここが呼ばれることが多い（確認要求）
    def RequestConfirmation(self, device, passkey):
        print(f"[Agent] ペアリング確認要求 (Passkey: {passkey:06d}) -> 自動承認")
        return # 何も返さない、エラーも出さないことで「承認」となる

    # デバイスによってはここが呼ばれる（権限要求）
    def RequestAuthorization(self, device):
        print(f"[Agent] 権限要求 -> 自動承認")
        return

    # 以下はJust Worksでは通常呼ばれないが、念のため空実装
    def RequestPinCode(self, device): return "0000"
    def DisplayPinCode(self, device, pincode): pass
    def RequestPasskey(self, device): return 0
    def DisplayPasskey(self, device, passkey, entered): pass
    def AuthorizeService(self, device, uuid): return
    def Cancel(self): print("[Agent] Cancel")

# ==========================================
# メイン処理
# ==========================================
def main():
    bus = SystemBus()
    manager = bus.get('org.bluez', '/org/bluez')
    adapter = bus.get('org.bluez', '/org/bluez/hci0')

    # 1. 以前のペアリング情報を削除（クリーンな状態でテストするため）
    device_path = f"/org/bluez/hci0/dev_{TARGET_MAC.replace(':', '_')}"
    try:
        adapter.RemoveDevice(device_path)
        print("[Info] 古いペアリング情報を削除しました")
        time.sleep(1)
    except:
        pass

    # 2. エージェントの登録
    agent = JustWorksAgent()
    bus.register_object(AGENT_PATH, agent, None)
    try:
        manager.RegisterAgent(AGENT_PATH, AGENT_CAPABILITY)
        manager.RequestDefaultAgent(AGENT_PATH)
        print(f"[Info] Agent登録完了 (Capability: {AGENT_CAPABILITY})")
    except Exception as e:
        print(f"[Info] Agent登録済み、またはエラー: {e}")

    # 3. 接続処理 (スキャンして見つけてから接続する標準手順)
    # ※Classic/BLE誤認を防ぐため、一度DiscoveryFilterをかけます
    print("[Info] BLEデバイスをスキャン中...")
    try:
        adapter.SetDiscoveryFilter({'Transport': GLib.Variant('s', 'le')})
        adapter.StartDiscovery()
    except Exception as e:
        print(f"[Warn] フィルタ設定失敗: {e}")
        adapter.StartDiscovery()

    target_device = None
    for i in range(20): # 20秒探す
        try:
            target_device = bus.get('org.bluez', device_path)
            print("[Info] ターゲットを発見しました")
            adapter.StopDiscovery()
            break
        except KeyError:
            time.sleep(1)

    if not target_device:
        print("[Error] ターゲットが見つかりません。Target側で 'advertise on' していますか？")
        sys.exit(1)

    # 4. 接続
    print("[Info] 接続中...")
    try:
        target_device.Connect()
        print("[Info] 接続成功！")
        time.sleep(2) # 接続安定待ち
    except Exception as e:
        print(f"[Error] 接続失敗: {e}")
        sys.exit(1)

    # 5. ペアリング実行 (ここが本番)
    print("------------------------------------------------")
    print("[Info] ペアリング(Pair)を開始します...")
    try:
        target_device.Pair()
        print("[SUCCESS] ペアリング成功！ (Just Works)")
        print(f"Paired: {target_device.Paired}")
        print("------------------------------------------------")
    except Exception as e:
        print(f"[Error] ペアリング失敗: {e}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass