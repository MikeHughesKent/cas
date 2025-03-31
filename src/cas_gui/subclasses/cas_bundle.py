# -*- coding: utf-8 -*-
"""
A graphical user interface for working with fibre bundle imaging.

Built on CAS-GUI.

"""

import sys 

# If PyFibreBundle is not on your path, add the path here:
sys.path.append(r'..\\..\\pyfibrebundle\\src')
#sys.path.append(r'..\\src')             # So that it find the cas_gui module that we are inside!
sys.path.append(r"..\\")   # So that it find the cas_gui module that we are inside!

import os
import time
import math
import pickle

import numpy as np
import matplotlib.pyplot as plt

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen

from PIL import Image

import cv2 as cv

sys.path.append(r'..\\..\\')  

from cas_gui.base import CAS_GUI

from threads.image_acquisition_thread import ImageAcquisitionThread
from widgets.image_display import ImageDisplay
from threads.bundle_processor import BundleProcessor

import pybundle

class CAS_GUI_Bundle(CAS_GUI):
    
    mosaicingEnabled = False
    multiCore = True
    processor = BundleProcessor
    
    authorName = "AOG"
    appName = "CAS-Bundle"
    
    camSource = 'SimulatedCamera'
    windowTitle = "Fibre Bundle Imaging"
    
    resPath = "..\\..\\..\\res"
    sourceFilename = r"..\..\..\tests\test_data\im1.tif"


    def __init__(self, parent=None):                      
        
        super(CAS_GUI_Bundle, self).__init__(parent)
        
        sourceFilename = r"..\..\..\tests\test_data\im1.tif"

        
        
        try:
            self.load_background()
        except:
            pass

        self.mosaic_options_changed()
        
        
        
    # Overloaded, call by superclass    
    def create_layout(self):
        
        super().create_layout()

        
        self.calibPanel = self.create_calib_panel()
        
        self.saveRawMenuButton = self.create_menu_button("Save Raw As", QIcon(os.path.join(self.resPath, 'icons', 'save_white.svg')), self.save_raw_as_button_clicked, position = 5)

        self.calibMenuButton = self.create_menu_button("Calibrate", QIcon(os.path.join(self.resPath, 'icons', 'grid_white.svg')), self.calib_menu_button_clicked, False, False, 3)

        
        # Create the mosaic display widget 
        if self.mosaicingEnabled:
            self.mosaicButton = self.create_menu_button(text = "Mosaicing", 
                                                         icon = QIcon('../res/icons/copy_white.svg'), 
                                                         handler = self.mosaic_button_clicked, 
                                                         hold = True, 
                                                         menuButton = True,
                                                         position = 8)
            
            
            self.mosaicDisplayFrame = QFrame()
            self.mosaicDisplayLayout = QVBoxLayout()
            self.mosaicDisplayLayout.setSpacing(0)
            self.mosaicDisplayLayout.setContentsMargins(0, 0, 0, 0)
            self.mosaicDisplayFrame.setLayout(self.mosaicDisplayLayout)
            
            self.mosaicPanel = self.create_mosaic_panel()
            
            self.mosaicDisplay, self.mosaicDisplayFrame =  self.create_image_display(name = "mosaicDisplay", statusBar = True, autoScale = True)       
            self.contentLayout.addWidget(self.mosaicDisplay)


        
    def mosaic_button_clicked(self):
        self.expanding_menu_clicked(self.mosaicButton, self.mosaicPanel)
        
        
    def start_acquire(self):
        super().start_acquire()
        
                
        
    
    def create_settings_panel(self):
        """ Create the control panel for fibre bundle processing"""
        
        bundlePanel, layout = self.panel_helper(title = "Processing Settings")
       
        self.bundleCoreMethodCombo = QComboBox(objectName = 'bundleCoreMethodCombo')
        self.bundleCoreMethodCombo.addItems(['Filtering', 'Interpolation'])
      
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
        
        self.bundleInterpFilterInput = QDoubleSpinBox(objectName = "bundleInterpFilter")
       
        layout.addWidget(self.bundleShowRaw)
        layout.addWidget(QLabel("Pre-processing Method:"))
        layout.addWidget(self.bundleCoreMethodCombo)

        
        # Panel with options for interpolation
        self.interpProcessPanel = QWidget()
        self.interpProcessPanel.setLayout(interpLayout:=QVBoxLayout())
        
        interpLayout.addWidget(QLabel("Image Pixels:"))
        interpLayout.addWidget(self.bundleGridSizeInput)
        interpLayout.addWidget(QLabel('Pre-Filter size:'))
        interpLayout.addWidget(self.bundleInterpFilterInput)
        interpLayout.setContentsMargins(0,0,0,0)       
        
        layout.addWidget(self.interpProcessPanel)
      
        # Panel with options for filtering
        self.filterProcessPanel = QWidget()
        self.filterProcessPanel.setLayout(fppLayout:=QVBoxLayout())
        fppLayout.addWidget(self.bundleFindBtn)  

        bcx = QHBoxLayout()
        bcx.addWidget(QLabel("Bundle X:"))
        bcx.addWidget(self.bundleCentreXInput)
        fppLayout.addLayout(bcx)

        bcy = QHBoxLayout()
        bcy.addWidget(QLabel("Bundle Y:"))
        bcy.addWidget(self.bundleCentreYInput)
        fppLayout.addLayout(bcy)

        bcr = QHBoxLayout()
        bcr.addWidget(QLabel("Bundle Rad:"))
        bcr.addWidget(self.bundleRadiusInput)
        fppLayout.addLayout(bcr)
        
        fppLayout.addWidget(QLabel('Filter size:'))
        fppLayout.addWidget(self.bundleFilterSizeInput)
        fppLayout.setContentsMargins(0,0,0,0)
        fppLayout.addWidget(self.bundleCropCheck)
        fppLayout.addWidget(self.bundleMaskCheck)
        
        layout.addWidget(self.filterProcessPanel)
        
        
        # These options are common to both processing methods
        layout.addWidget(self.bundleSubtractBackCheck)
        layout.addWidget(self.bundleNormaliseCheck)
        
        
        backHeader = QLabel("Background")
        backHeader.setProperty("subheader", "true")
        layout.addWidget(backHeader)
        
        self.backgroundStatusLabel = QLabel("")
        self.backgroundStatusLabel.setWordWrap(True)
        self.backgroundStatusLabel.setProperty("status", "true")
        self.backgroundStatusLabel.setTextFormat(Qt.RichText)
        layout.addWidget(self.backgroundStatusLabel)
        
        self.bundleLoadBackgroundBtn=QPushButton('Load Background')
        self.bundleLoadBackgroundFromBtn = QPushButton('Load Background From')
        self.bundleAcquireBackgroundBtn=QPushButton('Acquire Background')
        self.bundleSaveBackgroundBtn=QPushButton('Save Background')
        self.bundleSaveBackgroundAsBtn=QPushButton('Save Background As')
                
        layout.addWidget(self.bundleAcquireBackgroundBtn)
        layout.addWidget(self.bundleLoadBackgroundBtn)
        layout.addWidget(self.bundleLoadBackgroundFromBtn)
        layout.addWidget(self.bundleSaveBackgroundBtn)
        layout.addWidget(self.bundleSaveBackgroundAsBtn)
      
        bundleHeader = QLabel("Bundle Calibration")
        bundleHeader.setProperty("subheader", "true")
        layout.addWidget(bundleHeader)
        
        self.calibStatusLabel = QLabel("")
        self.calibStatusLabel.setWordWrap(True)
        self.calibStatusLabel.setProperty("status", "true")
        self.calibStatusLabel.setTextFormat(Qt.RichText)
        layout.addWidget(self.calibStatusLabel)
        
        self.bundleCalibBtn=QPushButton('Calibrate Bundle')
        layout.addWidget(self.bundleCalibBtn)
        
        self.bundleLoadCalibBtn=QPushButton('Load Calibration')
        self.bundleSaveCalibBtn=QPushButton('Save Calibration')
        layout.addWidget(self.bundleLoadCalibBtn)
        layout.addWidget(self.bundleSaveCalibBtn)
        
        layout.addStretch()
       
        self.bundleAcquireBackgroundBtn.clicked.connect(self.acquire_background_clicked)
        self.bundleLoadBackgroundBtn.clicked.connect(self.load_background_clicked)
        self.bundleLoadBackgroundFromBtn.clicked.connect(self.load_background_from_clicked)
        self.bundleSaveBackgroundBtn.clicked.connect(self.save_background_clicked)
        self.bundleSaveBackgroundAsBtn.clicked.connect(self.save_background_as_clicked)
        self.bundleLoadCalibBtn.clicked.connect(self.load_calibration_clicked)
        self.bundleSaveCalibBtn.clicked.connect(self.save_calibration_clicked)
        self.bundleCalibBtn.clicked.connect(self.calibrate_clicked)      
        
        
        
        layout.addStretch()
    
        self.bundleCoreMethodCombo.currentIndexChanged[int].connect(self.processing_options_changed)
        self.bundleInterpFilterInput.valueChanged[float].connect(self.processing_options_changed)
        self.bundleFilterSizeInput.valueChanged[float].connect(self.processing_options_changed)
        self.bundleCentreXInput.valueChanged[int].connect(self.processing_options_changed)
        self.bundleCentreYInput.valueChanged[int].connect(self.processing_options_changed)
        self.bundleRadiusInput.valueChanged[int].connect(self.processing_options_changed)
        self.bundleFindBtn.clicked.connect(self.bundle_find_clicked)
        self.bundleShowRaw.stateChanged.connect(self.processing_options_changed)
        self.bundleCropCheck.stateChanged.connect(self.processing_options_changed)
        self.bundleMaskCheck.stateChanged.connect(self.processing_options_changed)
        self.bundleSubtractBackCheck.stateChanged.connect(self.processing_options_changed)
        self.bundleNormaliseCheck.stateChanged.connect(self.processing_options_changed)
        self.bundleGridSizeInput.valueChanged[int].connect(self.processing_options_changed)
        
        
        return bundlePanel
    
    
    def create_calib_panel(self):
        """ Create the control panel for fibre bundle processing"""
        
        widget, layout = self.panel_helper(title = "Calibration")
        
        
        
        
        return widget


    def create_mosaic_panel(self):
        """ Creates the panel with mosaicing options"""
        
        widget, layout = self.panel_helper(title = "Mosaic Settings")

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
        
        layout.addStretch()

        self.resetMosaicBtn.clicked.connect(self.reset_mosaic_clicked)
        self.mosaicThresholdInput.valueChanged[float].connect(self.mosaic_options_changed)
        self.mosaicIntensityInput.valueChanged[float].connect(self.mosaic_options_changed)
        self.mosaicCOVInput.valueChanged[float].connect(self.mosaic_options_changed)
        self.mosaicOnCheck.stateChanged.connect(self.mosaic_options_changed)

        return widget
    
    
    
    def calib_menu_button_clicked(self):
        """ Handles press of 'Calibration' button.
        """
        if self.currentImage is not None:
            self.acquire_background()
            self.calibrate()
            self.bundle_find()
        else:
            QMessageBox.about(self, "Error", "Calibration requires an image.")    



    def update_image_display(self):
        """ Overrides from base class to include mosaicing window"""
        if self.bundleShowRaw.isChecked() is False and self.currentProcessedImage is not None:
           self.mainDisplay.set_image(self.currentProcessedImage)
        elif self.currentImage is not None:
           self.mainDisplay.set_image(self.currentImage)
        if self.imageProcessor is not None:
            if self.mosaicingEnabled and self.imageProcessor.get_processor().get_mosaic() is not None:
                self.mosaicDisplay.set_image(self.imageProcessor.get_processor().get_mosaic())       
                #print(self.imageProcessor.get_processor().get_mosaic())
        
    
    def processing_options_changed(self):
        """ Called when any of the widget values/states are changed"""
        
        # Show correct bundle processing options depending on method
        FILTER = 0
        INTERPOLATE = 1
        if self.bundleCoreMethodCombo.currentIndex() == FILTER:
            self.filterProcessPanel.show()
            self.interpProcessPanel.hide()

        elif self.bundleCoreMethodCombo.currentIndex() == INTERPOLATE:
            self.filterProcessPanel.hide()
            self.interpProcessPanel.show()
            
        if self.backgroundImage is not None:    
            self.backgroundStatusLabel.setText(self.backgroundSource)
        else:
            self.backgroundStatusLabel.setText("None")


        if self.imageProcessor is not None:
            if self.bundleCoreMethodCombo.currentIndex() == FILTER:
                self.calibStatusLabel.setText("")
            elif self.bundleCoreMethodCombo.currentIndex() == INTERPOLATE:
                if self.imageProcessor.get_processor().pyb.calibration is None:
                    self.calibStatusLabel.setText("None")
                else:
                    self.calibStatusLabel.setText(f"<b>Calibration:</b> <br> Found {self.imageProcessor.get_processor().pyb.calibration.nCores[0]} cores.")
        else:
            self.calibStatusLabel.setText(f"None")
            
                   
        if self.imageProcessor is not None:
    
            self.imageProcessor.get_processor().pyb.set_grid_size(self.bundleGridSizeInput.value())
            if self.bundleCoreMethodCombo.currentIndex() == 0:
                self.imageProcessor.get_processor().pyb.set_core_method(self.imageProcessor.get_processor().pyb.FILTER)
            elif self.bundleCoreMethodCombo.currentIndex() == 1:
                self.imageProcessor.get_processor().pyb.set_core_method(self.imageProcessor.get_processor().pyb.TRILIN)
                
            self.imageProcessor.get_processor().pyb.set_filter_size(self.bundleFilterSizeInput.value())
           # if self.bundleCropCheck.isChecked():
           #     self.imageProcessor.pyb.crop = self.bundleCentreXInput.value(), self.bundleCentreYInput.value(), self.bundleRadiusInput.value())
           # else:
           #     self.imageProcessor.pipe_message("crop", None)
                
            self.imageProcessor.get_processor().pyb.set_loc((self.bundleCentreXInput.value(), self.bundleCentreYInput.value(), self.bundleRadiusInput.value()))
           
            
            self.imageProcessor.get_processor().pyb.set_crop(self.bundleCropCheck.isChecked())
            self.imageProcessor.get_processor().pyb.set_auto_contrast(False)
            
            if self.bundleMaskCheck.isChecked():
                self.imageProcessor.get_processor().pyb.set_apply_mask(True) 
                self.imageProcessor.get_processor().pyb.set_auto_mask(True)
            else:
                self.imageProcessor.get_processor().pyb.set_apply_mask(False) 
                self.imageProcessor.get_processor().pyb.set_mask(None)

                
            if self.bundleSubtractBackCheck.isChecked():
                self.imageProcessor.get_processor().pyb.set_background(self.backgroundImage)
            else:
                self.imageProcessor.get_processor().pyb.set_background(None)

        
            if self.bundleNormaliseCheck.isChecked():
                self.imageProcessor.get_processor().pyb.set_normalise_image(self.backgroundImage)   
            else:
                self.imageProcessor.get_processor().pyb.set_normalise_image(None)

    
            self.imageProcessor.get_processor().pyb.set_output_type('float')
            
            if self.bundleCoreMethodCombo.currentIndex() == FILTER:
                self.imageProcessor.get_processor().pyb.set_filter_size(self.bundleFilterSizeInput.value())   
            elif self.bundleCoreMethodCombo.currentIndex() == INTERPOLATE:
                self.imageProcessor.get_processor().pyb.set_filter_size(self.bundleInterpFilterInput.value())  
            
            

            # This sends all the settings to the process running the processing
            self.imageProcessor.update_settings()    
                                    
            # If we are processing a single file, we should make sure this
            # gets updated now that we have changed the processing options. If we
            # are doing live imaging, the next image will be processed with the new
            # options anyway
            self.update_file_processing()
            
            
    def bundle_find_clicked(self):
        
        if self.currentImage is not None:
            loc = pybundle.find_bundle(pybundle.to8bit(self.currentImage))
            self.bundleCentreXInput.setValue(loc[0])
            self.bundleCentreYInput.setValue(loc[1])
            self.bundleRadiusInput.setValue(loc[2])
            
        else:
            QMessageBox.about(self, "Error", "There is no image to analyse.")
            
     
    def bundle_find(self):

        if self.currentImage is not None:
            loc = pybundle.find_bundle(pybundle.to8bit(self.currentImage))
            self.bundleCentreXInput.setValue(loc[0])
            self.bundleCentreYInput.setValue(loc[1])
            self.bundleRadiusInput.setValue(loc[2])
            if self.imageProcessor is not None:
                self.imageProcessor.update_settings()

            
             
        else:
            QMessageBox.about(self, "Error", "Cannot find bundle, there is no image to analyse.")    
            
                                     
    def calibrate_clicked(self):
        
        self.calibrate()
    
    
    
    def calibrate(self):   
        
        if self.backgroundImage is not None and self.imageProcessor is not None:
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.imageProcessor.get_processor().pyb.set_calib_image(self.backgroundImage)
            self.imageProcessor.get_processor().pyb.set_background(self.backgroundImage)
            self.imageProcessor.get_processor().pyb.set_normalise_image(self.backgroundImage)
            self.imageProcessor.get_processor().pyb.calibrate()
            self.imageProcessor.update_settings()
            QApplication.restoreOverrideCursor()

        else:
            QMessageBox.about(self, "Error", "Calibration requires both a current image and a background image.")  
        
        self.processing_options_changed()
        
        
            
    def save_calibration_clicked(self):
        self.save_calibration()
        
        
    def save_calibration(self):    
        self.imageProcessor.get_processor().pyb.save_calibration('calib.dat')


        
    def load_calibration_clicked(self):
        self.load_calibration()
        
    
    def load_calibration(self):
        self.imageProcessor.get_processor().pyb.load_calibration('calib.dat')
        self.processing_options_changed()
        
    
    def reset_mosaic_clicked(self):
        self.imageProcessor.get_processor().mosaic.reset()
        

    def mosaic_options_changed(self):
        
        if self.mosaicingEnabled:
            if self.mosaicOnCheck.isChecked():
                self.mosaicDisplay.show()
                #self.mosaicDisplayWidget.show()
                if self.imageProcessor is not None:
                    self.imageProcessor.get_processor().mosaicing = True
    
                    if self.mosaicThresholdInput.value() > 0:
                        self.imageProcessor.get_processor().mosaic.resetThresh = self.mosaicThresholdInput.value()
                    else:
                        self.imageProcessor.get_processor().mosaic.resetThresh = None
                     
                        
                    if self.mosaicIntensityInput.value() > 0: 
                        self.imageProcessor.get_processor().get_processor().get_processor().mosaic.resetIntensity = self.mosaicIntensityInput.value()
                    else:
                        self.imageProcessor.get_processor().mosaic.resetIntensity = None
                    
                    if self.mosaicCOVInput.value() > 0:
                        self.imageProcessor.get_processor().mosaic.resetSharpness = self.mosaicCOVInput.value()
                    else:
                        self.imageProcessor.get_processor().mosaic.resetSharpness= None
                        
            else:
                self.mosaicDisplay.hide()
    
                if self.imageProcessor is not None:
                    self.imageProcessor.get_processor().mosaicing = False
        wid = self.width()
        hei = self.height()
        self.resize(400,400)
        self.resize(2000,2000)
        self.resize(wid, hei)
        




    
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

