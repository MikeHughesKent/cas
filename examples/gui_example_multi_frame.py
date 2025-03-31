# -*- coding: utf-8 -*-
"""
CAS GUI: Example of Multiple Image Processing

This example shows how to extend CAS GUI to create a simple application
to process and display a stack of images from a camera by averging them.

For this to work we have to: 
    
1. Sub-class imageProcessor to create a custom processing algorithm by implementing 'process()'
2. Use set_batch_process_num() to tell the processor how many image to collect
   before running  'process()''
3. Create an options on the settings menu panel to allow the user to choose how many images
   to average.

Processing and the GUI both run on the same processor core.

"""

import sys, os
from pathlib import Path

import numpy as np

from PyQt5.QtWidgets import QApplication, QLabel, QSpinBox

# Check for a context.py file in folder which adds paths. This is needed
# if cas_gui wasn't pip installed to tell Python where the install is, in which case
# edit (or create) context.py with the path to the src folder of your copy of cas_gui.
try: 
    import context
except: 
    pass  

from cas_gui.base import CAS_GUI
from cas_gui.threads.image_processor_class import ImageProcessorClass


class AverageProcessor(ImageProcessorClass):  
    """ We subclass ImageProcessorClass to create a custom image processor.
    """
       
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
            outputFrame = np.mean(inputFrame, 2)
        else:
            outputFrame = inputFrame
        
        return outputFrame


class example_multi_GUI(CAS_GUI):
    
    # If the class name is changed, must also change the window = example_GUI()
    # line at the bottom of the file.
    
    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "Example Multi Frame GUI"
    
    # Path to resources
    resPath = "..//res"
    
    # Use only a single core
    multiCore = False

    # GUI window title
    windowTitle = "Camera Acquisition System: Multi Frame Example"
        
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
        # that we don't remove part of some sequence of frames. This is important
        # if we always want to have a sequentual run of images, with no dropped
        # frames in the sequence.
        
        if self.imageThread is not None:
            self.imageThread.set_num_removal_when_full(self.numAverageInput.value())            

                
        
# Launch the GUI
if __name__ == '__main__':    
    
   # Create and display GUI   
   app = QApplication(sys.argv)     
   window = example_multi_GUI()
   window.show()
   
   # When the window is closed, close everything
   sys.exit(app.exec_())
   
