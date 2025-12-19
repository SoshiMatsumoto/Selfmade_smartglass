This is a directory of BLE_pairing by JustWorks.

BLE pairing successed.

You can pair by BLE on Raspberrypi doing follow commands.

#### Peripheral device
```bash
bluetoothctl
agent NoInputNoOutput
discoverable on
pairable on
advertise on
```


#### Central device
```bash
# If you didn't do this, OS choose Bluetooth Classic to connect. 
sudo btmgmt bredr off
bluetoothctl
agent NoInputNoOutput
scan on
pair <MAC_ADDR>
```

central2.py is scripted program of upper commands.

peripheral.py and central.py is dead.

peripheral2.py is ready to connect program of peripheral device.
I stopped this because I think it is not necessary.

central3.py is hybrid pairing of BLE and bluetooth classic.
I stopped this because the same reason to peri2.py I thought.