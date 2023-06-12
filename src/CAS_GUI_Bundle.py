# -*- coding: utf-8 -*-
"""
Kent-CAS-GUI Bundle Class
Camera Acquisition System (CAS) GUI Class for developing GUIs that acquire
images through fibre bundles.

CAS_GUI is a graphical user interface built around the 
Kent Camera Acquisition System (CAS).

It is intended as a base class to be extended by more complete programs that
provide further functionality.

@author: Mike Hughes
Applied Optics Group
University of Kent

"""

import sys 
sys.path.append('C:\\Users\\AOG\\Dropbox\\Programming\\Python\\pybundle')

import os
sys.path.append(os.path.abspath("widgets"))
sys.path.append(os.path.abspath("cameras"))
sys.path.append(os.path.abspath("threads"))

import time
import numpy as np
import math

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen

from PIL import Image

import cv2 as cv

from CAS_GUI_Base import CAS_GUI

from ImageAcquisitionThread import ImageAcquisitionThread
from ImageDisplay import ImageDisplay

import matplotlib.pyplot as plt
from cam_control_panel import *

from BundleProcessorHandler import BundleProcessorHandler
from BundleProcessor import BundleProcessor

import pybundle
import pickle


class CAS_GUI_Bundle(CAS_GUI):
    
    mosaicingEnabled = False
    authorName = "AOG"
    appName = "CAS-Bundle"
    camSource = 'SimulatedCamera'
    sourceFilename = r"..\\..\endomicroscope\\test\\data\\raw_example.tif"

    def __init__(self,parent=None):                      
        
        super(CAS_GUI_Bundle, self).__init__(parent)

        
    # Overloaded, call by superclass    
    def create_layout(self):
        
        self.setWindowTitle('Camera Acquisition System: Bundle Processor')

        self.layout = QHBoxLayout()
     
        # Create the image display widget which will show the video
        self.mainDisplayFrame = QVBoxLayout()
        self.mainDisplay = ImageDisplay(name = "mainDisplay")
        self.mainDisplay.isStatusBar = True
        self.mainDisplay.autoScale = True
        self.mainDisplayFrame.addWidget(self.mainDisplay)
        
        # Create the mosaic display widget 
        if self.mosaicingEnabled:
            self.mosaicDisplayFrame = QVBoxLayout()
            self.mosaicControlPanel = self.init_mosaic_panel(self.controlPanelSize)
            self.mosaicDisplay = ImageDisplay(name = "mosaicDisplay")
            self.mosaicDisplay.isStatusBar = False
            self.mosaicDisplay.autoScale = True
            self.mosaicDisplayFrame.addWidget(self.mosaicDisplay)

        # Create the panel with camera control options (e.g. exposure)
        self.camControlPanel = init_cam_control_panel(self, self.controlPanelSize)   
        
        # Create the bundle processing panel
        self.bundleProcessPanel = self.init_bundle_process_panel(self.controlPanelSize)
        
        self.layout.addLayout(self.mainDisplayFrame)
        
        if self.mosaicingEnabled:
            self.layout.addLayout(self.mosaicDisplayFrame)            
           
        self.layout.addWidget(self.camControlPanel)
        self.layout.addWidget(self.bundleProcessPanel)

        if self.mosaicingEnabled:
            self.layout.addWidget(self.mosaicControlPanel)

        widget = QWidget()
        widget.setLayout(self.layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)
        
        
        
    def start_acquire(self):
        super().start_acquire()
        
        
    def create_processors(self):
        """ Overrides base class"""
        if self.imageThread is not None:
            inputQueue = self.imageThread.get_image_queue()
        else:
            inputQueue = None
        self.imageProcessor = BundleProcessor(10,10, inputQueue = inputQueue, mosaic = self.mosaicingEnabled)
        
        if self.imageProcessor is not None:
            self.imageProcessor.start()
        
        if self.mosaicingEnabled:
            self.handle_change_mosaic_options()
        self.handle_changed_bundle_processing()
      
        
    
    def init_bundle_process_panel(self, panelSize):
        """ Create the control panel for fibre bundle processibg"""
               
        self.bundleLoadBackgroundBtn=QPushButton('Load Background')
        self.bundleLoadBackgroundFromBtn = QPushButton('Load Background From')
        self.bundleAcquireBackgroundBtn=QPushButton('Acquire Background')
        self.bundleSaveBackgroundBtn=QPushButton('Save Background')
        self.bundleSaveBackgroundAsBtn=QPushButton('Save Background As')

        self.bundleCoreMethodCombo = QComboBox(objectName = 'bundleCoreMethodCombo')
        self.bundleCoreMethodCombo.addItems(['Filtering', 'Interpolation'])
        self.bundleCalibBtn=QPushButton('Calibrate')
        self.bundleLoadCalibBtn=QPushButton('Load Calibration')
        self.bundleSaveCalibBtn=QPushButton('Save Calibration')
        self.bundleShowRaw = QCheckBox('Show Raw', objectName = 'bundleShowRawCheck')
        
        self.bundleFilterSizeInput = QDoubleSpinBox(objectName = 'bundleFilterSizeInput')
        self.bundleFilterSizeInput.setKeyboardTracking(False)
        
        self.bundleCentreXInput = QSpinBox(objectName = 'bundleCentreXInput')
        self.bundleCentreXInput.setKeyboardTracking(False)
        self.bundleCentreXInput.setMaximum(10**6)
        self.bundleCentreXInput.setMinimum(-10**6)
        
        self.bundleCentreYInput = QSpinBox(objectName = 'bundleCentreYInput')
        self.bundleCentreYInput.setKeyboardTracking(False)
        self.bundleCentreYInput.setMaximum(10**6)
        self.bundleCentreYInput.setMinimum(-10**6)
        
        self.bundleRadiusInput = QSpinBox(objectName = 'bundleRadiusInput')
        self.bundleRadiusInput.setKeyboardTracking(False)
        self.bundleRadiusInput.setMaximum(10**6)
        self.bundleRadiusInput.setMinimum(-10**6)
        
        self.bundleGridSizeInput = QSpinBox(objectName = 'bundleGridSizeInput')
        self.bundleGridSizeInput.setKeyboardTracking(False)
        self.bundleGridSizeInput.setMaximum(10000)
        self.bundleGridSizeInput.setMinimum(1)
        
        self.bundleFindBtn=QPushButton('Locate Bundle')
        
        self.bundleCropCheck = QCheckBox("Crop to bundle", objectName = 'bundleCropCheck')
        self.bundleMaskCheck = QCheckBox("Mask bundle", objectName = 'bundleMaskCheck')
        self.bundleSubtractBackCheck = QCheckBox("Subtract Background", objectName = 'bundleSubtractBackCheck')
        self.bundleNormaliseCheck = QCheckBox("Normalise", objectName = 'bundleNormaliseCheck')
        
        bundlePanel = QWidget()
        bundlePanel.setLayout(topLayout:=QVBoxLayout())
        bundlePanel.setMaximumWidth(panelSize)
        bundlePanel.setMinimumWidth(panelSize)
        
        groupBox = QGroupBox("Bundle Pre-processing")
        topLayout.addWidget(groupBox)
        groupBox.setLayout(layout:=QVBoxLayout())

        layout.addWidget(self.bundleAcquireBackgroundBtn)
        layout.addWidget(self.bundleLoadBackgroundBtn)
        layout.addWidget(self.bundleLoadBackgroundFromBtn)

        layout.addWidget(self.bundleSaveBackgroundBtn)
        layout.addWidget(self.bundleSaveBackgroundAsBtn)
        
        hr1 = QFrame ()
        hr1.setFrameShape(QFrame.HLine)
        hr1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(hr1)
        
        layout.addWidget(self.bundleFindBtn)  

        bcx = QHBoxLayout()
        bcx.addWidget(QLabel("Bundle X:"))
        bcx.addWidget(self.bundleCentreXInput)
        layout.addLayout(bcx)

        bcy = QHBoxLayout()
        bcy.addWidget(QLabel("Bundle Y:"))
        bcy.addWidget(self.bundleCentreYInput)
        layout.addLayout(bcy)

        bcr = QHBoxLayout()
        bcr.addWidget(QLabel("Bundle Rad:"))
        bcr.addWidget(self.bundleRadiusInput)
        layout.addLayout(bcr)
        
        hr2 = QFrame ()
        hr2.setFrameShape(QFrame.HLine)
        hr2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(hr2)
        
        layout.addWidget(self.bundleShowRaw)
        layout.addWidget(QLabel("Pre-processing Method:"))
        layout.addWidget(self.bundleCoreMethodCombo)
        
        # Panel with options for interpolation
        self.interpProcessPanel = QWidget()
        self.interpProcessPanel.setLayout(interpLayout:=QVBoxLayout())
        interpLayout.addWidget(self.bundleCalibBtn)
        interpLayout.addWidget(self.bundleLoadCalibBtn)
        interpLayout.addWidget(self.bundleSaveCalibBtn)
        interpLayout.setContentsMargins(0,0,0,0)       
        layout.addWidget(self.interpProcessPanel)
        ####
       
        # Panel with options for filtering
        self.filterProcessPanel = QWidget()
        self.filterProcessPanel.setLayout(fppLayout:=QVBoxLayout())
        fppLayout.addWidget(QLabel('Filter size:'))
        fppLayout.addWidget(self.bundleFilterSizeInput)
        fppLayout.setContentsMargins(0,0,0,0)
        fppLayout.addWidget(self.bundleCropCheck)
        fppLayout.addWidget(self.bundleMaskCheck)
        layout.addWidget(self.filterProcessPanel)
        ####
        
        layout.addWidget(self.bundleSubtractBackCheck)
        layout.addWidget(self.bundleNormaliseCheck)
        
        bcs = QHBoxLayout()
        bcs.addWidget(QLabel("Image Pixels:"))
        bcs.addWidget(self.bundleGridSizeInput)
        layout.addLayout(bcs)
        
        topLayout.addStretch()
    
        self.bundleCoreMethodCombo.currentIndexChanged[int].connect(self.handle_changed_bundle_processing)
        self.bundleFilterSizeInput.valueChanged[float].connect(self.handle_changed_bundle_processing)
        self.bundleCentreXInput.valueChanged[int].connect(self.handle_changed_bundle_processing)
        self.bundleCentreYInput.valueChanged[int].connect(self.handle_changed_bundle_processing)
        self.bundleRadiusInput.valueChanged[int].connect(self.handle_changed_bundle_processing)
        self.bundleFindBtn.clicked.connect(self.handle_bundle_find)
        self.bundleShowRaw.stateChanged.connect(self.handle_changed_bundle_processing)
        self.bundleCropCheck.stateChanged.connect(self.handle_changed_bundle_processing)
        self.bundleMaskCheck.stateChanged.connect(self.handle_changed_bundle_processing)
        self.bundleSubtractBackCheck.stateChanged.connect(self.handle_changed_bundle_processing)
        self.bundleNormaliseCheck.stateChanged.connect(self.handle_changed_bundle_processing)
        self.bundleAcquireBackgroundBtn.clicked.connect(self.acquire_background_click)
        self.bundleLoadBackgroundBtn.clicked.connect(self.load_background_click)
        self.bundleLoadBackgroundFromBtn.clicked.connect(self.load_background_from_click)
        self.bundleSaveBackgroundBtn.clicked.connect(self.save_background_click)
        self.bundleSaveBackgroundAsBtn.clicked.connect(self.save_background_as_click)

        self.bundleLoadCalibBtn.clicked.connect(self.handle_load_calibration)
        self.bundleSaveCalibBtn.clicked.connect(self.handle_save_calibration)
        self.bundleGridSizeInput.valueChanged[int].connect(self.handle_changed_bundle_processing)
        self.bundleCalibBtn.clicked.connect(self.handle_calibrate)        
        
        return bundlePanel


    def init_mosaic_panel(self, panelSize):
        """ Creates the panel with mosaicing options"""
        
        mosaicPanel = QWidget()
        mosaicPanel.setLayout(topLayout:=QVBoxLayout())
        mosaicPanel.setMaximumWidth(panelSize)
        mosaicPanel.setMinimumWidth(panelSize)
        groupBox = QGroupBox("Mosaicing")
        topLayout.addWidget(groupBox)
        groupBox.setLayout(layout:=QVBoxLayout())
        
        self.resetMosaicBtn=QPushButton('Reset mosaic')
        self.saveMosaicBtn=QPushButton('Save mosaic')
        self.mosaicThresholdInput = QDoubleSpinBox(objectName = 'mosaicThresholdInput')
        self.mosaicThresholdInput.setMaximum(1)
        self.mosaicThresholdInput.setMinimum(0)
        
        self.mosaicIntensityInput = QDoubleSpinBox(objectName = 'mosaicIntensityInput')
        self.mosaicIntensityInput.setMaximum(10**6)
        self.mosaicIntensityInput.setMinimum(0)
        
        self.mosaicCOVInput = QDoubleSpinBox(objectName = 'mosaicCOVInput')
        self.mosaicCOVInput.setMaximum(10**6)
        self.mosaicCOVInput.setMinimum(0)

        self.mosaicOnCheck = QCheckBox("Enable Mosaicing", objectName= "mosaicOnCheck")

        layout.addWidget(self.mosaicOnCheck)
        
        layout.addWidget(QLabel("Correlation threshold (0-1):"))        
        layout.addWidget(self.mosaicThresholdInput)
        
        layout.addWidget(QLabel("Intensity threshold:"))
        layout.addWidget(self.mosaicIntensityInput)
                 
        layout.addWidget(QLabel("Sharpness threshold:"))
        layout.addWidget(self.mosaicCOVInput)
        
        topLayout.addStretch()

        self.resetMosaicBtn.clicked.connect(self.handle_reset_mosaic)
        self.mosaicThresholdInput.valueChanged[float].connect(self.handle_change_mosaic_options)
        self.mosaicIntensityInput.valueChanged[float].connect(self.handle_change_mosaic_options)
        self.mosaicCOVInput.valueChanged[float].connect(self.handle_change_mosaic_options)
        self.mosaicOnCheck.stateChanged.connect(self.handle_change_mosaic_options)

        return mosaicPanel
    

    def update_image_display(self):
        """ Overrides from base class to include mosaicing window"""
        if self.bundleShowRaw.isChecked():
           if self.currentImage is not None:
               self.mainDisplay.set_mono_image(self.currentImage)
        else:
           if self.currentProcessedImage is not None:
               self.mainDisplay.set_mono_image(self.currentProcessedImage)
        
        if self.mosaicingEnabled:
           self.mosaicDisplay.set_mono_image(self.imageProcessor.get_mosaic())       
        
    
    def handle_changed_bundle_processing(self):
        """ Called when any of the widget values/states are changed"""
        
        # Show correct bundle processing options depending on method
        if self.bundleCoreMethodCombo.currentIndex() == 0:
            self.filterProcessPanel.show()
            self.interpProcessPanel.hide()
        elif self.bundleCoreMethodCombo.currentIndex() == 1:
            self.filterProcessPanel.hide()
            self.interpProcessPanel.show()
        
        if self.imageProcessor is not None:
            self.imageProcessor.pyb.gridSize = self.bundleGridSizeInput.value()
            if self.bundleCoreMethodCombo.currentIndex() == 0:
                self.imageProcessor.pyb.set_core_method(self.imageProcessor.pyb.FILTER)
            elif self.bundleCoreMethodCombo.currentIndex() == 1:
                self.imageProcessor.pyb.set_core_method(self.imageProcessor.pyb.TRILIN)    
                
            self.imageProcessor.pyb.filterSize = self.bundleFilterSizeInput.value()
            if self.bundleCropCheck.isChecked():
                self.imageProcessor.crop = (self.bundleCentreXInput.value(), self.bundleCentreYInput.value(), self.bundleRadiusInput.value())
            else:
                self.imageProcessor.crop = None
                
            self.imageProcessor.pyb.set_loc((self.bundleCentreXInput.value(), self.bundleCentreYInput.value(), self.bundleRadiusInput.value()))
            self.imageProcessor.pyb.set_crop(self.bundleCropCheck.isChecked())
            self.imageProcessor.pyb.set_auto_contrast(False)
            if self.bundleMaskCheck.isChecked():
                self.imageProcessor.pyb.set_apply_mask(True) 
                self.imageProcessor.pyb.set_auto_mask(True)
            else:
                self.imageProcessor.pyb.set_apply_mask(False) 
                self.imageProcessor.pyb.set_mask(None)
                
            if self.bundleSubtractBackCheck.isChecked():
                self.imageProcessor.pyb.set_background(self.backgroundImage)
            else:
                self.imageProcessor.pyb.set_background(None)

        
            if self.bundleNormaliseCheck.isChecked():
                self.imageProcessor.pyb.set_normalise_image(self.backgroundImage)   
            else:
                self.imageProcessor.pyb.set_normalise_image(None)

    
            self.imageProcessor.pyb.set_filter_size(self.bundleFilterSizeInput.value())    
            self.imageProcessor.pyb.outputType = 'float'
            self.imageProcessor.update_settings()    
                                    
            # If we are processing a single file, we should make sure this
            # gets updated now that we have changed the processing options. If we
            # are doing live imaging, the next image will be processed with the new
            # options anyway
            self.update_file_processing()
            
            
    def handle_bundle_find(self):
        
        if self.currentImage is not None:
            loc = pybundle.find_bundle(pybundle.to8bit(self.currentImage))
            self.bundleCentreXInput.setValue(loc[0])
            self.bundleCentreYInput.setValue(loc[1])
            self.bundleRadiusInput.setValue(loc[2])
            
        else:
            QMessageBox.about(self, "Error", "There is no image to analyse.")
             
                             
    def handle_calibrate(self):
        
        
        
        if self.backgroundImage is not None and self.imageProcessor is not None:
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.imageProcessor.pyb.set_calib_image(self.backgroundImage)
            #self.imageProcessor.pyb.set_background(self.backgroundImage)
            #self.imageProcessor.pyb.set_normalise_image(self.backgroundImage)

            self.imageProcessor.pyb.calibrate()
            print(f"Found {np.shape(self.imageProcessor.pyb.calibration.coreX)} cores.")
            QApplication.restoreOverrideCursor()

        else:
            QMessageBox.about(self, "Error", "Image and background image required")  
        
        self.handle_changed_bundle_processing()
        
            
    def handle_save_calibration(self):
        with open('calib.dat','wb') as pickleFile:
            pickle.dump(self.imageProcessor.pyb.calibration, pickleFile)

        
    def handle_load_calibration(self):
        with open('calib.dat', 'rb') as pickleFile:
            self.imageProcessor.pyb.calibration = pickle.load(pickleFile)
        self.handle_changed_bundle_processing()
        
    def handle_reset_mosaic(self):
        self.imageProcessor.mosaic.reset()
        

    def handle_change_mosaic_options(self):
        if self.mosaicOnCheck.isChecked():

            #self.mosaicDisplayWidget.show()
            if self.imageProcessor is not None:
                self.imageProcessor.mosaicing = True

                if self.mosaicThresholdInput.value() > 0:
                    self.imageProcessor.mosaic.resetThresh = self.mosaicThresholdInput.value()
                else:
                    self.imageProcessor.mosaic.resetThresh = None
                 
                    
                if self.mosaicIntensityInput.value() > 0: 
                    self.imageProcessor.mosaic.resetIntensity = self.mosaicIntensityInput.value()
                else:
                    self.imageProcessor.mosaic.resetIntensity = None
                
                if self.mosaicCOVInput.value() > 0:
                    self.imageProcessor.mosaic.resetSharpness = self.mosaicCOVInput.value()
                else:
                    self.imageProcessor.mosaic.resetSharpness= None
                    
        else:
            if self.imageProcessor is not None:
                self.imageProcessor.mosaicing = False
        
    
    def handle_change_show_bundle_control(self, event):
        if self.showBundleControlCheck.isChecked():
            self.bundleProcessPanel.show()
            if self.mosaicingEnabled:
                self.mosaicControlPanel.show()
        else:  
            self.bundleProcessPanel.hide()
            if self.mosaicingEnabled:
                self.mosaicControlPanel.hide()


    
if __name__ == '__main__':
    
   app=QApplication(sys.argv)
   app.setStyle("Fusion")

   # Now use a palette to switch to dark colors:
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
   app.setPalette(palette)
   
   
   
   window=CAS_GUI_Bundle()
   window.show()
   sys.exit(app.exec_())

