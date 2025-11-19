This directory is making camera apps for smartglass.

Recording can be started by "START_RECORDING" command from a device connected with bluetooth.

### Smartglass(Server)
For Smartglass programs are "cam_apps_server.c" and "start_rec.c" and "stop_rec.c".

```bash
#How to compile.
#Build the recording program.
gcc -o start_rec start_rec.c
#You should do this because of check the recording program.
./start_rec
#Build the stop recording program.
gcc -o stop_rec stop_rec.c
#You should do this because of check the recording program too.
./stop_rec
#Build the server program.
gcc -o cam_apps_server cam_apps_server.c -lbluetooth
./cam_apps_server
```

#### Stop record without delete PID file.
You must be aware of the inherent dangers and accept full responsibility before compiling this program.

If you compile this, you cannot do recording.
```bash
gcc -o stop_rec_no_delete stop_rec_no_delete.c
```
You can stop recording without delete by choice command 6.

#### You have to get BD_ADDR to connection.
```bash
hciconfig
#You have to memo the Address like "XX:XX:XX:XX:XX:XX"
```

### Attacker(Client)
For Attacker program is client.c

```bash
#How to Compile
gcc -o client client.c -lbluetooth
```

### Command rist

1. START_RECORD - Start video recording

2. STOP_RECORD  - Stop video recording

3. TAKE_PHOTO   - Take a photo

4. STATUS       - Get camera status

5. QUIT         - Disconnect and exit

You cannot see the command 6.

6. STOP_RECORD_NO_DELETE - Stop video recording without delete PID file.
