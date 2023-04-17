#! /usr/bin/env python3
#  -*- coding: utf-8 -*-
#
# Support module generated by PAGE version 7.6
#  in conjunction with Tcl version 8.6
#    Apr 16, 2023 08:34:08 PM CEST  platform: Windows NT

import tkinter as tk

import pyproj
from src.graphical_interface.work_breakdown_structure.graph import WBSFrame

_debug = True  # False to eliminate debug printing from callback functions.


def main(*args):
    """Main entry point for the application."""
    global root
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    # Creates a toplevel widget.
    global _top1, _w1
    _top1 = root
    _w1 = pyproj.Toplevel1(_top1)
    root.mainloop()


Custom = WBSFrame  # To be updated by user with name of custom widget.

if __name__ == "__main__":
    pyproj.start_up()
