# -*- coding: utf-8 -*-
"""
CAS GUI: Example of creating menus

This example shows how to extend CAS GUI with an additional menu and a button.
The button will take a copy of the current image, which can then be
subtracted from all subsequent images by toggling the swtich in the
'Background Settings' menu.

To achieve this we:
    
    Override the create_layout function to create two menu buttons and the menu.
    Link a menu button to the menu
    Link the other menu button to a function which will copy the current image
      to a background image
    Implement a processor which handles the background subtraction  

"""

import sys 
import os
from pathlib import Path

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon


import numpy as np

import context    # Adds paths

from cas_gui.base import CAS_GUI
from cas_gui.threads.image_processor_class import ImageProcessorClass


class ExampleProcessor(ImageProcessorClass):
    """ This is where we define the processing that happens to the image. We
    sub-class ImageProcessorClass and, at a minimum, implement '__init__' to
    receive settings and 'process' to process each frame.
    """    
    
    backgroundSubtraction = False
    backgroundImage = None
    
    def __init__(self, backgroundSubtraction = True, backgroundIimage = None):
        """ Technically not needed since we are not adding anything, but
        if any additional initialisation is needed, it goes here.
        """
        self.backgroundSubtraction = backgroundSubtraction
        self.backgroundImage = None
        
                
    def process(self, inputFrame):
        """ This is where we do the processing.
        """
        outputFrame = inputFrame
        if self.backgroundSubtraction and self.backgroundImage is not None:
            if np.shape(inputFrame) == np.shape(self.backgroundImage):
                outputFrame = inputFrame.astype(float) - self.backgroundImage.astype(float)
        else:
            outputFrame = inputFrame
        
        return outputFrame
    


class example_GUI(CAS_GUI):
    """ This is the main class, this is a sub-class of CAS_GUI. In this example
    we use the add_settings() method to add some settings to the settings menu and
    processing_options_changed() to handle changes to these settings.
    """

    # If the class name is changed, must also change the window = example_GUI()
    # line at the bottom of the file.
    
    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "Example GUI"
    
    # GUI window title
    windowTitle = "Camera Acquisition System: Example"
    
    # Define the image processor
    processor = ExampleProcessor
        
    # Default source for simulated camera
    sourceFilename = Path('data/vid_example.tif')  

    # Default location for resources
    resPath = "..\\res"         
        
            
    def add_settings(self, settingsLayout):
        """ If we wanted to add settings to the Settings Panel we could add them
        here, but we are going to make a custom menu instead.
        """
        pass        
    
    
    def create_layout(self):
        """ We override this function to add in the custom menu panel and buttons
        """
        
        # Create default layout first
        super().create_layout()
        
        # Create a button to acquire a background image
        self.acquireBackgroundButton = self.create_menu_button(text = "Acquire Background",
                                                       icon = QIcon('../res/icons/chevron_white.svg'),
                                                       handler = self.acquire_background_clicked,
                                                       hold = True,         # Flag that this is a switch
                                                       menuButton = False,  # Flag that this does not open a menu
                                                       position = 3)        # Position in menu bar  

        # Create a button to open the custom menu
        self.backgroundMenuButton = self.create_menu_button(text = "Backgound Settings", 
                                                       icon = QIcon('../res/icons/settings_white.svg'), 
                                                       handler = self.background_menu_button_clicked, 
                                                       hold = False,        # Flag that this is not a switch
                                                       menuButton = True,   # Flag that we used this to open a menu
                                                       position = 4)        # Position in menu bar       
       
        # Create the menu panel by calling our custom function which we define below
        self.backgroundPanel = self.create_background_panel()
        

    def acquire_background_clicked(self):
        """ Called when the acquire background button is pressed. If we 
        have a raw image, we copy it and then call processing_options_changed
        where we updated the processor.
        """
        
        if self.currentImage is not None:
            self.backgroundImage = self.currentImage.copy()
            self.processing_options_changed()
          
        
    def background_menu_button_clicked(self):
        """ This is called when the custom menu button is clicked. We call
        a standard helper function to operate the menu."""
        self.expanding_menu_clicked(self.backgroundMenuButton, self.backgroundPanel)    

   
    def create_background_panel(self):
        """ Create the custom menu panel to control background subtraction """
        
        # We use a helper function to create the panel with the required title
        widget, layout = self.panel_helper(title = "Background Options")
        
        # Create a checkbox. Giving it an objectName will mean that its value
        # is saved in the registry and loaded at startup.
        self.backgroundCheck = QCheckBox("Apply Background", objectName = "applyBackgroundCeck")
        
        # Link this to processing_options_changed so that the processor will be
        # updated when we toggle the checkbox
        self.backgroundCheck.stateChanged.connect(self.processing_options_changed)
        
        # Add to the menu
        layout.addWidget(self.backgroundCheck)
    
        # Add spacer at the bottom to keep control at the top rather than spread out.
        layout.addStretch()
    
        # We must return the widget
        return widget
    
           

    def processing_options_changed(self):
        """ This function is called when the processing options are changed so
        that we can update the processor. Here we are just changing attributes
        of the imageProcessor class directly. For more complex processing,
        where some checking of the values or more complicated changes are needed,
        it is better to define functions such as set_background_image to handle
        this in the image processor and call these functions instead.
       
        """
        if self.imageProcessor is not None:
            self.imageProcessor.get_processor().backgroundSubtraction = self.backgroundCheck.isChecked()
            self.imageProcessor.get_processor().backgroundImage = self.backgroundImage
        
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
     

