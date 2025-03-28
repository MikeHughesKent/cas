# -*- coding: utf-8 -*-
"""
CAS GUI Multicore Example

This example shows how to use a separate core for the processing which 
should lead to an increase in the maximum achievable frame rate before 
frames are dropped.
"""

import sys 
import os
from pathlib import Path

from PyQt5 import QtGui, QtCore, QtWidgets  
from PyQt5.QtWidgets import *

from scipy.ndimage import gaussian_filter

import context    # Adds paths

from cas_gui.base import CAS_GUI
from cas_gui.threads.image_processor_class import ImageProcessorClass

class GaussianFilter(ImageProcessorClass):
    
    applyFilter = False
    filterSize = None   
    
    def __init__(self, applyFilter = False, filterSize = None):
        """ If any additional initialisation is needed, it goes here.
        """
        self.applyFilter = applyFilter
        self.filterSize = filterSize
        
                
    def process(self, inputFrame):
        """ This is where we do the processing. This function takes a raw
        image and returns the processed image, both as numpy arrays.
        """
        if self.applyFilter and self.filterSize > 0:
            outputFrame = gaussian_filter(inputFrame, self.filterSize)
        else:
            outputFrame = inputFrame
        return outputFrame
    

class example_GUI(CAS_GUI):

    # If the class name is changed, must also change the window = example_GUI()
    # line at the bottom of the file.
    
    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "Example GUI"
    
    # Path to where CAS icons etc are stored
    resPath = "..//res"
    
    # We are going to make use of multiple cores by running the processing
    # on a different core to the GUI and image acquirer. We will not use shared
    # memory as we do not have large images so can work with queues and avoid
    # dropped frames
    multiCore = True
    sharedMemory = False
    
    # Define the processor class which will be used by the ImageProcessor thread
    # to process the images    
    processor = GaussianFilter
    
    # GUI window title
    windowTitle = "Camera Acquisition System: Example with multi cores"
        
 
    # Default source for simulated camera
    sourceFilename = Path('data/vid_example.tif')           
        
            
    def add_settings(self, settingsLayout):
        """ We override this function to add custom options to the setings menu
        panel.
        """
        
        # Filter Checkbox
        self.filterCheckBox = QCheckBox("Apply Filter", objectName = 'FilterCheck')
        settingsLayout.addWidget(self.filterCheckBox)  
        self.filterCheckBox.stateChanged.connect(self.processing_options_changed)
            
        # Filter Size
        settingsLayout.addWidget(QLabel("Filter Size (px):"))
        self.filterSizeInput = QSpinBox(objectName = 'FilterSizeInput')
        settingsLayout.addWidget(self.filterSizeInput)  
        self.filterSizeInput.valueChanged[int].connect(self.processing_options_changed)       
  


    def processing_options_changed(self):
        """
        This function is called when the processing options are changed so
        that we can update the processor. Here we are just changing attributes
        of the processor class directly. For more complex processing,
        where some checking of the values or more complicated changes are needed,
        it is better to define functions such as set_filter_size to handle
        this in the image processor and call these functions instead.
       
        """
        if self.imageProcessor is not None:
            self.imageProcessor.get_processor().filterSize = self.filterSizeInput.value()
            self.imageProcessor.get_processor().applyFilter = self.filterCheckBox.isChecked()
            
            # If using multicore, it's essential to call update_settings once 
            # we are done so that the settigns are sent across to the core
            # where the processor is running. Otherwise there will be no
            # changes implemented.
            self.imageProcessor.update_settings()
            
        # The new processing will be applied to the next image grabbed from a 
        # camera. However, if we are processing an image from a file, we normally
        # want to apply the new processing immediately, so we need to call
        # update_file_processing.
        self.update_file_processing()
        
        
# Launch the GUI
if __name__ == '__main__':    
           
    # Create and display GUI
    app = QApplication(sys.argv)     
    window = example_GUI()
    window.show()
     
    # When the window is closed, close everything
    sys.exit(app.exec_())
     

