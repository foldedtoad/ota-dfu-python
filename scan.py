#!/usr/bin/env python

#------------------------------------------------------------------------------
# Device scan
#------------------------------------------------------------------------------

from subprocess import call

import pexpect
import signal

#------------------------------------------------------------------------------
# Bluetooth LE scan for advertising peripheral devices
#------------------------------------------------------------------------------
class HciTool:

    def __init__( self, advert_name ):
        self.advert_name = advert_name
        return

    def scan( self ):

        try:
            self.hcitool = pexpect.spawn('hcitool lescan')
            #self.hcitool.logfile = sys.stdout
            index = self.hcitool.expect(['LE Scan ...'], 1)
        except pexpect.EOF:
            self.hcitool.terminate(force=True)
            return []
        except Exception as err:
            print "scan: exception: {0}".format(sys.exc_info()[0])
            self.hcitool.terminate(force=True)
            return []

        if index != 0:
            print "scan: failed"
            self.hcitool.terminate(force=True)
            return []

        list = []
        for dummy in range(0, 2):
            try:
                list.append(self.hcitool.readline())
            except pexpect.TIMEOUT:
                break

        if list == []:
            return []

        # Eliminate duplicate items in list
        list = set(list)

        # Remove non self.advert_name units
        if self.advert_name != None:
            list = [item for item in list if self.advert_name in item]

        # remove empty items from list
        while '\r\n' in list:
            list.remove('\r\n')

        # Strip newline from items in list
        list = [item.strip() for item in list]
        list = list[0:2]

        # Close pexpect (release device for subsequent use)
        self.hcitool.terminate(force=True)

        return list

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
class Scan:

    def __init__( self, advert_name ):
        self.advert_name = advert_name
        return    

    def scan(self):

        scan_list = []

        try:
            hcitool = HciTool(self.advert_name)
            scan_list = hcitool.scan()

        except KeyboardInterrupt:
            # On Cntl-C
            pass;
        except pexpect.TIMEOUT:
            print "scan: pexpect.TIMEOUT"
            pass
        except Exception as e:
            print "scan: exception: {0} ".format(sys.exc_info()[0])
            pass


        return scan_list

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
if __name__ == '__main__':

    # Do not litter the world with broken .pyc files.
    sys.dont_write_bytecode = True

    #scanner = Scan("DfuTarg")  # specific advertisement name
    scanner = Scan(None)      # any advertising name
    
    scanner.scan()

    print "scan complete"
