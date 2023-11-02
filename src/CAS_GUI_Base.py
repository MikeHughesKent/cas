# -*- coding: utf-8 -*-
"""
Kent-CAS-GUI-Base

Kent CAS GUI is a graphical user interface built around the 
Kent Camera Acquisition System (Kent-CAS).

By itself, this class allows camera images or files to be viewed in real time. 

It is intended as a base class to be extended by more complete programs that
provide further functionality.

@author: Mike Hughes, Applied Optics Group, University of Kent

"""

import sys 
import os
import inspect

sys.path.append(os.path.abspath("widgets"))
sys.path.append(os.path.abspath("cameras"))
sys.path.append(os.path.abspath("threads"))

import time
import numpy as np
import math
import matplotlib.pyplot as plt
import multiprocessing as mp

from PyQt5 import QtGui, QtCore, QtWidgets  
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtXml import QDomDocument, QDomElement
from DoubleSlider import *

from PIL import Image

import cv2 as cv

from ImageAcquisitionThread import ImageAcquisitionThread
from image_display import ImageDisplay

from cam_control_panel import *

from ImageAcquisitionHandler import ImageAcquisitionHandler
from FileInterface import FileInterface

from datetime import datetime

from threading import Lock

from pathlib import Path

cuda = True                 # Set to False to disable use of GPU


class CAS_GUI(QMainWindow):
    
    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "CAS"
    windowTitle = "Kent Camera Acquisition System"
    logoFilename = None
    iconFilename = None
        
    # Define available cameras interface and their display names in the drop-down menu
    camNames = ['File', 'Simulated Camera', 'Flea Camera', 'Kiralux', 'Thorlabs DCX', 'Webcam', 'Colour Webcam']
    camSources = ['ProcessorInterface', 'SimulatedCamera', 'FleaCameraInterface', 'KiraluxCamera', 'DCXCameraInterface', 'WebCamera', 'WebCameraColour']
          
    # Default source for simulated camera
    sourceFilename = Path('../examples/data/vid_example.tif')
    
    # The size of the queue for raw images from the camera. If this is exceeded
    # then the oldest image will be removed.
    rawImageBufferSize = 10
    
    # GUI display defaults
    imageDisplaySize = 300
    controlPanelSize = 220
    
    # Timer interval defualts (ms)
    GUIupdateInterval = 100
    imagesUpdateInterval = 5
      
    # Defaults
    currentImage = None
    camOpen = False
    backgroundImage = None
    imageProcessor = None
    currentProcessedImage = None
    manualImageTransfer = False
    recording = False
    videoOut = None
    numFramesRecorded  = 0
    imageThread = None
    imageProcessor = None
    cam = None
    rawImage = None
    settings = {}   
  
    
    
    def __init__(self, parent=None):   
        """ Initial setup of GUI.
        """
        
        super(CAS_GUI, self).__init__(parent)

        # Create the GUI. This is generally over-ridden in sub-classes
        self.create_layout()
        
        self.set_colour_scheme()
        
        # Creates timers for GUI and camera acquisition
        self.create_timers()         
        self.acquisitionLock = Lock()
    
        # Load last values for GUI from registry
        self.settings = QtCore.QSettings(self.authorName, self.appName)  
        self.gui_restore()
        
        # In case software is being used for first time, we can implement some
        # useful defaults (for example in a sub-class)
        self.apply_default_settings()

        # Put the window in a sensible position
        self.move(0,0)
        
        # Make sure the display is correct for whatever camera source 
        # we initiallylly have selected
        self.handle_cam_source_change()
        
        
    def apply_default_settings(self):
        """Overload this function in sub-class to provide defaults"""
        pass
    
        
    def create_timers(self):
        """ Timers are used for image acquisition and GUI updates"""

        # Create timer for GUI updates
        self.GUITimer=QTimer()
        self.GUITimer.timeout.connect(self.update_GUI)        
        
        # Create timer for image processing
        self.imageTimer=QTimer()
        self.imageTimer.timeout.connect(self.handle_images)
        
        
    def create_layout(self):
        """ Assemble the GUI from Qt Widget. Overload this in subclass to
        define a custom layout.
        """

        # Create a standard layout, with panels arranged horizontally
        self.create_standard_layout(title = self.windowTitle, iconFilename = self.iconFilename)

        # Add an image display. The reference to the display must be stored
        # in self.mainDisplay in order for handle_images to work.
        self.mainDisplay, self.mainDisplayFrame =  self.create_image_display()       
        self.layout.addLayout(self.mainDisplayFrame)
        
        # Add a scroll-bar to the image display which will be shown only when
        # we load a file containing multiple images, so that we can scroll through them
        self.create_file_index_control()
       
        # Create the panel with camera control options (e.g. exposure)
        self.camControlPanel = self.create_cam_control_panel(self.controlPanelSize) 
        self.layout.addWidget(self.camControlPanel)
        
        # Make the start button visible and end button invisible
        self.endBtn.setVisible(False)
        self.startBtn.setVisible(False)
        
        # Logo
        if self.logoFilename is not None:
            self.create_logo_bar()
        
        
    
    def create_standard_layout(self, title = "Kent Camera Acquisition System", iconFilename = None):
        """ Creates a standard layout where each panel is arranged horizontally.
        Specify the window title as an optional argument.
        Returns tuple of references to the layout and the widget it sits inside.
        """        
        
        self.setWindowTitle(title) 
        
        self.outerFrame = QFrame()
        self.outerLayout = QVBoxLayout()
        self.outerFrame.setLayout(self.outerLayout)
        
        self.mainWidget = QWidget()
        self.layout = QHBoxLayout()
        self.mainWidget.setLayout(self.layout)
        
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        #self.outerLayout.setSpacing(0)
        #self.outerLayout.setContentsMargins(0, 0, 0, 0)
        
        
        self.outerLayout.addWidget(self.mainWidget)
        
        
        self.setCentralWidget(self.outerFrame)
        
        if iconFilename is not None:
            self.setWindowIcon(QtGui.QIcon(iconFilename))
        
        return 

    
    def create_image_display(self, name = "Image Display", statusBar = True, autoScale = True):
        """ Adds an image display to the standard layout. Returns tuple of reference to image
        display widget and reference to container widget in which this sits. These references
        must be kept in scope.
        
        """
        
        # Create an instance of an ImageDisplay with the required properties
        display = ImageDisplay(name = name)
        display.isStatusBar = statusBar
        display.autoScale = autoScale
        
        # Create an outer widget to put the display frame in
        displayFrame = QVBoxLayout()
        displayFrame.addWidget(display)

        
        return display, displayFrame
       
     
    def create_logo_bar(self):
        """ Adds logo at the bottom.
        """
        self.logobar = QHBoxLayout()        
        logo = QLabel()
        pixmap = QPixmap(self.logoFilename)
        logo.setPixmap(pixmap)
        self.logobar.addWidget(logo)
        self.outerLayout.addLayout(self.logobar)
        
        
     
    def create_file_index_control(self):
        """ Creates a control to allow the frame from within an image stack to
        be changed.
        """
        
        self.fileIdxWidget = QWidget()
        self.fileIdxWidgetLayout = QHBoxLayout()
        self.fileIdxWidget.setLayout(self.fileIdxWidgetLayout)
        self.fileIdxSlider = QSlider(QtCore.Qt.Horizontal)
        self.fileIdxSlider.valueChanged[int].connect(self.handle_change_file_idx_slider)
        self.fileIdxWidgetLayout.addWidget(QLabel("Frame No.:"))
        self.fileIdxWidgetLayout.addWidget(self.fileIdxSlider)
        self.mainDisplayFrame.addWidget(self.fileIdxWidget)        
        self.fileIdxInput = QSpinBox()
        self.fileIdxWidgetLayout.addWidget(self.fileIdxInput)
        self.fileIdxInput.valueChanged[int].connect(self.handle_change_file_idx)
        
     
    def create_cam_control_panel(self, controlPanelSize = 150, **kwargs):  
        """ Creates a camera control panel. Optionally specify the
        width in pixels.
        Returns a reference to the control panel. This reference must be kept.
        """

        controlPanel = init_cam_control_panel(self, controlPanelSize, **kwargs) 
        return controlPanel
        
        

    def create_processors(self):
        """Subclasses should overload this to create processing threads."""
        pass
      

    def set_colour_scheme(self, scheme = 'dark'):
        """ Sets the colour scheme for the GUI. Currently only supports the
        default 'dark' scheme and 'black' scheme.
        """
        QtWidgets.QApplication.setStyle("Fusion")

        palette = QtWidgets.QApplication.palette()

        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.black)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        palette.setColor(QPalette.Disabled, QPalette.Light, Qt.black)
        palette.setColor(QPalette.Disabled, QPalette.Shadow, QColor(12, 15, 16))
            
        if scheme == 'dark':
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
        elif scheme == 'black':
            palette.setColor(QPalette.Window, QColor(0, 0, 0))

        QtWidgets.QApplication.setPalette(palette)
        
    
    def create_control_panel_container(self,name = "Menu", panelSize = 200, compact = True):
        """
        Creates a panel for menu options.
        """
        
        controlPanel = QWidget()
        controlPanel.setLayout(topLayout:=QVBoxLayout())
        controlPanel.setMaximumWidth(panelSize)
        controlPanel.setMinimumWidth(panelSize) 
        
        widget = QGroupBox(name)
        topLayout.addWidget(widget)
        
        layout=QVBoxLayout()
        widget.setLayout(layout) 

        if compact:
            topLayout.addStretch()
        
        return controlPanel, widget, layout
    
    

    def handle_images(self):
        """ Called regularly by a timer to deal with input images. If a processor
        is defined by the sub-class, this will handle processing. Overload for
        a custom processing pipeline.
        """
        # Grab the most up-to-date image for display. If not None, we store
        # this in currentImage which is the image displayed in the GUI if the 
        # raw image is being displayed.

        gotRawImage = False
        gotProcessedImage = False
        rawImage = None
        
        
        if self.imageProcessor is not None:
            
            # If we have an image processor defined and we are doing manual image
            # transfer to a separate input queue to the processor (rather than queue
            # sharing), and we have a raw image ready, we copy the image to the 
            # processor input queue     
            
            if self.imageProcessor is not None and self.manualImageTransfer is True:
                if self.imageThread.is_image_ready():
                    rawImage = self.imageThread.get_next_image()
                    if rawImage is not None:
                        self.imageProcessor.add_image(rawImage) 
            
            # If there is a new processed image, pull it off the queue
            if self.imageProcessor.is_image_ready() is True:
                gotProcessedImage = True
                self.currentProcessedImage = self.imageProcessor.get_next_image()
        
        elif self.imageThread is not None:
            
            self.currentProcessedImage = None 
         
            if self.imageThread.is_image_ready():
                rawImage  = self.imageThread.get_latest_image()
        
        else:
            
            self.currentProcessedImage = None 

        
        if self.imageThread is not None:

            rawImage  = self.imageThread.get_latest_image()
               
            if rawImage is not None:
                gotRawImage = True
                self.currentImage = rawImage        

        if self.recording and self.videoOut is not None:
            
            if self.currentProcessedImage is not None and gotProcessedImage:
                imToSave = self.currentProcessedImage
            elif self.currentImage is not None and gotRawImage:  
                imToSave = self.currentImage
            else:
                imToSave = None 
            
            if imToSave is not None:
                self.numFramesRecorded = self.numFramesRecorded + 1
                if imToSave.ndim  == 3:
                    outImg = imToSave
                else:
                    outImg = np.zeros((np.shape(imToSave)[0], np.shape(imToSave)[1], 3), dtype = 'uint8')
                    outImg[:,:,0] = imToSave
                    outImg[:,:,1] = imToSave
                    outImg[:,:,2] = imToSave
                    
                self.videoOut.write(outImg)
            

    def update_image_display(self):
       """ Displays the current raw image. 
       Sub-classes should overload this if additional display boxes used.
       """
       if self.currentProcessedImage is not None:           
           self.mainDisplay.set_image(self.currentProcessedImage)           

       elif self.currentImage is not None:
           self.mainDisplay.set_image(self.currentImage)           
       
        
    def update_camera_status(self):
       """ Updates real-time camera frame rate display. If the camera control
       panel has not been created this will cause an error, so this function
       must be overridden.
       """                 
      
       if self.imageProcessor is not None:
           procFps = self.imageProcessor.get_actual_fps()
           self.processRateLabel.setText(str(round(procFps,1)))
      
       if self.imageThread is not None: 
           nWaiting = self.imageThread.get_num_images_in_queue()
           fps = self.imageThread.get_actual_fps()
       else:
           nWaiting = 0
           fps = 0
       self.frameRateLabel.setText(str(round(fps,1)))
       self.bufferFillLabel.setText(str(nWaiting))
       
       
    def update_camera_ranges_and_values(self):       
        """ After updating a camera parameter, the valid range of other parameters
        might change (e.g. frame rate may affect allowed exposures). Call this
        to update the GUI with correct ranges.
        """    
        if self.cam is not None:
            if self.cam.get_exposure() is not None:
                min, max = self.cam.get_exposure_range()
                self.exposureSlider.setMaximum(math.floor(max))
                self.exposureSlider.setMinimum(math.ceil(min))
                self.exposureInput.setMaximum(math.floor(max))
                self.exposureInput.setMinimum(math.ceil(min))
                self.exposureSlider.setTickInterval(int(round(max - min) / 10))
                self.exposureSlider.setValue(int(self.cam.get_exposure()))
            
            if self.cam.get_gain() is not None:
                min, max = self.cam.get_gain_range()
                self.gainSlider.setMaximum(math.floor(max))
                self.gainSlider.setMinimum(math.ceil(min))
                self.gainInput.setMaximum(math.floor(max))
                self.gainInput.setMinimum(math.ceil(min))
                self.gainSlider.setTickInterval(int(round(max - min) / 10))
                self.gainSlider.setValue(int(self.cam.get_gain()))
            
            self.cam.set_frame_rate_on()
            if self.cam.is_frame_rate_enabled():
                self.frameRateSlider.setEnabled = True
                self.frameRateInput.setEnabled = True
                min, max = self.cam.get_frame_rate_range()
                self.frameRateSlider.setMaximum(math.floor(max))
                self.frameRateSlider.setMinimum(math.ceil(min))
                self.frameRateInput.setMaximum(math.floor(max))
                self.frameRateInput.setMinimum(math.ceil(min))
                self.frameRateSlider.setTickInterval(int(round(max - min) / 10))
                self.frameRateInput.setValue((self.cam.get_frame_rate()))
            else:
                self.frameRateInput.setValue((self.cam.get_frame_rate()))
                self.frameRateSlider.setEnabled = False
                self.frameRateInput.setEnabled = False


    def update_camera_ranges(self):       
        """ After updating a camera parameter, the valid range of other parameters
        might change (e.g. frame rate may affect allowed exposures). Call this
        to update the GUI with correct ranges.
        """    
        if self.cam is not None:
            if self.cam.get_exposure() is not None:
                min, max = self.cam.get_exposure_range()
                self.exposureSlider.setMaximum(math.floor(max))
                self.exposureSlider.setMinimum(math.ceil(min))
                self.exposureInput.setMaximum(math.floor(max))
                self.exposureInput.setMinimum(math.ceil(min))
                self.exposureSlider.setTickInterval(int(round(max - min) / 10))
            
            if self.cam.get_gain() is not None:
                min, max = self.cam.get_gain_range()
                self.gainSlider.setMaximum(math.floor(max))
                self.gainSlider.setMinimum(math.ceil(min))
                self.gainInput.setMaximum(math.floor(max))
                self.gainInput.setMinimum(math.ceil(min))
                self.gainSlider.setTickInterval(int(round(max - min) / 10))
            
            self.cam.set_frame_rate_on()
            if self.cam.is_frame_rate_enabled():
                self.frameRateSlider.setEnabled = True
                self.frameRateInput.setEnabled = True
                min, max = self.cam.get_frame_rate_range()
                self.frameRateSlider.setMaximum(math.floor(max))
                self.frameRateSlider.setMinimum(math.ceil(min))
                self.frameRateInput.setMaximum(math.floor(max))
                self.frameRateInput.setMinimum(math.ceil(min))
                self.frameRateSlider.setTickInterval(int(round(max - min) / 10))
            else:
                self.frameRateSlider.setEnabled = False
                self.frameRateInput.setEnabled = False    
       
                     
    def update_camera_from_GUI(self):
        """ Write the currently selecte frame rate, exposure and gain to the camera
        """
        if self.camOpen:             
            self.cam.set_frame_rate(self.frameRateInput.value())
            self.cam.set_gain(self.gainSlider.value())
            self.cam.set_exposure(self.exposureSlider.value())
    
        
    def update_GUI(self):
        """ Update the image(s) and the status displays
        """
        
        self.update_camera_status()
        #t1 = time.perf_counter()
        self.update_image_display()
        #print(time.perf_counter() - t1)
        if self.recording is True:
            self.recordBtn.setText('Stop Recording')
        else:
            self.recordBtn.setText('Start Recording')
        
    
    def start_acquire(self):       
        """ Begin acquiring images by creating an image acquiistion thread 
        and starting it. The image acquisition thread grabs images to a queue
        which can then be retrieved by the GUI for processing/display
        """
        
        # Take the camera source selected in the GUI
        self.camSource = self.camSources[self.camSourceCombo.currentIndex()]
        
        if self.camSource == 'SimulatedCamera':
            
            # If we are using a simulated camera, ask for a file if not hard-coded
            if self.sourceFilename is None:
                self.sourceFilename = QFileDialog.getOpenFileName(filter  = '*.tif')[0]
                
            self.imageThread = ImageAcquisitionThread('SimulatedCamera', self.rawImageBufferSize, self.acquisitionLock, filename=self.sourceFilename)
            #self.imageThread = ImageAcquisitionHandler('SimulatedCamera', self.rawImageBufferSize, filename=self.sourceFilename )
            
            self.cam = self.imageThread.get_camera()
            self.cam.pre_load(-1)
        else:
            self.imageThread = ImageAcquisitionThread(self.camSource, self.rawImageBufferSize, self.acquisitionLock)


        # Sub-classes can overload create_processor to create processing threads
        self.create_processors()    

        self.cam = self.imageThread.get_camera()

        if self.cam is not None:
   
            self.camOpen = True
            #self.update_camera_ranges()
            self.update_camera_from_GUI()
            self.update_camera_ranges()
            self.update_image_display()
            
            # Start the camera image acquirer  and the timers 
            self.imageThread.start()       
            self.GUITimer.start(self.GUIupdateInterval)
            self.imageTimer.start(self.imagesUpdateInterval)
            
            # Flip which buttons will work
            self.endBtn.setVisible(True)
            self.startBtn.setVisible(False)
      

    def end_acquire(self):  
        """ Stops the image acquisition by stopping the image acquirer thread
        """
        if self.camOpen == True:
            self.GUITimer.stop()
            self.imageTimer.stop()
            self.imageThread.stop()
            self.camOpen = False
            self.endBtn.setVisible(False)
            self.startBtn.setVisible(True)
       
        
    def load_file_click(self):
        """ Handles a click of the load file button.
        """
        self.load_file()
        
        
    def load_file(self):        
        """Gets a filename. If it is valid, switches to file mode, stops timers 
        and image threads, loads in image and starts processor"""
        
        filename, filter = QFileDialog.getOpenFileName(parent=self, caption='Select file', filter='*.tif; *.png')
        if filename != "":
            if self.camOpen:
                try:
                    self.imageThread.stop()
                    self.imageTimer.stop()
                    self.GUITimer.stop()
                except:
                    print("could not close camera")
            self.cam = FileInterface(filename = filename)
            if self.cam.is_file_open():
                if self.imageProcessor is None: self.create_processors()    
                self.update_file_processing()
                self.fileIdxInput.setMaximum(self.cam.get_number_images() - 1)
                self.fileIdxSlider.setMaximum(self.cam.get_number_images() - 1)

            else:
                QMessageBox.about(self, "Error", "Could not load file.") 
                

    def handle_change_file_idx(self, event):
        """ Handles change in the spinbox which controls which image in a 
        multi-page tif is shown.
        """
        
        if self.cam is not None:
            self.cam.set_image_idx(self.fileIdxInput.value())
            self.update_file_processing()
        self.fileIdxSlider.setValue(self.fileIdxInput.value())
        
        
        
    def handle_change_file_idx_slider(self, event): 
        """ Handles change in the slider which controls which image in a 
        multi-page tif is shown.
        """
        self.fileIdxInput.setValue(self.fileIdxSlider.value())
            

   
    def update_file_processing(self):
        """ For use when processing a file, not live feeds. Whenever we need
        to reprocessed the file (e.g. due to changed processing options)
        this function can be called. It processes the current raw image, 
        updates currentProcessedImage, and then refreshes displayed
        images and GUI  
        """  
        #t1 = time.perf_counter()
        try:
            self.currentImage = self.cam.get_image()
            #print("Time to get image:", time.perf_counter() - t1)
        except:
            pass
        #t1 = time.perf_counter()
        if self.imageProcessor is not None and self.currentImage is not None:
            self.currentProcessedImage = self.imageProcessor.process_frame(self.currentImage)
        #print("Time to process image:", time.perf_counter() - t1)

        #t1 = time.perf_counter()
        self.update_image_display()
        #print("Time to update display", time.perf_counter() - t1)

        #t1 = time.perf_counter()
        self.update_GUI()
        #print("Time to update GUI", time.perf_counter() - t1)

    
    def handle_exposure_slider(self):
        """ Called when exposure slider is moved. Updates the camera exposure.
        """
        self.exposureSlider.setValue(self.exposureInput.value())
        if self.camOpen == True: 
            self.cam.set_exposure(self.exposureSlider.value())
            self.update_camera_ranges()
             
           
    def handle_gain_slider(self):
        """ Called when gain slider is moved. Updates the camera exposure.
        """
        self.gainInput.setValue(int(self.gainSlider.value()))
        if self.camOpen == True: 
            self.cam.set_gain(self.gainSlider.value())
            self.update_camera_ranges()
          
             
    def handle_frame_rate_slider(self):
        """ Called when frame rate slider is moved. Updates the camera exposure.
        """
        self.frameRateSlider.setValue(self.frameRateInput.value())
        if self.camOpen:             
            self.cam.set_frame_rate(self.frameRateInput.value())
            fps = self.cam.get_frame_rate()
            self.update_camera_ranges()
    
        
    def closeEvent(self, event):
        """ Called when main window closed.
        """ 

        if self.camOpen:
            self.end_acquire()
        if self.imageProcessor is not None:
            self.imageProcessor.stop() 
        self.gui_save()
        active = mp.active_children()
        for child in active:
            child.terminate()
           
    ### Button Click Handlers        

    def load_background_click(self, event):
        self.load_background()
        
        
    def load_background_from_click(self, event):
        self.load_background_from()     
        
                
    def save_background_click(self,event):
        self.save_background()
        
        
    def save_background_as_click(self,event):
        self.save_background_as()
        
        
    def acquire_background_click(self,event):
        self.acquire_background()
    
    
    def save_image_as_button_click(self, event):
        """ Requests filename then saves current processed image. If there
        is no processed image, try to save raw image instead.
        """
        im = self.currentProcessedImage
        if im is not None:
            try:
                filename = QFileDialog.getSaveFileName(self, 'Select filename to save to:', '', filter='*.tif')[0]
            except:
                filename = None
            if filename is not None and filename != "":
                self.save_image_ac(im, filename)
            else:
                QMessageBox.about(self, "Error", "Invalid filename.")  

        else:
            # If there is no processed image, try saving the raw image
            self.save_raw_as_button_click(0)

    
    def save_raw_as_button_click(self, event):
        """ Requests filename then saves current raw image.
        """
        
        im = self.currentImage
        if im is not None:
            try:
                filename = QFileDialog.getSaveFileName(self, 'Select filename to save to:', '', filter='*.tif')[0]
            except:
                filename = None
            if filename is not None and self.currentImage is not None and filename != "":
                self.save_image(im, filename)  
        else:
            QMessageBox.about(self, "Error", "There is no image to save.")  


    

    def snap_image_button_click(self, event):
        """ Saves current raw, processed and background images, if they
        exist, to timestamped files in the snaps folder."""
      
        now = datetime.now()
 
        rawFile = Path(now.strftime('../snaps/%Y_%m_%d_%H_%M_%S_raw.tif'))
        procFile = Path(now.strftime('../snaps/%Y_%m_%d_%H_%M_%S_proc.tif'))
        backFile = Path(now.strftime('../snaps/%Y_%m_%d_%H_%M_%S_back.tif'))
        
        if self.currentImage is not None:
            self.save_image(self.currentImage, rawFile)             
            if self.currentProcessedImage is not None:
                self.save_image_ac(self.currentProcessedImage, procFile)  
            if self.backgroundImage is not None:
                self.save_image(self.backgroundImage, backFile)
        else:  
            QMessageBox.about(self, "Error", "There is no image to save.")  

     
 

    def record_click(self):
        """ Handles click of start record button.
        """
        
        if self.recording is False:
            self.start_recording()
            self.recordBtn.setText('Stop Recording')
        else:
            self.stop_recording()
            self.recordBtn.setText('Record')

        self.update_GUI()
        
    
    
    
    def save_image_ac(self,img, fileName):
        """ Utility function to save 16 bit image 'img' to file 'fileName' with autoscaling """   
        if fileName:
            img = img.astype('float')
            img = img - np.min(img)
            img = (img / np.max(img) * 2**16).astype('uint16')
            im = Image.fromarray(img)
            im.save(fileName)
        
            
    def save_image(self,img, fileName):
        """ Utility function to save image 'img' to file 'fileName' with no scaling"""
        if fileName:            
            im = Image.fromarray(img)
            im.save(fileName)         
            
    
    def pil2np(self,im):
        """ Utility to convert PIL image 'im' to numpy array"""
        return np.asarray(im)        
    
    
    def load_background(self):
        """ Loads the default background file"""
        backIm = Image.open('background.tif')
        if backIm is not None:
             self.backgroundImage = self.pil2np(backIm)
             

    def load_background_from(self):
        """ Requests a filename from user and loads it as background"""
        try:
            filename = QFileDialog.getOpenFileName(self, 'Select background file to load:', '', filter='*.tif; *.png')[0]
        except:
            filename = None
        if filename is not None and filename != "":
            try:
                backIm = Image.open(filename)
            except:
                QMessageBox.about(self, "Error", "Could not load background file.")  
                return
            if backIm is not None:
                self.backgroundImage = self.pil2np(backIm)
        

    def save_background(self):
        """ Save current background to default background file"""
        if self.backgroundImage is not None:
            im = Image.fromarray(self.backgroundImage)
            im.save('background.tif')
        else:
            QMessageBox.about(self, "Error", "There is no background image to save.")  

            

    def save_background_as(self):
        """ Request filename and save current background image to this file"""        
        
        if self.backgroundImage is not None:

            try:
                filename = QFileDialog.getSaveFileName(self, 'Select filename to save to:', '', filter='*.tif')[0]
            except:
                filename = None
            if filename is not None and self.backgroundImage is not None:
                self.save_image(self.backgroundImage, filename)  
        else:
            QMessageBox.about(self, "Error", "There is no background image to save.")  


    def acquire_background(self):
        """ Takes current image as background"""
        if self.currentImage is not None:
            self.backgroundImage = self.currentImage
        else:
            QMessageBox.about(self, "Error", "There is no current image to use as the background.")  


    def start_recording(self):
        
        filename = 'test.avi'
        fourcc = cv.VideoWriter_fourcc(*"MJPG")
        imSize = (np.shape(self.currentImage)[1],np.shape(self.currentImage)[0]) 
        self.numFramesRecorded = 0

        self.videoOut = cv.VideoWriter(filename, fourcc, 20.0, imSize)
        self.recording = True
        
        
    def stop_recording(self):
        if self.videoOut is not None:
            self.videoOut.release()
        self.videoOut = None
        self.recording = False
        
    
    def handle_cam_source_change(self):
        """ Deals with user changing camera source option, including adjusting
        visibility of relevant widgets
        """
        if self.camSourceCombo.currentText() == 'File':
            self.end_acquire()
            
            # Hide camera controls, show file widgets
            self.camSettingsPanel.hide()
            self.camControlGroupBox.hide()
            self.startBtn.hide()
            self.endBtn.hide()    
            self.camStatusPanel.hide()
            self.inputFilePanel.show()
            self.fileIdxWidget.show()

        else:
            # Show camera controls, hide file widgets
            self.camSettingsPanel.show()
            self.camControlGroupBox.show()
            if self.camOpen:
                self.startBtn.hide()
                self.endBtn.show()
            else:    
                self.startBtn.show()
                self.endBtn.hide()
            self.camStatusPanel.show()
            self.inputFilePanel.hide()
            self.fileIdxWidget.hide()


    
    def gui_save(self):
        """ Save all current values in the GUI widgets to registry"""
        
        # Save geometry
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())
    
        for name, obj in inspect.getmembers(self):
          if isinstance(obj, QComboBox):
              name = obj.objectName()  # get combobox name
              index = obj.currentIndex()  # get current index from combobox
              text = obj.itemText(index)  # get the text for current index
              self.settings.setValue(name, text)  # save combobox selection to registry
                            
          if isinstance(obj, QDoubleSpinBox):
              name = obj.objectName()  
              value = obj.value()  
              self.settings.setValue(name, value)  
                            
          if isinstance(obj, QSpinBox):
              name = obj.objectName()  
              value = obj.value()  
              self.settings.setValue(name, value)  
              
          if isinstance(obj, QLineEdit):
              name = obj.objectName()
              value = obj.text()
              self.settings.setValue(name, value)  # save ui values, so they can be restored next time
    
          if isinstance(obj, QCheckBox):
              name = obj.objectName()
              state = obj.isChecked()
              self.settings.setValue(name, state)
              
          if isinstance(obj, QRadioButton):
              name = obj.objectName()
              value = obj.isChecked()  # get stored value from registry
              self.settings.setValue(name, value)



    def gui_restore(self):
      """ Load GUI widgets values/states from registry"""
     
      for name, obj in inspect.getmembers(self):

          if isinstance(obj, QComboBox):

              index = obj.currentIndex()  # get current region from combobox
              name = obj.objectName()
              value = (self.settings.value(name))
    
              if value == "":
                  continue
    
              index = obj.findText(value)  # get the corresponding index for specified string in combobox
    
              if index == -1:  # add to list if not found
                  obj.insertItems(0, [value])
                  index = obj.findText(value)
                  obj.setCurrentIndex(index)
              else:
                  obj.setCurrentIndex(index)  # preselect a combobox value by index
    
          if isinstance(obj, QLineEdit):
              name = obj.objectName()
              if self.settings.value(name) is not None:
                  value = (self.settings.value(name).decode('utf-8'))  # get stored value from registry
                  obj.setText(value)  
                  
          if isinstance(obj, QCheckBox):
              name = obj.objectName()
              value = self.settings.value(name)  # get stored value from registry
              if value != None:
                  obj.setChecked(str2bool(value))  
                  
          if isinstance(obj, QDoubleSpinBox):
              name = obj.objectName()
              value = self.settings.value(name)  # get stored value from registry
              if value != None:
                  if obj.maximum() < float(value):
                      obj.setMaximum(float(value))
                  if obj.minimum() > float(value):
                      obj.setMinimum(float(value))
                  obj.setValue(float(value))  
                  
          if isinstance(obj, QSpinBox):
              name = obj.objectName()
              value = self.settings.value(name)  # get stored value from registry
              if value != None:
                  if obj.maximum() < float(value):
                      obj.setMaximum(float(value))
                  if obj.minimum() > float(value):
                      obj.setMinimum(float(value))
                  obj.setValue(int(value)) 
    
          if isinstance(obj, QRadioButton):
             name = obj.objectName()
             value = self.settings.value(name)  # get stored value from registry
             if value != None:
                 obj.setChecked(str2bool(value))      

# Helper utility 
def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")
   
    
# Launch the GUI
if __name__ == '__main__':
    
   app=QApplication(sys.argv)
   app.setStyle("Fusion")
     
   # Create and display GUI
   window = CAS_GUI()
   window.show()
   
   # When the window is closed, close everything
   sys.exit(app.exec_())

