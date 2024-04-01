# -*- coding: utf-8 -*-
"""
Kent-CAS-GUI Example of Multiple Image Processing

This example shows how to extend CAS GUI to create a simple application
to process and display a stack of images from a camera.

@author: Mike Hughes, Applied Optics Group, University of Kent

"""

import sys 
import os
from pathlib import Path
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets  
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import context    # Adds paths

from cas_gui.base import CAS_GUI
from cas_gui.threads.image_processor_class import ImageProcessorClass


class AverageProcessor(ImageProcessorClass):
    
       
    def __init__(self):
        """ Technically not needed since we are not adding anything, but
        if any additional initialisation is needed, it goes here.
        """
        
        super().__init__()        
       
                
    def process(self, inputFrame):
        """ This is where we do the processing.
        """
        
        # If we have a stack of frames, take the average
        if inputFrame.ndim == 3:
            outputFrame = np.mean(inputFrame,2)
        else:
            outputFrame = inputFrame
        
        return outputFrame


class example_multi_GUI(CAS_GUI):
    

    # If the class name is changed, must also change the window = example_GUI()
    # line at the bottom of the file.
    
    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "Example Multi GUI"
    
    # Path to resources
    resPath = "..//res"
    
    multiCore = True

    # GUI window title
    windowTitle = "Kent Camera Acquisition System: Multi Frame Example"
        
    # Define available cameras interface and their display names in the drop-down menu
    camNames = ['File', 'Simulated Camera', 'Flea Camera', 'Kiralux', 'Thorlabs DCX', 'Webcam', 'Colour Webcam']
    camSources = ['ProcessorInterface', 'SimulatedCamera', 'FleaCameraInterface', 'KiraluxCamera', 'DCXCameraInterface', 'WebCamera', 'WebCameraColour']
          
    # Default source for simulated camera
    sourceFilename = Path('data/vid_example.tif')
    
    # Define the processor class which will be used by the ImageProcessor thread
    # to process the images 
    processor = AverageProcessor
    
   
    
    def add_settings(self, settingsLayout):
        """ We override this function to add custom options to the setings menu
        panel.
        """
        
        # Number to Average 
        self.settingsLayout.addWidget(QLabel("Number to Average"))
        self.numAverageInput = QSpinBox(objectName = 'NumAverageInput')
        self.settingsLayout.addWidget(self.numAverageInput)  
        self.numAverageInput.setMinimum(1)
        self.numAverageInput.setMaximum(5)
        self.numAverageInput.valueChanged[int].connect(self.processing_options_changed)
        
    
   

    def processing_options_changed(self):
        """
        This function is called when the processing options are changed so
        that we can update the processor. Here we are just changing attributes
        of the imageProcessor class directly. For more complex processing,
        where some checking of the values or more complicated changes are needed,
        it is better to define functions such as set_filter_size to handle
        this in the image processor and call these functions instead.
       
        """
        if self.imageProcessor is not None:
            
            # Tell the processor how many images to process as a batch
            self.imageProcessor.set_batch_process_num(self.numAverageInput.value())
            
            # The image acquisition thread removes frames from the queue when it is
            # full. We can set the option here of how many to remove so
            # that we don't remove part of some sequence of frames
        
        if self.imageThread is not None:
            self.imageThread.set_num_removal_when_full(self.numAverageInput.value())
            

        # The new processing will be applied to the next image grabbed from a 
        # camera. However, if we are processing an image from a file, we normally
        # want to apply the new processing immediately, so we need to call
        # update_file_processing.
        self.update_file_processing()
        
        
# Launch the GUI
if __name__ == '__main__':    
    
   # Create and display GUI   
   app = QApplication(sys.argv)     
   window = example_multi_GUI()
   window.show()
   
   # When the window is closed, close everything
   sys.exit(app.exec_())
   
