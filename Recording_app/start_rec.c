#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define MAX_COMMAND_LENGTH 512
#define SAVE_DIRECTORY "Videos"
#define RPICAM_PATH "/home/matsumoto/bt_attack/Smartglass_apps/build/apps/rpicam-vid"
#define PID_FILE "/tmp/recording.pid"

int main() {
    // 1. 既に録画中かチェック
    FILE *pid_check = fopen(PID_FILE, "r");
    if (pid_check != NULL) {
        fclose(pid_check);
        printf("エラー: 既に録画中です。先にSTOP_RECORDを実行してください。\n");
        return 1;
    }
    
    // 2. 保存先ディレクトリを作成
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
    
    // 5. rpicam-vidコマンドを組み立て（バックグラウンド実行）
    char command[MAX_COMMAND_LENGTH];
    snprintf(command, sizeof(command), 
             "%s -t 0 --width 1920 --height 1080 -o %s &",
             RPICAM_PATH, output_path);
    
    // 6. 実行するコマンドを表示
    printf("実行するコマンド: %s\n", command);
    fprintf(stderr, "実行するコマンド: %s\n", command);
    
    // 7. コマンドを実行
    int result = system(command);
    
    // 8. 実行結果を確認
    if (result != 0) {
        printf("コマンドの実行中にエラーが発生しました。\n");
        return 1;
    }
    
    // 9. 少し待ってからプロセスIDを取得
    sleep(1);
    
    // 10. rpicam-vidのプロセスIDを取得してファイルに保存
    FILE *pid_cmd = popen("pgrep -n rpicam-vid", "r");
    if (pid_cmd == NULL) {
        printf("エラー: プロセスIDの取得に失敗しました。\n");
        return 1;
    }
    
    char pid_str[32];
    if (fgets(pid_str, sizeof(pid_str), pid_cmd) != NULL) {
        // 改行を削除
        pid_str[strcspn(pid_str, "\n")] = 0;
        
        // PIDファイルに保存
        FILE *pid_file = fopen(PID_FILE, "w");
        if (pid_file == NULL) {
            printf("エラー: PIDファイルの作成に失敗しました。\n");
            pclose(pid_cmd);
            return 1;
        }
        
        fprintf(pid_file, "%s", pid_str);
        fclose(pid_file);
        
        printf("録画を開始しました。PID: %s\n", pid_str);
        printf("動画ファイルは %s に保存されます。\n", output_path);
    } else {
        printf("エラー: プロセスIDの取得に失敗しました。\n");
        pclose(pid_cmd);
        return 1;
    }
    
    pclose(pid_cmd);
    
    return 0;
}