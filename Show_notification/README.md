This repository is for the PoC of silent recording attack.

When you do this PoC, the following scenario is gone.

1. Smartglass (Raspberry pi) shows a notification.
2. Then start the recording silently.
3. The video is saved in Show_notification/Videos directory.

The mechanism is a command injection.

Payload of the notification contains a path of start_rec and stop_rec.
The default recording time is 30 sec.
```bash
gcc -o notification_server notification_server.c -lbluetooth

./notification_server

#Get BD_ADDR.
hciconfig
```
```bash
gcc -o attacker attacker.c
./attacker XX:XX:XX:XX:XX:XX "<BD_ADDR>"
```