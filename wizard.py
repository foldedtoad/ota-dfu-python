#!/usr/bin/env python

#------------------------------------------------------------------------------
# Graphical User Interface for DFU Server
#------------------------------------------------------------------------------

import os

from Tkinter import *

import ttk
import tkMessageBox

import tkFileDialog
from tkFileDialog import askopenfilename

from scan import Scan
from dfu2 import *

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
class Application(Frame):

    def __init__(self, master):
        Frame.__init__(self, master)
        self.file = None
        self.addr = None
        self.device = None
        self.grid()
        self.create_widgets()

    def create_widgets(self):

        self.frame1 = Frame(self)
        self.frame1['relief'] = RIDGE
        self.frame1.grid(row=0, column=0, pady=3, sticky=N)

        self.button1 = Button(self.frame1)
        self.button1["width"] = 20
        self.button1["text"] = "Select application.zip file"
        self.button1["command"] = self.selectFile
        self.button1.grid(row=0, column=0, sticky=N)

        self.text1 = Label(self.frame1)
        self.text1["background"] = "white"
        self.text1["width"] = 30
        self.text1["text"] = "none"
        self.text1.grid(row=1, column=0, pady=5, sticky=N)  

        self.frame2 = Frame(self)
        self.frame2.grid(row=1, rowspan=2, sticky=N)

        self.button2 = Button(self.frame2)
        self.button2["width"] = 20
        self.button2["text"] = "Scan for target devices"
        self.button2["command"] = self.get_device_name
        self.button2.grid(row=0, column=0, sticky=N)

        self.scrollbar2 = Scrollbar(self.frame2)
        self.scrollbar2.grid(row=2, column=0, sticky=N)

        self.listbox2 = Listbox(self.frame2)
        self.listbox2['height'] = 5
        self.listbox2.bind("<Double-Button-1>", self.device_selected)
        self.listbox2.grid(row=2, column=0, sticky=N)

        self.scrollbar2.config(command=self.listbox2.yview)
        self.listbox2.config(yscrollcommand=self.scrollbar2.set)

        self.text2 = Label(self.frame2)
        self.text2["text"] = "Double-click to select"
        self.text2.grid(row=3, column=0, sticky=N)

        self.frame3 = Frame(self)
        self.frame3.grid(row=7, column=0, rowspan=2, pady=5, sticky=N)

        self.progress3 = ttk.Progressbar(self.frame3)
        self.progress3['orient'] = 'horizontal'
        self.progress3['length'] = 250
        self.progress3['mode'] = 'determinate'
        self.progress3.grid(row=0, column=0, sticky=N)

        self.text3 = Label(self.frame3)
        self.text3["text"] = "Download progress"
        self.text3.grid(row=3, column=0, sticky=N+W+E)
        #self.text3.pack(side=BOTTOM, fill="x")

    def selectFile(self):
        self.file = askopenfilename(filetypes=[('Zip files', '*.zip')])
        filename = os.path.basename(self.file)
        self.text1["text"] = filename

    def get_device_name(self):
        scanner = Scan(None)
        targets = scanner.scan()
        self.listbox2.delete(0, END)

        if targets:
            for target in targets:
                index = targets.index(target)
                addr  = targets[index][:17]
                self.listbox2.insert("end", addr)

    def device_selected(self, event):
        widget = event.widget
        selected = widget.curselection()
        self.addr = widget.get(selected[0])

        if self.addr and self.file:
            print "addr: {0}".format(self.addr)
            print "file: {0}".format(self.file)

            # dfu_server("-z {0} -a {1}".format(self.file, self.addr))

        else:
            tkMessageBox.showwarning("Error", "Missing application file")

        return


#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
def main():

    root = Tk()
    root.title("DFU Server")
    root.configure(bg='lightgrey')
    root.geometry("250x235")

    app = Application(root)

    root.mainloop()

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
if __name__ == '__main__':

    # Do not litter the world with broken .pyc files.
    sys.dont_write_bytecode = True

    main()
