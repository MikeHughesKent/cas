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
from image_display import ImageDisplay


class example_GUI(CAS_GUI):

    # If the class name is changed, must also change the window = example_GUI()
    # line at the bottom of the file.
    
    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "Example GUI"
    
    # GUI window title
    windowTitle = "Kent Camera Acquisition System: Example"
        
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
        
        
    def create_processors(self):
          """ 
          We have overrided this function to create the thread for processing the images.
          """
          # We will use the queue that the image acquisition thread has created
          # to act as the input queue, this avoids the need for any copying of images
          if self.imageThread is not None:
              inputQueue = self.imageThread.get_image_queue()
          else:
              inputQueue = None
         
          # Create the processor. This is imported from the gui_example_processor file  
          # The first two arguments are the sizes of the input and output queue, although
          # as we have chosen to pass the inputQueue directly, the first number is ignored.
          self.imageProcessor = FilterProcessor(10,10, inputQueue = inputQueue)
          
          # Update the processor based on initial values of widgets
          self.processing_options_changed(0)
      
          # Start the thread
          if self.imageProcessor is not None:
              self.imageProcessor.start()


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
            self.imageProcessor.filterSize = self.filterSizeInput.value()
            self.imageProcessor.applyFilter = self.filterCheckBox.isChecked()

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
     

