This directory is making camera apps for smartglass.

Recording can be started by "START_RECORDING" command from a device connected with bluetooth.

You have to do some following method.

### Smartglass(Server)
For Smartglass programs are "cam_apps_server.c" and "client.c".

```bash
#How to compile.
#Build the recording program.
gcc -o start_rec start_rec.c
#You should do this because of check the recording program.
./start_rec
#Build the server program.
gcc -o cam_apps_server cam_apps_server.c -lbluetooth
./cam_apps_server
```

You have to get BD_ADDR to connection.
```bash
hciconfig
#You have to memo the Address like "XX:XX:XX:XX:XX:XX"
```

### Attacker(Client)
For Attacker program is client.c

```bash
#How to Compile
gcc -o client client.c
```