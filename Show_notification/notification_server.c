/*
 * Bluetooth Classic RFCOMM Server (Vulnerable)
 * スマートグラス通知サーバー（脆弱性デモ用）
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <sys/socket.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>

#define RFCOMM_CHANNEL 1
#define BUFFER_SIZE 1024

void log_info(const char *format, ...) {
    va_list args;
    va_start(args, format);
    printf("[INFO] ");
    vprintf(format, args);
    printf("\n");
    fflush(stdout);
    va_end(args);
}

void handle_notification(const char *data) {
    log_info("通知を受信しました: %s", data);
    
    /* =================================================================
     * 【ここが脆弱性！】
     * 受信したテキストをサニタイズせず、そのままOSコマンドに埋め込んでいる。
     * 開発者の意図: echoコマンドを使ってログや画面に表示したいだけ。
     * ================================================================= */
    
    char command[BUFFER_SIZE + 128];

    // DISPLAY環境変数を指定しないと、system()経由でGUIが表示されないことが多いです
    // notify-send "タイトル" "メッセージ" の形式にします
    snprintf(command, sizeof(command), 
             "export DISPLAY=:0; notify-send \"Notification\" \"%s\"", data);
    
    log_info("[SYSTEM] 実行するコマンド: %s", command);
    
    /* OSコマンドの実行 (ここで攻撃コードが走る) */
    system(command);
}

int main(int argc, char *argv[]) {
    int server_sock, client_sock;
    struct sockaddr_rc local_addr = {0};
    struct sockaddr_rc remote_addr = {0};
    socklen_t addr_len = sizeof(remote_addr);
    char buffer[BUFFER_SIZE] = {0};
    char local_bdaddr[18];
    
    log_info("スマートグラス(Bluetooth Server)を起動します...");


    /* 通知デーモンの準備 */
    // 既に起動している場合はエラー出力が出るだけなので、2> /dev/null で捨てています
    system("export DISPLAY=:0; dunst > /dev/null 2>&1 &");
    sleep(1); // 起動待ち
    /* ----------------------------- */
    
    /* RFCOMMソケットの作成 */
    server_sock = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (server_sock < 0) {
        perror("ソケット作成エラー");
        return 1;
    }
    
    /* ローカルアドレスの設定 */
    local_addr.rc_family = AF_BLUETOOTH;
    local_addr.rc_bdaddr = *BDADDR_ANY;
    local_addr.rc_channel = RFCOMM_CHANNEL;
    
    /* バインド */
    if (bind(server_sock, (struct sockaddr *)&local_addr, sizeof(local_addr)) < 0) {
        perror("バインドエラー");
        close(server_sock);
        return 1;
    }
    
    /* リスン */
    if (listen(server_sock, 1) < 0) {
        perror("リスンエラー");
        close(server_sock);
        return 1;
    }
    
    /* 自分のBDアドレスを表示 */
    ba2str(&local_addr.rc_bdaddr, local_bdaddr);
    log_info("SmartGlass_Demo として起動しました");
    log_info("RFCOMMチャンネル: %d", RFCOMM_CHANNEL);
    log_info("スマホからの接続を待機中...");
    printf("\n");
    printf("攻撃側で以下のコマンドを実行してください:\n");
    printf("  sudo ./attacker <このデバイスのBDアドレス>\n");
    printf("\nBDアドレスの確認方法:\n");
    printf("  hciconfig\n");
    printf("\n");
    
    /* 接続待ち受けループ */
    while (1) {
        log_info("接続待機中...");
        
        client_sock = accept(server_sock, (struct sockaddr *)&remote_addr, &addr_len);
        if (client_sock < 0) {
            perror("接続受付エラー");
            continue;
        }
        
        char remote_bdaddr[18];
        ba2str(&remote_addr.rc_bdaddr, remote_bdaddr);
        log_info("接続を受け付けました: %s", remote_bdaddr);
        
        /* データ受信 */
        memset(buffer, 0, sizeof(buffer));
        int bytes_read = read(client_sock, buffer, sizeof(buffer) - 1);
        
        if (bytes_read > 0) {
            buffer[bytes_read] = '\0';
            handle_notification(buffer);
        } else if (bytes_read < 0) {
            perror("読み込みエラー");
        }
        
        /* クライアント切断 */
        close(client_sock);
        log_info("クライアントが切断しました");
        printf("\n");
    }
    
    close(server_sock);
    return 0;
}