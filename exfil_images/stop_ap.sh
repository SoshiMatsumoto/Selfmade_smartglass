set -e

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
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
echo "  不正AP停止スクリプト"
echo "========================================"
echo ""

# プロセス停止
log_info "hostapdを停止中..."
killall hostapd 2>/dev/null || true
systemctl stop hostapd 2>/dev/null || true

log_info "dnsmasqを停止中..."
killall dnsmasq 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# NetworkManagerの再有効化
log_info "NetworkManagerにインターフェースを戻しています..."
nmcli device set wlan0 managed yes 2>/dev/null || true

# 設定ファイル削除
log_info "一時ファイルを削除中..."
rm -f /tmp/hostapd_attack.conf
rm -f /tmp/dnsmasq_attack.conf
rm -f /tmp/hostapd.log
rm -f /tmp/dnsmasq.log

echo ""
echo "========================================"
log_info "APを停止しました"
echo "========================================"
echo ""