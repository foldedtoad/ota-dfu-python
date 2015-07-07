Python nrf51822 DFU uploader
============================

Wrapper for bluez gatttool using pexpect to achive DFU uploads to the nrf51822. 

The script does not handle any notifications given by the 
peer as it is strictly not needed for simple uploads.

System:
* Linux raspian - kernel 3.12.22 or later
* bluez - 5.4 or later

See https://learn.adafruit.com/pibeacon-ibeacon-with-a-raspberry-pi/setting-up-the-pi for details on building bluez.

This project assumes you are developing on a Linux/Unix or OSX system and deploying to a Raspberry Pi (Raspian) system. Development on Windows systems should be OK, but it hasn't been (nor will be) tested. 

Prerequisite -  

    sudo pip install pexpect
    sudo pip install intelhex

Firmware Build Requirement -  
* Your nRF51 firmware build method will produce either a firmware hex or bin file named "application.hex" or "application.bin".  This naming convention is per Nordics DFU specification, which is use by this DFU server as well as the Android Master Control Panel DFU, and iOS DFU app.  
* Your nRF51 firmware build method will produce an Init file (aka "application.dat".  Again, this is per Nordic's naming conventions. 

The "gen_dat" Utility -  
The gen_dat utility will read your build method's hex file and produce a dat file.  The utility is written the C-language, but should be easy to rebuild: just follow the directions at the top of the source file. Ideally, you would incorporate the gen_dat utility into your build system so that your build method will generate the dat file for each build.  

Below is a snippet showing how you might use the gen_dat utility in a makefile. The "application.mk" file shows a more complete example. This makefile example shows how the gen_dat and zip files are integrated into the build process.  It is an example, and you must customize it to your requirements.

    GENZIP   := zip
    GENDAT   := ./gen_dat
    
    # Create .dat file from the .bin file
    gendat: 
        @echo Preparing: application.dat
        $(NO_ECHO)$(GENDAT) $(OUTPUT_BINARY_DIRECTORY)/application.bin $(OUTPUT_BINARY_DIRECTORY)/application.dat 
    
    # Create .zip file from .bin and .dat files
    genzip: 
	@echo Preparing: $(OUTPUT_NAME).zip
	-@$(GENZIP) -j $(OUTPUT_BINARY_DIRECTORY)/application.zip $(OUTPUT_BINARY_DIRECTORY)/application.bin $(OUTPUT_BINARY_DIRECTORY)/application.dat


Usage -
There are two ways to speicify firmware files for this OTA-DFU server. Either by specifying both the <hex or bin> file with the dat file, or more easily by the zip file, which contains both the hex and dat files.  
The new "zip file" form is encouraged by Nordic, but the older hex+dat file methods should still work.  


Usage Examples -  

    > sudo ./dfu.py -f ~/application.hex -d ~/application.dat -a EF:FF:D2:92:9C:2A

or

    > sudo ./dfu.py -z ~/application.zip -a EF:FF:D2:92:9C:2A  

To figure out the address of DfuTarg do a 'hcitool lescan' - 

    $ sudo hcitool -i hci0 lescan  
    LE Scan ...   
    CD:E3:4A:47:1C:E4 DfuTarg  
    CD:E3:4A:47:1C:E4 (unknown) 


Example of dfu.py output -

    pi@raspberrypi ~/src/ota-dfu/ $ sudo ./dfu.py -z application_debug_1435008894.zip -a EF:FF:D2:92:9C:2A
    DFU Server start
    unzip_dir: /tmp/application_debug_1435008894_nzjesh
    input_setup
    bin array size:  72352
    scan_and_connect
    dfu_send_image
    [0, 0, 0, 0, 0, 0, 0, 0, 160, 26, 1, 0]
    Sending hex file size
    oper: RESPONSE, proc: START, status: SUCCESS
    dfu_send_info
    PKT_RCPT:      200
    PKT_RCPT:      400
    PKT_RCPT:      600
    PKT_RCPT:      800
    PKT_RCPT:     1000
    PKT_RCPT:     1200
    PKT_RCPT:     1400
    PKT_RCPT:     1600
    PKT_RCPT:     1800
    PKT_RCPT:     2000
    PKT_RCPT:     2200
    PKT_RCPT:     2400
    PKT_RCPT:     2600
    PKT_RCPT:     2800
    PKT_RCPT:     3000
      ...
      ...
      ...
    PKT_RCPT:    69800
    PKT_RCPT:    70000
    PKT_RCPT:    70200
    PKT_RCPT:    70400
    PKT_RCPT:    70600
    PKT_RCPT:    70800
    PKT_RCPT:    71000
    PKT_RCPT:    71200
    PKT_RCPT:    71400
    PKT_RCPT:    71600
    PKT_RCPT:    71800
    PKT_RCPT:    72000
    PKT_RCPT:    72200
    State timeout
    DFU Server done
