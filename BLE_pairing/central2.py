import sys
import time
import signal
from gi.repository import GLib
from pydbus import SystemBus

# ==========================================
# 設定エリア (ここを確認してください)
# ==========================================

# ログで見つかったターゲット(Raspberry Pi)のMACアドレス
TARGET_MAC = "E4:5F:01:F2:6D:21"

# Nordic UART Service (NUS) の UUID定義
# 書き込み用 (RX) Characteristic UUID
NUS_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# 送信するコマンド
COMMAND_TO_SEND = "LED_ON"

# ==========================================
# Bluetooth Agent (ペアリング自動承認用)
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
    """ペアリング要求を全て自動でYESと答えるエージェント"""
    dbus = AGENT_INTERFACE
    
    def Release(self): pass
    def RequestPinCode(self, device): return "0000"
    def DisplayPinCode(self, device, pincode): pass
    def RequestPasskey(self, device): return 0
    def DisplayPasskey(self, device, passkey, entered): pass
    def RequestConfirmation(self, device, passkey): return # 自動承認
    def RequestAuthorization(self, device): return
    def AuthorizeService(self, device, uuid): return
    def Cancel(self): pass

# ==========================================
# メイン処理クラス
# ==========================================
class BleController:
    def __init__(self):
        self.bus = SystemBus()
        self.adapter = self.bus.get('org.bluez', '/org/bluez/hci0')
        self.manager = self.bus.get('org.bluez', '/org/bluez')
        self.device_path = f"/org/bluez/hci0/dev_{TARGET_MAC.replace(':', '_')}"
        self.device = None

    def setup_agent(self):
        """エージェントを登録してペアリング処理を自動化する"""
        try:
            agent = AutoAgent()
            self.bus.register_object(AGENT_PATH, agent, None)
            self.manager.RegisterAgent(AGENT_PATH, AGENT_CAPABILITY)
            self.manager.RequestDefaultAgent(AGENT_PATH)
            print("[Info] Agent registered (Just Works mode)")
        except Exception as e:
            print(f"[Warn] Agent registration warning (ignorable if already running): {e}")

    def find_device(self):
        """デバイスを探す（既存なら取得、なければスキャン）"""
        print(f"[Info] ターゲット {TARGET_MAC} を検索中...")
        
        # 1. 既にBlueZが知っているか確認
        try:
            self.device = self.bus.get('org.bluez', self.device_path)
            print("[Info] キャッシュされたデバイスが見つかりました")
            return True
        except KeyError:
            pass

        # 2. スキャン開始
        try:
            self.adapter.StartDiscovery()
            print("[Info] スキャンを開始しました (最大20秒)...")
            
            for i in range(20):
                try:
                    self.device = self.bus.get('org.bluez', self.device_path)
                    print(f"[Info] 発見しました！ ({i+1}秒目)")
                    self.adapter.StopDiscovery()
                    return True
                except KeyError:
                    time.sleep(1)
            
            self.adapter.StopDiscovery()
            print("[Error] デバイスが見つかりませんでした。電源を確認してください。")
            return False
        except Exception as e:
            print(f"[Error] スキャンエラー: {e}")
            return False

    def connect(self):
        """接続とペアリング"""
        if not self.device: return False

        print(f"[Info] {TARGET_MAC} に接続を試みています...")
        try:
            self.device.Connect()
            print("[Info] 接続成功！")
        except Exception as e:
            print(f"[Error] 接続失敗: {e}")
            return False

        # ペアリング確認
        if not self.device.Paired:
            print("[Info] ペアリング中...")
            try:
                self.device.Pair()
                print("[Info] ペアリング成功")
            except Exception as e:
                print(f"[Warn] ペアリング失敗 (接続は維持されています): {e}")
        
        # GATTサービスの解決待ち (超重要)
        print("[Info] サービス解決を待機中...")
        timeout = 0
        while not self.device.ServicesResolved:
            time.sleep(0.5)
            timeout += 1
            if timeout > 20: # 10秒待機
                print("[Warn] サービス解決がタイムアウトしました")
                break
        
        return True

    def send_command(self):
        """Nordic UART Serviceを探して書き込む"""
        print("[Info] キャラクタリスティックを検索中...")
        
        # マネージドオブジェクト全体から目的のUUIDを探す
        mngr = self.bus.get('org.bluez', '/')
        objects = mngr.GetManagedObjects()

        target_char = None
        for path, interfaces in objects.items():
            if "org.bluez.GattCharacteristic1" in interfaces:
                uuid = interfaces["org.bluez.GattCharacteristic1"]["UUID"]
                if uuid.lower() == NUS_RX_UUID.lower():
                    # さらに、このキャラクタリスティックが目的のデバイスのものか確認
                    if path.startswith(self.device_path):
                        target_char = self.bus.get('org.bluez', path)
                        break
        
        if target_char:
            print(f"[Info] 送信対象発見: {NUS_RX_UUID}")
            try:
                # 文字列をバイト列に変換して送信
                data = [ord(c) for c in COMMAND_TO_SEND]
                # WriteValue(bytes, options)
                target_char.WriteValue(data, {'type': GLib.Variant('s', 'command')}) 
                print(f"[Success] コマンド '{COMMAND_TO_SEND}' を送信しました！")
            except Exception as e:
                # 'command' typeがサポートされていない場合、空のdictでリトライ
                try:
                     data = [ord(c) for c in COMMAND_TO_SEND]
                     target_char.WriteValue(data, {})
                     print(f"[Success] コマンド '{COMMAND_TO_SEND}' を送信しました！ (Retry)")
                except Exception as e2:
                    print(f"[Error] 書き込みエラー: {e2}")
        else:
            print(f"[Error] Nordic UART Service ({NUS_RX_UUID}) が見つかりません。")
            print("       ターゲット側のプログラムが正しくNUSをアドバタイズしているか確認してください。")

    def disconnect(self):
        if self.device:
            try:
                self.device.Disconnect()
                print("[Info] 切断しました")
            except:
                pass

# ==========================================
# 実行ブロック
# ==========================================
if __name__ == '__main__':
    controller = BleController()
    
    try:
        # 1. エージェント設定
        controller.setup_agent()
        
        # 2. デバイス検索
        if controller.find_device():
            # 3. 接続
            if controller.connect():
                # 4. コマンド送信
                controller.send_command()
                
                # 少し待ってから切断
                time.sleep(2)
                controller.disconnect()
            else:
                print("接続フェーズで失敗しました")
        else:
            print("デバイスが見つかりませんでした")

    except KeyboardInterrupt:
        print("\n中断されました")
        controller.disconnect()