set -e

# 設定
INTERFACE="wlan0"
IP_ADDRESS="192.168.4.1"
NETMASK="255.255.255.0"
DHCP_RANGE="192.168.4.2,192.168.4.20"
SSID="matsumoto_AP_danger"

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# rootチェック
if [ "$EUID" -ne 0 ]; then
    log_error "このスクリプトはroot権限で実行する必要があります"
    echo "sudo $0 を実行してください"
    exit 1
fi

echo "========================================"
echo "  不正AP起動スクリプト"
echo "========================================"
echo "SSID: $SSID"
echo "IP: $IP_ADDRESS"
echo "Interface: $INTERFACE"
echo "========================================"
echo ""

# 必要なパッケージの確認
log_info "必要なパッケージを確認中..."
if ! command -v hostapd &> /dev/null; then
    log_error "hostapd がインストールされていません"
    echo "sudo apt-get install hostapd でインストールしてください"
    exit 1
fi

if ! command -v dnsmasq &> /dev/null; then
    log_error "dnsmasq がインストールされていません"
    echo "sudo apt-get install dnsmasq でインストールしてください"
    exit 1
fi

# 既存プロセスの停止
log_info "既存のプロセスを停止中..."
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true
killall hostapd 2>/dev/null || true
killall dnsmasq 2>/dev/null || true
sleep 1

# NetworkManagerの無効化（インターフェース競合回避）
log_info "NetworkManagerからインターフェースを解放中..."
nmcli device set $INTERFACE managed no 2>/dev/null || true
sleep 1

# インターフェースの設定
log_info "インターフェースに静的IPを設定中..."
ip addr flush dev $INTERFACE
ip addr add $IP_ADDRESS/24 dev $INTERFACE
ip link set $INTERFACE up

# hostapd設定ファイルの生成
log_info "hostapd設定ファイルを生成中..."
HOSTAPD_CONF="/tmp/hostapd_attack.conf"
cat > $HOSTAPD_CONF <<EOF
interface=$INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
EOF

# dnsmasq設定ファイルの生成
log_info "dnsmasq設定ファイルを生成中..."
DNSMASQ_CONF="/tmp/dnsmasq_attack.conf"
cat > $DNSMASQ_CONF <<EOF
interface=$INTERFACE
dhcp-range=$DHCP_RANGE,$NETMASK,24h
dhcp-option=3,$IP_ADDRESS
dhcp-option=6,$IP_ADDRESS
server=8.8.8.8
log-queries
log-dhcp
bind-interfaces
EOF

# IP forwarding有効化（オプション）
log_info "IP forwardingを有効化中..."
echo 1 > /proc/sys/net/ipv4/ip_forward

# hostapdの起動
log_info "hostapdを起動中..."
hostapd -B $HOSTAPD_CONF > /tmp/hostapd.log 2>&1
if [ $? -eq 0 ]; then
    log_info "hostapd起動成功"
else
    log_error "hostapd起動失敗"
    cat /tmp/hostapd.log
    exit 1
fi
sleep 2

# dnsmasqの起動
log_info "dnsmasqを起動中..."
dnsmasq -C $DNSMASQ_CONF > /tmp/dnsmasq.log 2>&1
if [ $? -eq 0 ]; then
    log_info "dnsmasq起動成功"
else
    log_error "dnsmasq起動失敗"
    cat /tmp/dnsmasq.log
    exit 1
fi
sleep 1

# 状態確認
log_info "AP状態を確認中..."
echo ""
echo "========================================"
echo "  APが正常に起動しました"
echo "========================================"
echo "SSID: $SSID"
echo "IP Address: $IP_ADDRESS"
echo "DHCP Range: $DHCP_RANGE"
echo "========================================"
echo ""
echo "接続されたデバイスを確認:"
echo "  tail -f /var/lib/misc/dnsmasq.leases"
echo ""
echo "hostapdログ: /tmp/hostapd.log"
echo "dnsmasqログ: /tmp/dnsmasq.log"
echo ""
echo "APを停止するには:"
echo "  sudo $0 stop"
echo "または"
echo "  sudo killall hostapd dnsmasq"
echo ""