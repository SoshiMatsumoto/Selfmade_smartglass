This directory is implement the exfil image files attack.

The attacker start the fake Access Point named "matsumoto_AP_danger".

After that, the attacker open the server for appload files.

We use Show_notification server for doing attack.

You have to follow the steps bellow.

### Attacker
Start the fake AP and open the server.
```bash
# start fake Access Point.
sudo ./start_ap.sh
# open the server.
python3 image_receiver.py
```
After starting notification_server.c by server device, you can do this.
```bash
# You have to make the Assets folder to saving files.
# After that, get the path of directory and editing the VIDEO_DIR path in attacker.py.
# If you need, you have to change the TARGET_MAC in attacker.py by "hciconfig".
python3 attacker.py
```

### Server
You have to compile notification_server.c in Show_notification directory.