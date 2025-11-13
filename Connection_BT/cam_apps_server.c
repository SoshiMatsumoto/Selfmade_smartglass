#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>
#include <string.h>
#include <errno.h>

#define SERVICE_NAME "RaspiCameraControl"
#define SERVICE_UUID "00001101-0000-1000-8000-00805F9B34FB" // Serial Port Profile UUID

int main(int argc, char **argv)
{
    struct sockaddr_rc loc_addr = { 0 }, rem_addr = { 0 };
    char buf[1024] = { 0 };
    int s, client, bytes_read;
    socklen_t opt = sizeof(rem_addr);

    printf("=== Raspberry Pi Camera Server ===\n");
    printf("Waiting for connection from controller...\n\n");

    // RFCOMMソケットの作成
    s = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (s < 0) {
        perror("Socket creation failed");
        return 1;
    }

    // ローカルアドレスの設定
    loc_addr.rc_family = AF_BLUETOOTH;
    loc_addr.rc_bdaddr = *BDADDR_ANY;
    loc_addr.rc_channel = (uint8_t) 1; // RFCOMMチャンネル1を使用

    // ソケットのバインド
    if (bind(s, (struct sockaddr *)&loc_addr, sizeof(loc_addr)) < 0) {
        perror("Bind failed");
        close(s);
        return 1;
    }

    // リスニング開始
    if (listen(s, 1) < 0) {
        perror("Listen failed");
        close(s);
        return 1;
    }

    printf("Server is listening on RFCOMM channel %d\n", loc_addr.rc_channel);
    printf("Service UUID: %s\n\n", SERVICE_UUID);

    // クライアント接続の受け入れ
    client = accept(s, (struct sockaddr *)&rem_addr, &opt);
    if (client < 0) {
        perror("Accept failed");
        close(s);
        return 1;
    }

    // 接続元のアドレスを表示
    char addr_str[18];
    ba2str(&rem_addr.rc_bdaddr, addr_str);
    printf("✓ Connected from: %s\n\n", addr_str);

    // コマンド受信ループ
    while (1) {
        memset(buf, 0, sizeof(buf));
        bytes_read = read(client, buf, sizeof(buf) - 1);
        
        if (bytes_read > 0) {
            printf("Received command: %s\n", buf);
            
            // コマンド処理
            if (strcmp(buf, "START_RECORD") == 0) {
                printf("→ Action: Starting video recording...\n");
                
                // start_rec プログラムを実行（同じディレクトリ内）
                int ret = system("./start_rec &");
                
                if (ret == 0) {
                    char *response = "OK:RECORDING_STARTED";
                    write(client, response, strlen(response));
                } else {
                    printf("   ERROR: Failed to start recording (return code: %d)\n", ret);
                    char *response = "ERROR:RECORDING_FAILED";
                    write(client, response, strlen(response));
                }
            }
            else if (strcmp(buf, "STOP_RECORD") == 0) {
                printf("→ Action: Stopping video recording...\n");
                char *response = "OK:RECORDING_STOPPED";
                write(client, response, strlen(response));
            }
            else if (strcmp(buf, "TAKE_PHOTO") == 0) {
                printf("→ Action: Taking photo...\n");
                char *response = "OK:PHOTO_TAKEN";
                write(client, response, strlen(response));
            }
            else if (strcmp(buf, "STATUS") == 0) {
                printf("→ Action: Sending status...\n");
                char *response = "OK:READY";
                write(client, response, strlen(response));
            }
            else if (strcmp(buf, "QUIT") == 0) {
                printf("→ Received quit command. Closing connection...\n");
                break;
            }
            else {
                printf("→ Unknown command\n");
                char *response = "ERROR:UNKNOWN_COMMAND";
                write(client, response, strlen(response));
            }
            printf("\n");
        }
        else if (bytes_read == 0) {
            printf("Client disconnected\n");
            break;
        }
        else {
            perror("Read error");
            break;
        }
    }

    // クリーンアップ
    close(client);
    close(s);
    printf("Server shutdown\n");
    
    return 0;
}