import sys
import time
from gi.repository import GLib
from pydbus import SystemBus

# === 設定エリア ===
# 通信相手(Peripheral側)のMACアドレスをここに記入してください
TARGET_MAC_ADDRESS = "E4:5F:01:F2:6D:21" 

# コマンド送信先のCharacteristic UUID (Peripheral側と合わせる)
UART_RX_CHARACTERISTIC_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# Just Works用エージェント設定
AGENT_PATH = '/test/agent_initiator'
CAPABILITY = "NoInputNoOutput"

# === Agent Class (Just Works強制用) ===
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

class InitiatorAgent(object):
    """
    ペアリング要求時にOSからの確認に応答するためのエージェント
    """
    dbus = AGENT_INTERFACE
    
    def Release(self):
        print("[Agent] Release called")
    
    def RequestPinCode(self, device):
        print(f"[Agent] RequestPinCode for {device}")
        return "0000"
    
    def DisplayPinCode(self, device, pincode):
        print(f"[Agent] DisplayPinCode: {pincode}")
    
    def RequestPasskey(self, device):
        print(f"[Agent] RequestPasskey for {device}")
        return 0
    
    def DisplayPasskey(self, device, passkey, entered):
        print(f"[Agent] DisplayPasskey: {passkey:06d} (entered: {entered})")
    
    def RequestConfirmation(self, device, passkey):
        print(f"[Agent] ペアリング確認要求: {passkey:06d} -> 自動承認")
        return
    
    def RequestAuthorization(self, device):
        print(f"[Agent] RequestAuthorization for {device}")
        return
    
    def AuthorizeService(self, device, uuid):
        print(f"[Agent] AuthorizeService: {uuid}")
        return
    
    def Cancel(self):
        print("[Agent] Cancel called")

# === Main Logic ===
def connect_and_send():
    bus = SystemBus()
    adapter = bus.get('org.bluez', '/org/bluez/hci0')
    manager = bus.get('org.bluez', '/org/bluez')

    # 1. Agentの登録
    agent = InitiatorAgent()
    
    # オブジェクトをD-Busに登録する正しい方法
    bus.register_object(AGENT_PATH, agent, None)
    
    try:
        manager.RegisterAgent(AGENT_PATH, CAPABILITY)
        manager.RequestDefaultAgent(AGENT_PATH)
        print("[Info] Agent registered as NoInputNoOutput (Just Works)")
    except Exception as e:
        print(f"[Warn] Agent registration failed (maybe already registered): {e}")

    # 2. デバイスオブジェクトの取得と接続
    device_path = f"/org/bluez/hci0/dev_{TARGET_MAC_ADDRESS.replace(':', '_')}"
    
    try:
        device = bus.get('org.bluez', device_path)
    except KeyError:
        print("[Error] デバイスが見つかりません。一度スキャンしてOSに認識させてください。")
        print("実行例: bluetoothctl scan on (数秒待って) scan off")
        sys.exit(1)

    print(f"[Info] {TARGET_MAC_ADDRESS} に接続中...")
    try:
        device.Connect()
        print("[Info] 接続成功")
    except Exception as e:
        print(f"[Error] 接続失敗: {e}")
        sys.exit(1)

    # 3. ペアリング実行 (Just Works)
    if not device.Paired:
        print("[Info] ペアリングを開始します...")
        try:
            device.Pair()
            print("[Info] ペアリング完了！")
        except Exception as e:
            print(f"[Error] ペアリング失敗: {e}")
    else:
        print("[Info] 既にペアリング済みです")

    # 4. GATTサービスの解決待ち
    time.sleep(2)

    # 5. コマンド送信 (Characteristicへの書き込み)
    mngr_obj = bus.get('org.bluez', '/')
    mngt = mngr_obj.GetManagedObjects()
    target_char = None
    
    for path, interfaces in mngt.items():
        if "org.bluez.GattCharacteristic1" in interfaces:
            if interfaces["org.bluez.GattCharacteristic1"]["UUID"] == UART_RX_CHARACTERISTIC_UUID:
                target_char = bus.get('org.bluez', path)
                break
    
    if target_char:
        command_str = "LED_ON"
        command_bytes = [ord(c) for c in command_str]
        
        print(f"[Info] コマンド送信: {command_str}")
        try:
            target_char.WriteValue(command_bytes, {})
            print("[Info] 送信完了")
        except Exception as e:
            print(f"[Error] 送信エラー: {e}")
    else:
        print(f"[Error] 送信先のCharacteristic ({UART_RX_CHARACTERISTIC_UUID}) が見つかりません")

if __name__ == '__main__':
    connect_and_send()