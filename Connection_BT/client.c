#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>
#include <string.h>
#include <stdlib.h>

#define SERVICE_UUID "00001101-0000-1000-8000-00805F9B34FB"

void print_menu() {
    printf("\n=== Camera Control Menu ===\n");
    printf("1. START_RECORD - Start video recording\n");
    printf("2. STOP_RECORD  - Stop video recording\n");
    printf("3. TAKE_PHOTO   - Take a photo\n");
    printf("4. STATUS       - Get camera status\n");
    printf("5. QUIT         - Disconnect and exit\n");
    printf("Choice: ");
}

int main(int argc, char **argv)
{
    struct sockaddr_rc addr = { 0 };
    int s, status;
    char dest[18];
    char buf[1024] = { 0 };
    
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <bluetooth_address>\n", argv[0]);
        fprintf(stderr, "Example: %s E4:5F:01:F2:6D:21\n", argv[0]);
        return 1;
    }

    strncpy(dest, argv[1], 18);
    
    printf("=== Raspberry Pi Camera Controller ===\n");
    printf("Target camera: %s\n\n", dest);

    // RFCOMMソケットの作成
    s = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (s < 0) {
        perror("Socket creation failed");
        return 1;
    }

    // 接続先アドレスの設定
    addr.rc_family = AF_BLUETOOTH;
    addr.rc_channel = (uint8_t) 1;
    str2ba(dest, &addr.rc_bdaddr);

    // カメラサーバーに接続
    printf("Connecting to camera server...\n");
    status = connect(s, (struct sockaddr *)&addr, sizeof(addr));

    if (status == 0) {
        printf("✓ Connected successfully!\n");
    } else {
        perror("Connection failed");
        close(s);
        return 1;
    }

    // コマンド送信ループ
    while (1) {
        print_menu();
        
        int choice;
        if (scanf("%d", &choice) != 1) {
            // 入力バッファをクリア
            while (getchar() != '\n');
            printf("Invalid input. Please enter a number.\n");
            continue;
        }
        while (getchar() != '\n'); // 改行を消費

        char *command = NULL;
        switch (choice) {
            case 1:
                command = "START_RECORD";
                break;
            case 2:
                command = "STOP_RECORD";
                break;
            case 3:
                command = "TAKE_PHOTO";
                break;
            case 4:
                command = "STATUS";
                break;
            case 5:
                command = "QUIT";
                break;
            default:
                printf("Invalid choice. Please try again.\n");
                continue;
        }

        // コマンド送信
        printf("\nSending command: %s\n", command);
        status = write(s, command, strlen(command));
        
        if (status < 0) {
            perror("Write failed");
            break;
        }

        if (strcmp(command, "QUIT") == 0) {
            printf("Disconnecting...\n");
            break;
        }

        // レスポンス受信
        memset(buf, 0, sizeof(buf));
        status = read(s, buf, sizeof(buf) - 1);
        
        if (status > 0) {
            printf("Response: %s\n", buf);
        } else if (status == 0) {
            printf("Server disconnected\n");
            break;
        } else {
            perror("Read failed");
            break;
        }
    }

    // クリーンアップ
    close(s);
    printf("Client shutdown\n");
    
    return 0;
}