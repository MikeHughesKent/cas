# -*- coding: utf-8 -*-
"""
Kent-CAS-GUI Example

This examples shows how to extend CAS GUI to create a simple application
to process and display images from a camera.

@author: Mike Hughes, Applied Optics Group, University of Kent

"""

import sys 
import os
from pathlib import Path
from PyQt5 import QtGui, QtCore, QtWidgets  
from PyQt5.QtWidgets import *

import context    # Adds paths

from CAS_GUI_Base import *
from gui_example_processor import FilterProcessor
from ImageAcquisitionThread import ImageAcquisitionThread
from ImageProcessorThread import ImageProcessorThread

from image_display import ImageDisplay
from gui_example_filter_class import FilterClass




class example_GUI(CAS_GUI):

    # If the class name is changed, must also change the window = example_GUI()
    # line at the bottom of the file.
    
    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "Example GUI"
    
    # We are going to make use of multiple cores by running the processing
    # on a different core to the GUI and image acquirer
    multicore = True
    
    # Define the processor class which will be used by the ImageProcessor thread
    # to process the images    
    processor = FilterClass
    
    # GUI window title
    windowTitle = "Kent Camera Acquisition System: Example with multi cores"
        
    # Define available cameras interface and their display names in the drop-down menu
    camNames = ['File', 'Simulated Camera', 'Flea Camera', 'Kiralux', 'Thorlabs DCX', 'Webcam', 'Colour Webcam']
    camSources = ['ProcessorInterface', 'SimulatedCamera', 'FleaCameraInterface', 'KiraluxCamera', 'DCXCameraInterface', 'WebCamera', 'WebCameraColour']
          
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
        
  


    def processing_options_changed(self,event):
        """
        This function is called when the processing options are changed so
        that we can update the processor. Here we are just changing attributes
        of the imageProcessor class directly. For more complex processing,
        where some checking of the values or more complicated changes are needed,
        it is better to define functions such as set_filter_size to handle
        this in the image processor and call these functions instead.
       
        """
        if self.imageProcessor is not None:
            self.imageProcessor.get_processor().filterSize = self.filterSizeInput.value()
            self.imageProcessor.get_processor().applyFilter = self.filterCheckBox.isChecked()

            
            # If using multicore, it's essential to call update_settings once 
            # we are done so that the settigns are sent across to the core
            # where the processor is running
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
     

