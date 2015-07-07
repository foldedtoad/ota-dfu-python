#!/usr/bin/env python
#------------------------------------------------------------------------------
# DFU Server for Nordic nRF51 based systems.
# Conforms to nRF51_SDK 8.0 BLE_DFU requirements.
#------------------------------------------------------------------------------
import os
import sys
import pexpect
import optparse
import time

from intelhex import IntelHex
from array    import array
from unpacker import Unpacker

# DFU Opcodes
class Commands:
    START_DFU                    = 1
    INITIALIZE_DFU               = 2
    RECEIVE_FIRMWARE_IMAGE       = 3
    VALIDATE_FIRMWARE_IMAGE      = 4
    ACTIVATE_FIRMWARE_AND_RESET  = 5
    SYSTEM_RESET                 = 6
    PKT_RCPT_NOTIF_REQ           = 8

# DFU Procedures values
DFU_proc_to_str = {
    "01" : "START",
    "02" : "INIT",
    "03" : "RECEIVE_APP",
    "04" : "VALIDATE",
    "08" : "PKT_RCPT_REQ",
}

# DFU Operations values
DFU_oper_to_str = {
    "01" : "START_DFU",
    "02" : "RECEIVE_INIT",
    "03" : "RECEIVE_FW",
    "04" : "VALIDATE",
    "05" : "ACTIVATE_N_RESET",
    "06" : "SYS_RESET",
    "07" : "IMAGE_SIZE_REQ",
    "08" : "PKT_RCPT_REQ",
    "10" : "RESPONSE",
    "11" : "PKT_RCPT_NOTIF",
}

# DFU Status values
DFU_status_to_str = {
    "01" : "SUCCESS",
    "02" : "INVALID_STATE",
    "03" : "NOT_SUPPORTED",
    "04" : "DATA_SIZE",
    "05" : "CRC_ERROR",
    "06" : "OPER_FAILED",
}

#------------------------------------------------------------------------------
# Convert a number into an array of 4 bytes (LSB).
# This has been modified to prepend 8 zero bytes per the new DFU spec.
#------------------------------------------------------------------------------
def convert_uint32_to_array(value):
    return [0,0,0,0,0,0,0,0,
           (value >> 0  & 0xFF),
           (value >> 8  & 0xFF),
           (value >> 16 & 0xFF),
           (value >> 24 & 0xFF)
    ]

#------------------------------------------------------------------------------
# Convert a number into an array of 2 bytes (LSB).
#------------------------------------------------------------------------------
def convert_uint16_to_array(value):
    return [
        (value >> 0 & 0xFF),
        (value >> 8 & 0xFF)
    ]

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
def convert_array_to_hex_string(arr):
    hex_str = ""
    for val in arr:
        if val > 255:
            raise Exception("Value is greater than it is possible to represent with one byte")
        hex_str += "%02x" % val

    return hex_str

#------------------------------------------------------------------------------
# Define the BleDfuServer class
#------------------------------------------------------------------------------
class BleDfuServer(object):

    #--------------------------------------------------------------------------
    # Adjust these handle values to your peripheral device requirements.
    #--------------------------------------------------------------------------
    ctrlpt_handle      = 0x19
    ctrlpt_cccd_handle = 0x1a
    data_handle        = 0x17

    pkt_receipt_interval = 10
    pkt_payload_size     = 20

    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    def __init__(self, target_mac, hexfile_path, datfile_path):

        self.hexfile_path = hexfile_path
        self.datfile_path = datfile_path

        self.ble_conn = pexpect.spawn("gatttool -b '%s' -t random --interactive" % target_mac)

        # remove next line comment for pexpect detail tracing.
        #self.ble_conn.logfile = sys.stdout

    #--------------------------------------------------------------------------
    # Connect to peripheral device.
    #--------------------------------------------------------------------------
    def scan_and_connect(self):

        print "scan_and_connect"

        try:
            self.ble_conn.expect('\[LE\]>', timeout=10)
        except pexpect.TIMEOUT, e:
            print "Connect timeout"

        self.ble_conn.sendline('connect')

        try:
            res = self.ble_conn.expect('\[CON\].*>', timeout=10)
        except pexpect.TIMEOUT, e:
            print "Connect timeout"

    #--------------------------------------------------------------------------
    # Wait for notification to arrive.
    # Example format: "Notification handle = 0x0019 value: 10 01 01"
    #--------------------------------------------------------------------------
    def _dfu_wait_for_notify(self):

        while True:
            #print "dfu_wait_for_notify"

            if not self.ble_conn.isalive():
                print "connection not alive"
                return None

            try:
                index = self.ble_conn.expect('Notification handle = .*? \r\n', timeout=30)

            except pexpect.TIMEOUT:
                #
                # The gatttool does not report link-lost directly.
                # The only way found to detect it is monitoring the prompt '[CON]'
                # and if it goes to '[   ]' this indicates the connection has
                # been broken.
                # In order to get a updated prompt string, issue an empty
                # sendline('').  If it contains the '[   ]' string, then
                # raise an exception. Otherwise, if not a link-lost condition,
                # continue to wait.
                #
                self.ble_conn.sendline('')
                string = self.ble_conn.before
                if '[   ]' in string:
                    print 'Connection lost! {0}.{1}'.format(name, os.getpid())
                    raise Exception('Connection Lost')
                return None

            if index == 0:
                after = self.ble_conn.after
                hxstr = after.split()[3:]
                handle = long(float.fromhex(hxstr[0]))
                return hxstr[2:]

            else:
                print "unexpeced index: {0}".format(index)
                return None

    #--------------------------------------------------------------------------
    # Parse notification status results
    #--------------------------------------------------------------------------
    def _dfu_parse_notify(self, notify):

        if len(notify) < 3:
            print "notify data length error"
            return None

        dfu_oper = notify[0]
        oper_str = DFU_oper_to_str[dfu_oper]

        if oper_str == "RESPONSE":

            dfu_process = notify[1]
            dfu_status  = notify[2]

            process_str = DFU_proc_to_str[dfu_process]
            status_str  = DFU_status_to_str[dfu_status]

            print "oper: {0}, proc: {1}, status: {2}".format(oper_str, process_str, status_str)

            if oper_str == "RESPONSE" and status_str == "SUCCESS":
                return "OK"
            else:
                return "FAIL"

        if oper_str == "PKT_RCPT_NOTIF":

            byte1 = int(notify[4], 16)
            byte2 = int(notify[3], 16)
            byte3 = int(notify[2], 16)
            byte4 = int(notify[1], 16)

            receipt = 0
            receipt = receipt + (byte1 << 24)
            receipt = receipt + (byte2 << 16)
            receipt = receipt + (byte3 << 8)
            receipt = receipt + (byte4 << 0)

            print "PKT_RCPT: {0:8}".format(receipt)

            return "OK"


    #--------------------------------------------------------------------------
    # Send two bytes: command + option
    #--------------------------------------------------------------------------
    def _dfu_state_set(self, opcode):
        self.ble_conn.sendline('char-write-req 0x%04x %04x' % (self.ctrlpt_handle, opcode))

        # Verify that command was successfully written
        try:
            res = self.ble_conn.expect('.* Characteristic value was written successfully', timeout=10)
        except pexpect.TIMEOUT, e:
            print "State timeout"

    #--------------------------------------------------------------------------
    # Send one byte: command
    #--------------------------------------------------------------------------
    def _dfu_state_set_byte(self, opcode):
        self.ble_conn.sendline('char-write-req 0x%04x %02x' % (self.ctrlpt_handle, opcode))

        # Verify that command was successfully written
        try:
            res = self.ble_conn.expect('.* Characteristic value was written successfully', timeout=10)
        except pexpect.TIMEOUT, e:
            print "State timeout"

    #--------------------------------------------------------------------------
    # Send 3 bytes: PKT_RCPT_NOTIF_REQ with interval of 10 (0x0a)
    #--------------------------------------------------------------------------
    def _dfu_pkt_rcpt_notif_req(self):

        opcode = 0x080000
        opcode = opcode + (self.pkt_receipt_interval << 8)

        self.ble_conn.sendline('char-write-req 0x%04x %06x' % (self.ctrlpt_handle, opcode))

        # Verify that command was successfully written
        try:
            res = self.ble_conn.expect('.* Characteristic value was written successfully', timeout=10)
        except pexpect.TIMEOUT, e:
            print "Send PKT_RCPT_NOTIF_REQ timeout"

    #--------------------------------------------------------------------------
    # Send an array of bytes: request mode
    #--------------------------------------------------------------------------
    def _dfu_data_send_req(self, data_arr):
        hex_str = convert_array_to_hex_string(data_arr)
        #print hex_str
        self.ble_conn.sendline('char-write-req 0x%04x %s' % (self.data_handle, hex_str))

        # Verify that data was successfully written
        try:
            res = self.ble_conn.expect('.* Characteristic value was written successfully', timeout=10)
        except pexpect.TIMEOUT, e:
            print "Data timeout"

    #--------------------------------------------------------------------------
    # Send an array of bytes: command mode
    #--------------------------------------------------------------------------
    def _dfu_data_send_cmd(self, data_arr):
        hex_str = convert_array_to_hex_string(data_arr)
        #print hex_str
        self.ble_conn.sendline('char-write-cmd 0x%04x %s' % (self.data_handle, hex_str))

    #--------------------------------------------------------------------------
    # Enable DFU Control Point CCCD (Notifications)
    #--------------------------------------------------------------------------
    def _dfu_enable_cccd(self):
        cccd_enable_value_array_lsb = convert_uint16_to_array(0x0001)
        cccd_enable_value_hex_string = convert_array_to_hex_string(cccd_enable_value_array_lsb)
        self.ble_conn.sendline('char-write-req 0x%04x %s' % (self.ctrlpt_cccd_handle, cccd_enable_value_hex_string))

        # Verify that CCCD was successfully written
        try:
            res = self.ble_conn.expect('.* Characteristic value was written successfully', timeout=10)
        except pexpect.TIMEOUT, e:
            print "CCCD timeout"

    #--------------------------------------------------------------------------
    # Send the Init info (*.dat file contents) to peripheral device.
    #--------------------------------------------------------------------------
    def _dfu_send_init(self):

        print "dfu_send_info"

        # Open the DAT file and create array of its contents
        bin_array = array('B', open(self.datfile_path, 'rb').read())

        # Transmit Init info
        self._dfu_data_send_req(bin_array)

    #--------------------------------------------------------------------------
    # Initialize: 
    #    Hex: read and convert hexfile into bin_array 
    #    Bin: read binfile into bin_array
    #--------------------------------------------------------------------------
    def input_setup(self):

        print "input_setup"

        if self.hexfile_path == None:
            raise Exception("input invalid")

        name, extent = os.path.splitext(self.hexfile_path)

        if extent == ".bin":
            self.bin_array = array('B', open(self.hexfile_path, 'rb').read())
            self.hex_size = len(self.bin_array)
            print "bin array size: ", self.hex_size
            return

        if extent == ".hex":
            intelhex = IntelHex(self.hexfile_path)
            self.bin_array = intelhex.tobinarray()
            self.hex_size = len(self.bin_array)
            print "bin array size: ", self.hex_size
            return

        raise Exception("input invalid")

    #--------------------------------------------------------------------------
    # Send the binary firmware image to peripheral device.
    #--------------------------------------------------------------------------
    def dfu_send_image(self):

        print "dfu_send_image"

        # Enable Notifications
        self._dfu_enable_cccd()

        # Send 'START DFU' + Application Command
        self._dfu_state_set(0x0104)

        # Transmit binary image size
        hex_size_array_lsb = convert_uint32_to_array(len(self.bin_array))

        print hex_size_array_lsb
        self._dfu_data_send_req(hex_size_array_lsb)
        print "Sending hex file size"

        # Send 'INIT DFU' Command
        self._dfu_state_set(0x0200)

        # Wait for INIT DFU notification (indicates flash erase completed)
        notify = self._dfu_wait_for_notify()

        # Check the notify status.
        dfu_status = self._dfu_parse_notify(notify)
        if dfu_status != "OK":
            raise Exception("bad notification status")

        # Transmit the Init image (DAT).
        self._dfu_send_init()

        # Send 'INIT DFU' + Complete Command
        self._dfu_state_set(0x0201)

        # Send packet receipt notification interval (currently 10)
        self._dfu_pkt_rcpt_notif_req()

        # Send 'RECEIVE FIRMWARE IMAGE' command to set DFU in firmware receive state. 
        self._dfu_state_set_byte(Commands.RECEIVE_FIRMWARE_IMAGE)

        '''
        Send bin_array contents as as series of packets (burst mode).
        Each segment is pkt_payload_size bytes long.
        For every pkt_receipt_interval sends, wait for notification.
        '''
        segment_count = 1
        for i in range(0, self.hex_size, self.pkt_payload_size):

            segment = self.bin_array[i:i + self.pkt_payload_size]
            self._dfu_data_send_cmd(segment)

            #print "segment #", segment_count

            if (segment_count % self.pkt_receipt_interval) == 0:
                notify = self._dfu_wait_for_notify()

                if notify == None:
                    raise Exception("no notification received")

                dfu_status = self._dfu_parse_notify(notify)

                if dfu_status == None or dfu_status != "OK":
                    raise Exception("bad notification status")

            segment_count += 1

        # Send Validate Command
        self._dfu_state_set_byte(Commands.VALIDATE_FIRMWARE_IMAGE)

        # Wait a bit for copy on the peer to be finished
        time.sleep(1)

        # Send Activate and Reset Command
        self._dfu_state_set_byte(Commands.ACTIVATE_FIRMWARE_AND_RESET)


    #--------------------------------------------------------------------------
    # Disconnect from peer device if not done already and clean up. 
    #--------------------------------------------------------------------------
    def disconnect(self):
        self.ble_conn.sendline('exit')
        self.ble_conn.close()

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
def main():

    print "DFU Server start"

    try:
        parser = optparse.OptionParser(usage='%prog -f <hex_file> -a <dfu_target_address>\n\nExample:\n\tdfu.py -f application.hex -f application.dat -a cd:e3:4a:47:1c:e4',
                                       version='0.5')

        parser.add_option('-a', '--address',
                  action='store',
                  dest="address",
                  type="string",
                  default=None,
                  help='DFU target address.'
                  )

        parser.add_option('-f', '--file',
                  action='store',
                  dest="hexfile",
                  type="string",
                  default=None,
                  help='hex file to be uploaded.'
                  )

        parser.add_option('-d', '--dat',
                  action='store',
                  dest="datfile",
                  type="string",
                  default=None,
                  help='dat file to be uploaded.'
                  )

        parser.add_option('-z', '--zip',
                  action='store',
                  dest="zipfile",
                  type="string",
                  default=None,
                  help='zip file to be used.'
                  )

        options, args = parser.parse_args()

    except Exception, e:
        print e
        print "For help use --help"
        sys.exit(2)

    try:

        ''' Validate input parameters '''

        if not options.address:
            parser.print_help()
            exit(2)

        unpacker = None
        hexfile  = None
        datfile  = None

        if options.zipfile != None:

            if (options.hexfile != None) or (options.datfile != None):
                print "Conflicting input directives"
                exit(2)

            unpacker = Unpacker()

            hexfile, datfile = unpacker.unpack_zipfile(options.zipfile)

        else:
            if (not options.hexfile) or (not options.datfile):
                parser.print_help()
                exit(2)

            if not os.path.isfile(options.hexfile):
                print "Error: Hex file doesn't exist"
                exit(2)

            if not os.path.isfile(options.datfile):
                print "Error: DAT file doesn't exist"
                exit(2)

            hexfile = options.hexfile
            datfile = options.datfile


        ''' Start of Device Firmware Update processing '''

        ble_dfu = BleDfuServer(options.address.upper(), hexfile, datfile)

        # Initialize inputs
        ble_dfu.input_setup()

        # Connect to peer device.
        ble_dfu.scan_and_connect()

        # Transmit the hex image to peer device.
        ble_dfu.dfu_send_image()

        # Wait to receive the disconnect event from peripheral device.
        time.sleep(1)

        # Disconnect from peer device if not done already and clean up. 
        ble_dfu.disconnect()

    except Exception, e:
        print e
        pass

    except:
        pass

    # If Unpacker for zipfile used then delete Unpacker
    if unpacker != None:
        unpacker.delete()

    print "DFU Server done"

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
if __name__ == '__main__':

    # Do not litter the world with broken .pyc files.
    sys.dont_write_bytecode = True

    main()

