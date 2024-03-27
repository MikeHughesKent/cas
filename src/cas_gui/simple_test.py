# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 13:52:28 2024

@author: mrh40
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication

from cas_gui.base import CAS_GUI
from cas_gui.threads.image_processor_class import ImageProcessorClass

class MyProcessorClass(ImageProcessorClass):
    
    def process(self, inputImage):
        return np.fliplr(inputImage)
    
class example_GUI(CAS_GUI):
    windowTitle = "My example GUI"
    processor = MyProcessorClass
     
if __name__ == '__main__':    
            
     # Create and display GUI
     app = QApplication(sys.argv)     
     window = example_GUI()
     window.show()
      
     # When the window is closed, close everything
     sys.exit(app.exec_())