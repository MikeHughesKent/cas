# -*- coding: utf-8 -*-
"""
CAS GUI: Minimal Example

A bare minumum example to create a GUI using CAS.

"""
import sys

from PyQt5.QtWidgets import QApplication

# Check for a context.py file in folder which adds paths. This is needed
# if cas_gui wasn't pip installed to tell Python where the install is, in which case
# edit (or create) context.py with the path to the src folder of your copy of cas_gui.
try: 
    import context
except: 
    pass  

from cas_gui.base import CAS_GUI


class example_GUI(CAS_GUI):
    pass
    
if __name__ == '__main__':    
           
    # Create and display GUI
    app = QApplication(sys.argv)     
    window = example_GUI()
    window.show()
     
    # When the window is closed, close everything
    sys.exit(app.exec_())