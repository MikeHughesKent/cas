# -*- coding: utf-8 -*-
"""
CAS GUI: Minimal Example

A bare minumum example to create a GUI using CAS.

"""
import sys

from PyQt5.QtWidgets import QApplication

import context    # Adds paths

from cas_gui.base import CAS_GUI


class example_GUI(CAS_GUI):
    resPath = "..\\res"     
    sourceFilename = r"data/vid_example.tif"  
    
    
if __name__ == '__main__':    
           
    # Create and display GUI
    app = QApplication(sys.argv)     
    window = example_GUI()
    window.show()
     
    # When the window is closed, close everything
    sys.exit(app.exec_())