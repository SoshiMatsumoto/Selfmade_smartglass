#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>

#define PID_FILE "/tmp/recording.pid"

int main() {
    // 1. PIDファイルの存在確認
    FILE *pid_file = fopen(PID_FILE, "r");
    if (pid_file == NULL) {
        printf("エラー: 録画中のプロセスが見つかりません。\n");
        return 1;
    }
    
    // 2. PIDを読み込む
    char pid_str[32];
    if (fgets(pid_str, sizeof(pid_str), pid_file) == NULL) {
        printf("エラー: PIDファイルの読み込みに失敗しました。\n");
        fclose(pid_file);
        return 1;
    }
    fclose(pid_file);
    
    // 改行を削除
    pid_str[strcspn(pid_str, "\n")] = 0;
    
    // 3. PIDを整数に変換
    int pid = atoi(pid_str);
    if (pid <= 0) {
        printf("エラー: 無効なPIDです。\n");
        // remove(PID_FILE); // 削除しない
        return 1;
    }
    
    printf("録画を停止します。PID: %d\n", pid);
    
    // 4. プロセスが存在するか確認
    if (kill(pid, 0) != 0) {
        printf("警告: プロセスが既に終了しています。\n");
        // remove(PID_FILE); // 削除しない
        return 1;
    }
    
    // 5. SIGINTシグナルを送信（Ctrl+Cと同じ）
    if (kill(pid, SIGINT) == 0) {
        printf("録画停止シグナルを送信しました。\n");
        
        // プロセスが終了するまで少し待つ
        sleep(2);
        
        // まだ動いている場合はSIGTERMを送信
        if (kill(pid, 0) == 0) {
            printf("プロセスがまだ動いています。強制終了します。\n");
            kill(pid, SIGTERM);
            sleep(1);
        }
        
        printf("録画を停止しました。\n");
    } else {
        printf("エラー: プロセスの停止に失敗しました。\n");
        // remove(PID_FILE); // 削除しない
        return 1;
    }
    
    // 6. PIDファイルを削除しない（コメントアウト）
    /*
    if (remove(PID_FILE) == 0) {
        printf("PIDファイルを削除しました。\n");
    } else {
        printf("警告: PIDファイルの削除に失敗しました。\n");
    }
    */
    printf("PIDファイルは保持されます。\n");
    
    return 0;
}