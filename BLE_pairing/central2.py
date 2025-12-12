import sys
import time
from gi.repository import GLib
from pydbus import SystemBus

# ==========================================
# 設定
# ==========================================
TARGET_MAC = "E4:5F:01:F2:6D:21"
NUS_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
COMMAND_TO_SEND = "LED_ON"

# ==========================================
# Agent (ペアリング自動承認用)
# ==========================================
AGENT_PATH = '/test/agent_initiator'
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

class AutoAgent(object):
    dbus = AGENT_INTERFACE
    def Release(self): pass
    def RequestPinCode(self, device): return "0000"
    def DisplayPinCode(self, device, pincode): pass
    def RequestPasskey(self, device): return 0
    def DisplayPasskey(self, device, passkey, entered): pass
    def RequestConfirmation(self, device, passkey): return 
    def RequestAuthorization(self, device): return
    def AuthorizeService(self, device, uuid): return
    def Cancel(self): pass

class BleController:
    def __init__(self):
        self.bus = SystemBus()
        self.adapter = self.bus.get('org.bluez', '/org/bluez/hci0')
        self.manager = self.bus.get('org.bluez', '/org/bluez')
        self.device_path = f"/org/bluez/hci0/dev_{TARGET_MAC.replace(':', '_')}"
        self.device = None

    def setup_agent(self):
        try:
            agent = AutoAgent()
            self.bus.register_object(AGENT_PATH, agent, None)
            self.manager.RegisterAgent(AGENT_PATH, AGENT_CAPABILITY)
            self.manager.RequestDefaultAgent(AGENT_PATH)
            print("[Info] Agent registered")
        except: pass

    def force_connect(self):
        print(f"[Info] {TARGET_MAC} へ直接接続を試みます (Scan Skip)...")
        
        # 1. 古い情報の削除
        try:
            # 以前のClassic接続情報などが残っていると邪魔なので消す
            bad_device = self.bus.get('org.bluez', self.device_path)
            self.adapter.RemoveDevice(self.device_path)
            print("[Info] キャッシュクリア")
            time.sleep(1)
        except:
            pass

        # 2. 強制接続 (ConnectDeviceメソッド)
        # これを使うと AddressType を指定して接続できる
        connected = False
        try:
            print("[Info] Connecting as Public Address (LE)...")
            self.adapter.ConnectDevice({
                'Address': TARGET_MAC,
                'AddressType': 'public'  # Raspberry Piは通常Public
            })
            connected = True
        except Exception as e:
            print(f"[Warn] Public接続失敗: {e}")
            try:
                print("[Info] Connecting as Random Address (LE)...")
                self.adapter.ConnectDevice({
                    'Address': TARGET_MAC,
                    'AddressType': 'random'
                })
                connected = True
            except Exception as e2:
                print(f"[Error] Random接続失敗: {e2}")

        if not connected:
            return False

        # 3. デバイスオブジェクトの取得待ち
        print("[Info] デバイスオブジェクトの生成を待機中...")
        for i in range(10):
            try:
                self.device = self.bus.get('org.bluez', self.device_path)
                print("[Info] 接続確立！")
                return True
            except:
                time.sleep(0.5)
        
        return False

    def pair_and_send(self):
        if not self.device: return

        # ペアリング
        if not self.device.Paired:
            print("[Info] ペアリング要求...")
            try:
                self.device.Pair()
                print("[Info] ペアリング成功")
            except Exception as e:
                print(f"[Warn] ペアリング警告: {e}")

        # サービス解決待ち
        print("[Info] GATTサービス解決待ち...")
        for i in range(20):
            if self.device.ServicesResolved:
                break
            time.sleep(0.5)

        # 送信
        print("[Info] キャラクタリスティック検索...")
        mngr = self.bus.get('org.bluez', '/')
        objects = mngr.GetManagedObjects()
        target_char = None
        
        for path, interfaces in objects.items():
            if "org.bluez.GattCharacteristic1" in interfaces:
                uuid = interfaces["org.bluez.GattCharacteristic1"]["UUID"]
                if uuid.lower() == NUS_RX_UUID.lower() and path.startswith(self.device_path):
                    target_char = self.bus.get('org.bluez', path)
                    break
        
        if target_char:
            try:
                data = [ord(c) for c in COMMAND_TO_SEND]
                target_char.WriteValue(data, {'type': GLib.Variant('s', 'command')})
                print(f"\n[SUCCESS] コマンド '{COMMAND_TO_SEND}' 送信成功！！！\n")
            except Exception as e:
                print(f"[Error] 送信失敗: {e}")
        else:
            print("[Error] Nordic UART Serviceが見つかりません (GATT解決に失敗した可能性があります)")

    def disconnect(self):
        if self.device:
            try:
                self.device.Disconnect()
                print("[Info] 切断完了")
            except: pass

if __name__ == '__main__':
    controller = BleController()
    try:
        controller.setup_agent()
        if controller.force_connect():
            controller.pair_and_send()
            time.sleep(2)
            controller.disconnect()
        else:
            print("[Fatal] 接続できませんでした。相手の電源を確認してください。")
    except KeyboardInterrupt:
        controller.disconnect()