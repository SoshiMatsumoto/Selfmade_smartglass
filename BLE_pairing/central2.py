import sys
import time
from gi.repository import GLib
from pydbus import SystemBus

# ==========================================
# 設定エリア
# ==========================================
TARGET_MAC = "E4:5F:01:F2:6D:21"
NUS_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
COMMAND_TO_SEND = "LED_ON"

# ==========================================
# Agent (Just Works) - 変更なし
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
        try:
            self.adapter = self.bus.get('org.bluez', '/org/bluez/hci0')
            self.manager = self.bus.get('org.bluez', '/org/bluez')
        except Exception as e:
            print(f"[Fatal] Bluetoothアダプタが見つかりません: {e}")
            sys.exit(1)
        
        self.device_path = f"/org/bluez/hci0/dev_{TARGET_MAC.replace(':', '_')}"
        self.device = None

    def setup_agent(self):
        try:
            agent = AutoAgent()
            self.bus.register_object(AGENT_PATH, agent, None)
            self.manager.RegisterAgent(AGENT_PATH, AGENT_CAPABILITY)
            self.manager.RequestDefaultAgent(AGENT_PATH)
            print("[Info] Agent registered")
        except Exception:
            pass 

    def find_device(self):
        print(f"[Info] {TARGET_MAC} を検索中 (BLE強制)...")
        
        # ★★★ ここが修正ポイント ★★★
        # Classic Bluetoothを無視して、BLEだけを探すフィルタを適用
        try:
            filter_args = {
                'Transport': GLib.Variant('s', 'le'), # 'le' = Low Energy only
                'DuplicateData': GLib.Variant('b', True)
            }
            self.adapter.SetDiscoveryFilter(filter_args)
            print("[Info] BLE専用フィルタを適用しました")
        except Exception as e:
            print(f"[Warn] フィルタ適用失敗: {e}")

        # 既存のデバイスキャッシュがあれば削除する（Classicとして認識されているのを防ぐため）
        try:
            existing_device = self.bus.get('org.bluez', self.device_path)
            self.adapter.RemoveDevice(self.device_path)
            print("[Info] 古いキャッシュを削除しました")
        except:
            pass

        # スキャン開始
        try:
            self.adapter.StartDiscovery()
            
            found = False
            for i in range(20): # 20秒待機
                try:
                    self.device = self.bus.get('org.bluez', self.device_path)
                    # デバイスが見つかっても、AddressTypeが public/random (BLE) か確認するとなお良い
                    print(f"[Info] デバイスを発見！ ({i+1}秒目)")
                    found = True
                    break
                except KeyError:
                    time.sleep(1)
            
            self.adapter.StopDiscovery()
            return found

        except Exception as e:
            print(f"[Error] スキャンエラー: {e}")
            return False

    def connect(self):
        if not self.device: return False

        print(f"[Info] 接続開始...")
        try:
            # BLEとして接続
            self.device.Connect()
            print("[Info] 接続成功！")
        except Exception as e:
            print(f"[Error] 接続失敗: {e}")
            return False

        # ペアリング
        if not self.device.Paired:
            print("[Info] ペアリング中...")
            try:
                self.device.Pair()
                print("[Info] ペアリング成功")
            except Exception as e:
                print(f"[Warn] ペアリング失敗 (接続は維持): {e}")
        
        # サービス解決待ち
        print("[Info] サービス解決を待機中...")
        timeout = 0
        while not self.device.ServicesResolved:
            time.sleep(0.5)
            timeout += 1
            if timeout > 20:
                print("[Warn] タイムアウト")
                break
        return True

    def send_command(self):
        print("[Info] NUS RXキャラクタリスティックを検索...")
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
                # WriteValueにtypeオプションを追加
                target_char.WriteValue(data, {'type': GLib.Variant('s', 'command')})
                print(f"[Success] '{COMMAND_TO_SEND}' を送信しました！")
            except Exception as e:
                 # リトライ（WriteRequest）
                try:
                    data = [ord(c) for c in COMMAND_TO_SEND]
                    target_char.WriteValue(data, {})
                    print(f"[Success] '{COMMAND_TO_SEND}' を送信しました！(Retry)")
                except Exception as e2:
                    print(f"[Error] 送信失敗: {e2}")
        else:
            print(f"[Error] NUSが見つかりません。")

    def disconnect(self):
        if self.device:
            try:
                self.device.Disconnect()
                print("[Info] 切断しました")
            except: pass

if __name__ == '__main__':
    controller = BleController()
    try:
        controller.setup_agent()
        if controller.find_device():
            if controller.connect():
                controller.send_command()
                time.sleep(2)
                controller.disconnect()
        else:
            print("デバイスが見つかりませんでした")
    except KeyboardInterrupt:
        controller.disconnect()