#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>

#define MAX_COMMAND_LENGTH 512
#define SAVE_DIRECTORY "/home/matsumoto/bt_attack/Selfmade_smartglass/Connection_BT/Videos"
#define RPICAM_PATH "/home/matsumoto/bt_attack/Smartglass_apps/build/apps/rpicam-vid"

int main() {
    // 1. 保存先ディレクトリを作成
    struct stat st = {0};
    if (stat(SAVE_DIRECTORY, &st) == -1) {
        if (mkdir(SAVE_DIRECTORY, 0755) != 0) {
            perror("Failed to create directory");
            return 1;
        }
    }
    
    // 2. 現在時刻を取得してタイムスタンプを生成
    time_t now;
    struct tm *timeinfo;
    char timestamp[64];
    
    time(&now);
    timeinfo = localtime(&now);
    
    // YYYYMMDD-HHMMSS 形式でフォーマット
    strftime(timestamp, sizeof(timestamp), "%Y%m%d-%H%M%S", timeinfo);
    
    // 3. ファイル名を生成
    char filename[128];
    snprintf(filename, sizeof(filename), "video_%s.h264", timestamp);
    
    // 4. 保存先パスを生成
    char output_path[256];
    snprintf(output_path, sizeof(output_path), "%s/%s", SAVE_DIRECTORY, filename);
    
    // 5. rpicam-vidコマンドを組み立て
    char command[MAX_COMMAND_LENGTH];
    snprintf(command, sizeof(command), 
             "%s -t 10000 --width 1920 --height 1080 -o %s",
             RPICAM_PATH, output_path);
    
    // 6. 実行するコマンドを表示
    printf("実行するコマンド: %s\n", command);
    fprintf(stderr, "実行するコマンド: %s\n", command);
    
    // 7. コマンドを実行
    int result = system(command);
    
    // 8. 実行結果を確認
    if (result == 0) {
        printf("コマンドは正常に実行されました。\n");
        printf("動画ファイルが %s に保存されました。\n", output_path);
    } else {
        printf("コマンドの実行中にエラーが発生しました。\n");
        return 1;
    }
    
    return 0;
}