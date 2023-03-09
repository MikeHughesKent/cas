# -*- coding: utf-8 -*-
"""
Kent-CAS-GUI
Camera Acquisition System (CAS) GUI Base Class

CAS_GUI is a graphical user interface built around the 
Kent Camera Acquisition System (CAS).

By itself, this class allows camera images or files to be viewed in real time. 

It is intended as a base class to be extended by more complete programs that
provide further functionality.

@author: Mike Hughes
Applied Optics Group
University of Kent

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
from ImageDisplay import ImageDisplay

from cam_control_panel import *

from ImageAcquisitionHandler import ImageAcquisitionHandler
from FileInterface import FileInterface

from DummyThread import DummyThread

from datetime import datetime

from threading import Lock
cuda = True


class CAS_GUI(QMainWindow):
    
    authorName = "AOG"
    appName = "CAS"
        
    # Define available cameras
    camNames = ['File', 'Simulated Camera', 'Flea Camera', 'Kiralux', 'Thorlabs DCX', 'Webcam']
    camSources = ['ProcessorInterface', 'SimulatedCamera', 'FleaCameraInterface', 'KiraluxCamera', 'DCXCameraInterface', 'WebCamera']
          
    # Default source for simulated camera
    sourceFilename = r"..\tests\test_data\im1.tif"
    
    rawImageBufferSize = 10
    
    # Gui display defaults
    imageDisplaySize = 300
    controlPanelSize = 220
    
    # Timer interval defualts (ms)
    GUIupdateInterval = 200
    imagesUpdateInterval = 1
        
    currentImage = None
    camOpen = False
    backgroundImage = None
    imageProcessor = None
    currentProcessedImage = None
    manualImageTransfer = False
    recording = False
    
    settings = {}   
  
    imageThread = None
    imageProcessor = None
    
    def __init__(self,parent=None):    
        
        super(CAS_GUI, self).__init__(parent)

        self.create_layout()
        self.create_timers()  
        
        self.acquisitionLock = Lock()
    
        # Load last values for GUI from registry
        self.settings = QtCore.QSettings(self.authorName, self.appName)  
        self.gui_restore()
        
        # In case software is being used for first time, we implement some
        # useful defaults
        #self.apply_default_settings()

        self.move(0,0)
        #self.lock = threading.Lock()
        self.handle_cam_source_change()
        
        
    def apply_default_settings():
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
        """ Asemble the GUI from Qt Widget. Overload this in subclass to
        define a custom layout """

        self.setWindowTitle('Camera Acquisition System')       

        self.layout = QHBoxLayout()
        self.mainDisplayFrame = QVBoxLayout()
        
        # Create the image display widget which will show the video
        self.mainDisplay = ImageDisplay(name = "mainDisplay")
        self.mainDisplay.isStatusBar = True
        self.mainDisplay.autoScale = True
       
        # Create the panel with camera control options (e.g. exposure)
        self.camControlPanel = init_cam_control_panel(self, self.controlPanelSize)   
        
        # Add the camera display to a parent layout
        self.mainDisplayFrame.addWidget(self.mainDisplay)
        
        self.layout.addLayout(self.mainDisplayFrame)
        self.layout.addWidget(self.camControlPanel)

        widget = QWidget()
        widget.setLayout(self.layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)
        
        
    def create_processors(self):
        """Subclasses overload this to create processing threads"""
        pass
            
    
    def handle_images(self):
        """ Called regularly by a timer to deal with input images. If a processor
        is defined by the sub-class, this will handle processing. Overload for
        a custom processing pipeline"""
        
        # Grab the most uptodate image for display. If it is an image, we store
        # this in currentImage which is the image displayed in the GUI (if the 
        # raw image is being displayed.)
        if self.imageThread is not None:
            im = self.imageThread.get_latest_image()
            if im is not None:
                self.currentImage = im        
                
        # If we have an image processor defined and we are doing manual image
        # transfer to a separate input queue to the processor (rather than queue
        # sharing), we copy the image to the processor input queue        
        if self.imageProcessor is not None and self.manualImageTransfer is True:
            rawImage = self.imageThread.get_next_image()
            if rawImage is not None:
                self.imageProcessor.add_image(rawImage)            
           
        # If image processor present, get the latest processed image from the image processor    
        if self.imageProcessor is not None: 
            if self.imageProcessor.is_image_ready() is True:
                self.currentProcessedImage = self.imageProcessor.get_next_image()
        else:
        # If no image processor then remove the image from the queue
            self.currentProcessedImage = None 
            temp = self.imageThread.get_next_image()
    

    def update_image_display(self):
       """ Displays the current raw image. 
       Sub-classes should overload this if additional displays used."""
       
       if self.currentImage is not None:
           self.mainDisplay.set_mono_image(self.currentImage)           
       
        
    def update_camera_status(self):
       """ Updates real-time camera frame rate display"""                 
      
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
       
       
    def update_camera_ranges(self):       
        """ After updating a camera parameter, the valid range of other parameters
        might change (e.g. frame rate may affect allowed exposures). Call this
        to update the GUI with correct ranges """    
        if self.cam.get_exposure() is not None:
            self.exposureSlider.setValue((self.cam.get_exposure()))
            min, max = self.cam.get_exposure_range()
            self.exposureSlider.setMaximum((max))
            self.exposureSlider.setMinimum((min))
            self.exposureInput.setMaximum((max))
            self.exposureInput.setMinimum((min))
            self.exposureSlider.setTickInterval(int(round(max - min) / 10))
        
        if self.cam.get_gain() is not None:
            self.gainSlider.setValue(int(self.cam.get_gain()))
            min, max = self.cam.get_gain_range()
            self.gainSlider.setMaximum(math.floor(max))
            self.gainSlider.setMinimum(math.ceil(min))
            self.gainInput.setMaximum(math.floor(max))
            self.gainInput.setMinimum(math.ceil(min))
            self.gainSlider.setTickInterval(int(round(max - min) / 10))
        
        if self.cam.is_frame_rate_enabled():
            min, max = self.cam.get_frame_rate_range()
            self.frameRateInput.setValue((self.cam.get_frame_rate()))
            self.frameRateSlider.setMaximum((max))
            self.frameRateSlider.setMinimum((min))
            self.frameRateInput.setMaximum((max))
            self.frameRateInput.setMinimum((min))
            self.frameRateSlider.setTickInterval(int(round(max - min) / 10))
        else:
            self.frameRateSlider.setEnabled = False

        
    def handle_exposure_slider(self):
        self.exposureSlider.setValue(self.exposureInput.value())
        if self.camOpen == True: 
            self.cam.set_exposure(self.exposureSlider.value())
            self.update_camera_ranges()
            
          
    def handle_gain_slider(self):
        self.gainInput.setValue(int(self.gainSlider.value()))
        if self.camOpen == True: 
            self.cam.set_gain(self.gainSlider.value())
            self.update_camera_ranges()
         
            
    def handle_frame_rate_slider(self):
        self.frameRateSlider.setValue(self.frameRateInput.value())
        if self.camOpen:             
            self.cam.set_frame_rate(self.frameRateInput.value())
            fps = self.cam.get_frame_rate()
            self.update_camera_ranges()
    
                     
    def update_camera_from_GUI(self):
        if self.camOpen:             
            self.cam.set_frame_rate(self.frameRateInput.value())
            self.cam.set_gain(self.gainSlider.value())
            self.cam.set_exposure(self.exposureSlider.value())
    
        
    def update_GUI(self):
        self.update_image_display()
        self.update_camera_status()
        if self.recording is True:
            self.recordBtn.setText('Stop Recording')
        else:
            self.recordBtn.setText('Start Recording')
        
    
    def start_acquire(self):       
        """ The image acquisition thread grabs images to a Queue which can then
         be retrieved by the GUI for processing/display"""
        
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
            #self.imageThread = ImageAcquisitionHandler(self.camSource, self.rawImageBufferSize)

        self.create_processors()    

        self.cam = self.imageThread.get_camera()

        if self.cam is not None:
            self.camOpen = True
            self.update_camera_ranges()
            self.update_camera_from_GUI()
            self.update_camera_ranges()

            self.update_image_display()
            
            # Start the camera image acquirer  
            self.imageThread.start()       
            self.GUITimer.start(self.GUIupdateInterval)
            self.imageTimer.start(self.imagesUpdateInterval)
            self.endBtn.setEnabled(True)
            self.startBtn.setEnabled(False)
      

    def end_acquire(self):  
        if self.camOpen == True:
            self.GUITimer.stop()
            self.imageTimer.stop()
            try:
                self.imageThread.stop()
            except:
                print("could not close camera")
            self.camOpen = False
            self.endBtn.setEnabled(False)
            self.startBtn.setEnabled(True)
       
        
    def load_file_click(self):
        self.load_file()
        
        
    def load_file(self):        
        """Switches to file mode, stops timers and image threads, loads in image
        and starts processor"""
        
        filename, filter = QFileDialog.getOpenFileName(parent=self, caption='Select file', filter='*.tif; *.png')
        if filename is not None:
            if self.camOpen:
                try:
                    self.imageThread.stop()
                    self.imageTimer.stop()
                    self.GUITimer.stop()
                except:
                    print("could not close camera")
            self.cam = FileInterface(filename = filename)
            if self.cam.is_file_open():
                self.create_processors()    
                self.update_file_processing()
            else:
                QMessageBox.about(self, "Error", "Could not load file.")  

   
    def update_file_processing(self):
        """ For use when processing a file. Processes current raw image, 
        # updating currentProcessedImage, and then refreshes displayed
        # images and GUI  """  
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

        
        
    def closeEvent(self, event):
        """ Called when main window closed   """ 

        if self.camOpen:
            self.end_acquire()
        if self.imageProcessor is not None:
            self.imageProcessor.stop() 
        self.gui_save()
        active = mp.active_children()
        for child in active:
            child.terminate()
            

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
        try:
            filename = QFileDialog.getSaveFileName(self, 'Select filename to save to:', '', filter='*.tif')[0]
        except:
            filename = None
        if filename is not None and self.currentProcessedImage is not None:
            self.save_image_ac(self.currentProcessedImage, filename)
            
    
    def save_raw_as_button_click(self, event):
        try:
            filename = QFileDialog.getSaveFileName(self, 'Select filename to save to:', '', filter='*.tif')[0]
        except:
            filename = None
        if filename is not None and self.currentImage is not None:
            self.save_image(self.currentImage, filename)  
 

    def snap_image_button_click(self, event):
      
        now = datetime.now()
 
        rawFile = now.strftime('..\\snaps\\%Y_%m_%d_%H_%M_%S_raw.tif')
        procFile = now.strftime('..\\snaps\\%Y_%m_%d_%H_%M_%S_proc.tif')
        backFile = now.strftime('..\\snaps\\%Y_%m_%d_%H_%M_%S_back.tif')
        
        if self.currentImage is not None:
            self.save_image(self.currentImage, rawFile) 
        if self.currentProcessedImage is not None:
            self.save_image_ac(self.currentProcessedImage, procFile)  
        if self.backgroundImage is not None:
            self.save_image(self.backgroundImage, backFile)
 

    def record_click(self):
        
        if self.recording is False:
            self.start_recording()
        else:
            self.stop_recording()
       
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
        """ Utility function to save image  'img' to file 'fileName' with no scaling"""
        if fileName:            
            im = Image.fromarray(img)
            im.save(fileName)         
            
    
    def pil2np(self,im):
        """ Utility to convert PIL image 'im' to numpy array"""
        return np.array(im.getdata()).reshape(im.size[1], im.size[0])        
    
    
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
        if filename is not None:
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
            

    def save_background_as(self):
        """ Request filename and save current background image to this file"""        
        try:
            filename = QFileDialog.getSaveFileName(self, 'Select filename to save to:', '', filter='*.tif')[0]
        except:
            filename = None
        if filename is not None and self.backgroundImage is not None:
            self.save_image(self.backgroundImage, filename)  
            

    def acquire_background(self):
        """ Takes current image as background"""
        if self.currentImage is not None:
            self.backgroundImage = self.currentImage
             

    def start_recording(self):
        """ For future use"""
        pass
        
        
    def stop_recording(self):  
        """ For future use"""
        pass
        
    
    def handle_cam_source_change(self):
        """ Deals with user changing camera source option, including adjusting
        visibility of relevant widgets"""
        if self.camSourceCombo.currentText() == 'File':
            self.end_acquire()
            # Hide camera controls, show file widgets
            self.camSettingsPanel.hide()
            self.camControlGroupBox.hide()
            self.startBtn.hide()
            self.endBtn.hide()    
            self.camStatusPanel.hide()
            self.inputFilePanel.show()

        else:
            # Show camera controls, hide file widgets
            self.camSettingsPanel.show()
            self.camControlGroupBox.show()
            self.startBtn.show()
            self.endBtn.show()
            self.camStatusPanel.show()
            self.inputFilePanel.hide()

    
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
                  obj.setText(value)  # restore lineEditFile
    
          if isinstance(obj, QCheckBox):
              name = obj.objectName()
              value = self.settings.value(name)  # get stored value from registry
              if value != None:
                  obj.setChecked(str2bool(value))  # restore checkbox
                  
          if isinstance(obj, QDoubleSpinBox):
              name = obj.objectName()
              value = self.settings.value(name)  # get stored value from registry
              if value != None:
                  obj.setValue(float(value))  # restore checkbox
                  
          if isinstance(obj, QSpinBox):
              name = obj.objectName()
              value = self.settings.value(name)  # get stored value from registry
              if value != None:
                  obj.setValue(int(value))  # restore checkbox
    
          if isinstance(obj, QRadioButton):
             name = obj.objectName()
             value = self.settings.value(name)  # get stored value from registry
             if value != None:
                 obj.setChecked(str2bool(value))      

# Helper utility 
def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")
   
    

if __name__ == '__main__':
    
   app=QApplication(sys.argv)
   app.setStyle("Fusion")

   #Now use a palette to switch to dark colors:
   palette = QPalette()
   palette.setColor(QPalette.Window, QColor(53, 53, 53))
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
   
   app.setPalette(palette)  
   
   window=CAS_GUI()
   window.show()
   sys.exit(app.exec_())

