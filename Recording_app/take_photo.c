#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define MAX_COMMAND_LENGTH 512
#define SAVE_DIRECTORY "Photos" // 保存先ディレクトリ名を変更
// rpicam-still のパスに変更 (同じビルドディレクトリにあると仮定しています)
#define RPICAM_PATH "/home/matsumoto/bt_attack/Smartglass_apps/build/apps/rpicam-still"

int main() {
    // 静止画撮影は一瞬で終わるため、PIDチェック（重複起動防止）は基本的に不要です。
    // 必要であれば追加可能ですが、ここではシンプルにするために削除しています。
    
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
    
    // 3. ファイル名を生成 (拡張子を .jpg に変更)
    char filename[128];
    snprintf(filename, sizeof(filename), "photo_%s.jpg", timestamp);
    
    // 4. 保存先パスを生成
    char output_path[256];
    snprintf(output_path, sizeof(output_path), "%s/%s", SAVE_DIRECTORY, filename);
    
    // 5. rpicam-stillコマンドを組み立て
    // 変更点:
    // - rpicam-still を使用
    // - "-t 1000": 露出調整のため1秒(1000ms)待ってから撮影 (即時撮影したい場合は -t 1 ですが画質が落ちる可能性があります)
    // - "&" (バックグラウンド実行) は削除。撮影完了まで待ちます。
    char command[MAX_COMMAND_LENGTH];
    snprintf(command, sizeof(command), 
             "%s -t 1000 --width 1920 --height 1080 -o %s",
             RPICAM_PATH, output_path);
    
    // 6. 実行するコマンドを表示
    printf("撮影を開始します...\n");
    printf("実行コマンド: %s\n", command);
    
    // 7. コマンドを実行 (撮影が終わるまでここでブロックされます)
    int result = system(command);
    
    // 8. 実行結果を確認
    if (result != 0) {
        printf("エラー: 写真撮影に失敗しました。\n");
        return 1;
    }
    
    printf("撮影完了: %s に保存されました。\n", output_path);
    
    return 0;
}