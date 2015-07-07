Python nrf51822 DFU uploader
============================

Wrapper for bluez gatttool using pexpect to achive DFU 
uploads to the nrf51822. 

The script does not handle any notifications given by the 
peer as it is strictly not needed for simple uploads.

System:
* Linux raspian - kernel 3.12.22 or later
* bluez - 5.4 or later

See https://learn.adafruit.com/pibeacon-ibeacon-with-a-raspberry-pi/setting-up-the-pi for details on building bluez.

Prerequisite -  

    sudo pip install pexpect
    sudo pip install intelhex

Usage -  
    sudo ./dfu.py -f \<hex_file> -d \<dat_file> -a \<ble-address\>  or  
    sudo ./dfu.py -z \<zip_file> -a \<ble-address\> 
    
Example -  

    > sudo ./dfu.py -f ~/application.hex -d ~/application.dat -a EF:FF:D2:92:9C:2A

or

    > sudo ./dfu.py -z ~/application.zip -a EF:FF:D2:92:9C:2A  

To figure out the address of DfuTarg do a 'hcitool lescan' - 

    $ sudo hcitool -i hci0 lescan  
    LE Scan ...   
    CD:E3:4A:47:1C:E4 DfuTarg  
    CD:E3:4A:47:1C:E4 (unknown) 
