# -*- coding: utf-8 -*-
"""

@author: Mike Hughes
Applied Optics Group
University of Kent

"""


import sys 
import time
import numpy as np
import math
import warnings
warnings.filterwarnings("ignore")

sys.path.append(r"C:\Users\AOG\Dropbox\Programming\Python\PyHoloscope")

from PyQt5 import QtGui, QtCore, QtWidgets  
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtXml import QDomDocument, QDomElement
from DoubleSlider import *
from slider2 import *

from PIL import Image
import inspect

import cv2 as cv

from RawImageWidget import RawImageWidget

from ImageAcquisitionThread import ImageAcquisitionThread
from ImageDisplay import ImageDisplay
from BundleProcessor import BundleProcessor

import matplotlib.pyplot as plt

import pyqtgraph as pg

import logging

from pybundle import PyBundle
import PyHoloscope 
#logging.disable(logging.CRITICAL)

class inline_GUI(QMainWindow):
    
    def __init__(self,parent=None):        
                 
        self.pyb = PyBundle()
        self.holo = PyHoloscope.Holo(PyHoloscope.INLINE_MODE, 1, 1)
        self.imageDisplaySize = 300
        self.controlPanelSize = 220
        self.currentImage = None
        self.camOpen = False
      
        self.rawImage = None
        self.backgroundImage = None
        self.procImage = None
         
        super(inline_GUI, self).__init__(parent)
        
        
        self.setWindowTitle('Inline Holography System')        

        self.mainLayout = QHBoxLayout()
        
        self.rawDisplayFrame = QVBoxLayout()
        self.procDisplayFrame = QVBoxLayout()
        
        # Unprocessed image frame
        self.rawDisplay = ImageDisplay(name = 'RawDisp')
        self.rawDisplay.isStatusBar = True
        self.rawDisplay.autoScale = False
        self.rawDisplayFrame.addWidget(self.rawDisplay)
        
        # Processed image frame
        self.procDisplay = ImageDisplay(name = 'ProcDisp')
        self.procDisplay.isStatusBar = True
        self.procDisplay.autoScale = True      
        self.procDisplayFrame.addWidget(self.procDisplay)

        # Control panel frame
        self.controlPanel = self.init_control_panel(self.controlPanelSize)
        self.bundlePanel = self.init_bundle_process_panel(self.controlPanelSize)
        self.holoPanel = self.init_inline_holo_process_panel(self.controlPanelSize)

     
        #self.bundlePanel.hide()


        topleft = QFrame()
        textedit = QTextEdit()
        splitter1 = QSplitter()
        rawDisplayWidget = QWidget()
        rawDisplayWidget.setLayout(self.rawDisplayFrame)
        procDisplayWidget = QWidget()
        procDisplayWidget.setLayout(self.procDisplayFrame)
        splitter1.addWidget(rawDisplayWidget)
        splitter1.addWidget(procDisplayWidget)
        #self.mainLayout.addLayout(self.rawDisplayFrame)
       # self.mainLayout.addLayout(self.procDisplayFrame)
        self.mainLayout.addWidget(splitter1)
        self.mainLayout.addWidget(self.controlPanel)
        self.mainLayout.addWidget(self.bundlePanel)
        self.mainLayout.addWidget(self.holoPanel)
        
        
        
        widget = QWidget()
        widget.setLayout(self.mainLayout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)
  
        
        self.move(50,50) 
            
        #settingsFile = 'inline_bundle_offline.ini'
        self.settings = QtCore.QSettings("AOG", "Inline Holography Offline GUI")  
        self.guirestore()
        
        
    def mouseMoveEvent(self, event):
        pass
    
    
    
        
    # Create widgets for camera controls    
    def init_control_panel(self, controlPanelSize):
        
        self.loadImageBtn=QPushButton('Load Image')
        self.loadBackgroundBtn=QPushButton('Load Background')
        
        self.loadSequenceBtn=QPushButton('Load Sequence')
        self.saveImageBtn=QPushButton('Save Image')
        self.saveSequenceBtn=QPushButton('Save Sequence')  
        self.saveDepthStackBtn=QPushButton('Save Depth Stack') 

   
        self.loadImageBtn.clicked.connect(self.load_image_click)
        self.loadBackgroundBtn.clicked.connect(self.load_background_click)
        
        self.saveImageBtn.clicked.connect(self.save_image_click)
        
        self.bundleMode = QCheckBox('Fibre Bundle Mode', objectName='bundleMode')
        
        self.bundleMode.stateChanged.connect(self.bundle_check_change)
        #self.saveImageBtn.clicked.connect(self.save_button_click)
        
                      
        controlPanel = QWidget()
        controlPanel.setLayout(topLayout:=QVBoxLayout())
        controlPanel.setMaximumWidth(controlPanelSize)
        controlPanel.setMinimumWidth(controlPanelSize)
        
        topLayout.addWidget(self.loadImageBtn)
        topLayout.addWidget(self.loadBackgroundBtn)
        topLayout.addWidget(self.loadSequenceBtn)
        topLayout.addWidget(self.saveImageBtn)
        topLayout.addWidget(self.saveSequenceBtn)

        topLayout.addWidget(self.bundleMode) 

       
        topLayout.addStretch()

        return controlPanel
    
        
    
    
    def init_bundle_process_panel(self, panelSize):
        
        
        self.filterProcessPanel = QWidget()
        self.filterProcessPanel.setLayout(fppLayout:=QVBoxLayout())

        
        self.coreMethodCombo = QComboBox(objectName='coreMethodCombo')
        self.coreMethodCombo.addItems(['Filtering', 'Interpolation'])
        self.bundleCalibBtn=QPushButton('Calibrate')
        self.bundleLoadCalibBtn=QPushButton('Load Calibration')
        self.bundleSaveCalibBtn=QPushButton('Save Calibration')
        self.bundleShowRaw = QCheckBox('Show Raw', objectName='bundleShowRaw')
        
        self.bundleFilterSizeInput = QDoubleSpinBox(objectName='bundleFilterSizeInput')
        
        self.bundleCentreXInput = QSpinBox(objectName='bundleCentreXInput')
        self.bundleCentreXInput.setMaximum(10**6)
        self.bundleCentreXInput.setMinimum(-10**6)
        
        self.bundleCentreYInput = QSpinBox(objectName='bundleCentreYInput')
        self.bundleCentreYInput.setMaximum(10**6)
        self.bundleCentreYInput.setMinimum(-10**6)
        
        self.bundleRadiusInput = QSpinBox(objectName='bundleRadiusInput')
        self.bundleRadiusInput.setMaximum(10**6)
        self.bundleRadiusInput.setMinimum(-10**6)
        
        
        self.bundleFindBtn=QPushButton('Locate Bundle')

        
        self.bundleCropCheck = QCheckBox("Crop to bundle", objectName='bundleCropCheck')
        self.bundleMaskCheck = QCheckBox("Mask bundle", objectName='bundleMaskCheck')
        
        self.bundleAutoContrastCheck = QCheckBox("Auto contrast", objectName='bundleAutoContrastCheck')
        self.bundleUseBackgroundCheck = QCheckBox("Subtract Background", objectName='bundleUseBackgroundCheck')
        self.bundleNormaliseCheck = QCheckBox("Normalise", objectName='bundleNormaliseCheck')


        
        bundlePanel = QWidget()
        bundlePanel.setLayout(topLayout:=QVBoxLayout())
        bundlePanel.setMaximumWidth(panelSize)
        bundlePanel.setMinimumWidth(panelSize)
        
        groupBox = QGroupBox("Bundle Pre-processing")
        topLayout.addWidget(groupBox)
        groupBox.setLayout(layout:=QVBoxLayout())


        layout.addWidget(QLabel("Bundle Centre X:"))
        layout.addWidget(self.bundleCentreXInput)

        layout.addWidget(QLabel("Bundle Centre Y:"))
        layout.addWidget(self.bundleCentreYInput)

        layout.addWidget(QLabel("Bundle Radius:"))
        layout.addWidget(self.bundleRadiusInput)

        layout.addWidget(self.bundleFindBtn)
        
        
        layout.addWidget(QLabel("Pre-processing Method"))
        layout.addWidget(self.coreMethodCombo)
        layout.addWidget(self.bundleCalibBtn)
        layout.addWidget(self.bundleLoadCalibBtn)
        layout.addWidget(self.bundleSaveCalibBtn)
        layout.addWidget(self.bundleShowRaw)

      
        #self.filterProcessPanel.setStyleSheet("padding: 0px; margin: 0px")
        #self.bundleFilterSizeInput.setStyleSheet("margin: 0px; padding:0px#")
        fppLayout.addWidget(QLabel('Filter size:'))
        fppLayout.addWidget(self.bundleFilterSizeInput)
        fppLayout.addWidget(self.bundleUseBackgroundCheck)
        
        
        fppLayout.addWidget(self.bundleCropCheck)
        fppLayout.addWidget(self.bundleMaskCheck)
        fppLayout.addWidget(self.bundleAutoContrastCheck)
        fppLayout.addWidget(self.bundleUseBackgroundCheck)
        fppLayout.addWidget(self.bundleNormaliseCheck)

        
        layout.addWidget(self.filterProcessPanel)
        topLayout.addStretch()
    
        self.coreMethodCombo.currentIndexChanged[int].connect(self.update_processing)
        self.bundleFilterSizeInput.valueChanged[float].connect(self.update_processing)
        self.bundleCentreXInput.valueChanged[int].connect(self.update_processing)
        self.bundleCentreYInput.valueChanged[int].connect(self.update_processing)
        self.bundleRadiusInput.valueChanged[int].connect(self.update_processing)
        self.bundleRadiusInput.valueChanged[int].connect(self.update_processing)
        self.bundleFindBtn.clicked.connect(self.locate_bundle_click)
        self.bundleCropCheck.stateChanged.connect(self.update_processing)
        self.bundleMaskCheck.stateChanged.connect(self.update_processing)
        self.bundleUseBackgroundCheck.stateChanged.connect(self.update_processing)
        self.bundleNormaliseCheck.stateChanged.connect(self.update_processing)
        self.bundleAutoContrastCheck.stateChanged.connect(self.update_processing)
        self.bundleCalibBtn.clicked.connect(self.calibrate_click)
        
        #self.handle_changed_bundle_processing()
        
        return bundlePanel
    
    




    def init_inline_holo_process_panel(self, panelSize):
        
        
        self.holoWavelengthInput = QDoubleSpinBox(objectName='holoWavelengthInput')
        self.holoWavelengthInput.setMaximum(10**6)
        self.holoWavelengthInput.setMinimum(-10**6)
        
        self.holoPixelSizeInput = QDoubleSpinBox(objectName='holoPixelSizeInput')
        self.holoPixelSizeInput.setMaximum(10**6)
        self.holoPixelSizeInput.setMinimum(-10**6)
        
        self.holoDepthInput = QDoubleSpinBox(objectName='holoDepthInput')
        self.holoDepthInput.setMaximum(10**6)
        self.holoDepthInput.setMinimum(-10**6)
        
        self.holoRefocusCheck = QCheckBox("Refocus", objectName='holoRefocusCheck')
        self.holoWindowCombo = QComboBox(objectName='holoWindowCombo')
        self.holoWindowCombo.addItems(['None', 'Circular', 'Rectangular'])

        self.holoWindowThicknessInput = QDoubleSpinBox(objectName='holoWindowThicknessInput')
        self.holoWindowThicknessInput.setMaximum(10**6)
        self.holoWindowThicknessInput.setMinimum(-10**6)
        
        holoPanel = QWidget()
        holoPanel.setLayout(topLayout:=QVBoxLayout())
        holoPanel.setMaximumWidth(panelSize)
        holoPanel.setMinimumWidth(panelSize)
        
        topLayout.addWidget(QLabel('Wavelegnth (microns):'))
        topLayout.addWidget(self.holoWavelengthInput)
        topLayout.addWidget(QLabel('Pixel Size (microns):'))
        topLayout.addWidget(self.holoPixelSizeInput)
        topLayout.addWidget(QLabel('Refocus distance (microns):'))
        topLayout.addWidget(self.holoDepthInput)
        
        topLayout.addWidget(self.holoRefocusCheck)
         
        topLayout.addWidget(QLabel('Window:'))
        topLayout.addWidget(self.holoWindowCombo)

        topLayout.addWidget(QLabel("Window Thickness (px):"))
        topLayout.addWidget(self.holoWindowThicknessInput)                    


        topLayout.addStretch()
        
        self.holoWavelengthInput.valueChanged[float].connect(self.update_processing)
        self.holoPixelSizeInput.valueChanged[float].connect(self.update_processing)
        self.holoDepthInput.valueChanged[float].connect(self.update_processing)
        self.holoRefocusCheck.stateChanged.connect(self.update_processing)
        self.holoWindowThicknessInput.valueChanged[float].connect(self.update_processing)
        self.holoWindowCombo.currentIndexChanged[int].connect(self.update_processing)

        
        return holoPanel
           
        
                  
    def update_processing(self):
        
        #  update bundle processing from GUI
        if self.coreMethodCombo.currentIndex() == 0:
            self.pyb.set_core_method(self.pyb.FILTER)
        elif self.coreMethodCombo.currentIndex() == 1:
            self.pyb.set_core_method(self.pyb.TRILIN)
        self.pyb.set_bundle_loc((self.bundleCentreXInput.value(), self.bundleCentreYInput.value(), self.bundleRadiusInput.value()))
        self.pyb.set_auto_contrast(True)
        self.pyb.set_output_type('uint8')
        self.pyb.set_crop(self.bundleCropCheck.isChecked())
        self.pyb.set_auto_contrast(False)
        if self.bundleMaskCheck.isChecked() and self.rawImage is not None:
            self.pyb.set_auto_mask(self.rawImage)
        else:
            self.pyb.set_mask(None)
            
        if self.bundleUseBackgroundCheck.isChecked():
            self.pyb.set_background(self.backgroundImage)
        else:
            self.pyb.set_background(None)
        if self.bundleNormaliseCheck.isChecked():
            self.pyb.set_normalise_image(self.backgroundImage)    
        else:
            self.pyb.set_normalise_image(None)

        self.pyb.set_filter_size(self.bundleFilterSizeInput.value())    
        self.pyb.outputType = 'float'
        # update holography processing from GUI
        if self.holoRefocusCheck.isChecked():
           
            
            if self.holoWavelengthInput.value() != self.holo.wavelength:
                self.holo.set_wavelength(self.holoWavelengthInput.value())
            if self.holoPixelSizeInput.value() != self.holo.pixelSize:
                self.holo.set_pixel_size(self.holoPixelSizeInput.value())
            if self.holoDepthInput.value() != self.holo.depth:
                self.holo.set_depth(self.holoDepthInput.value())
            if self.holoWindowCombo.currentText() == "Circular":
                self.holo.window = 1
                self.holo.set_window_radius(None)
                self.holo.set_window_thickness(self.holoWindowThicknessInput.value())
            else:
                self.holo.window = None
        
        self.procImage = self.process_image(self.rawImage)
        self.update_image_display()


    def process_image(self, img):
        
        if self.rawImage is not None:        
            if self.bundleMode.isChecked():
                preProcImage = self.pyb.process(img)
            else:
                preProcImage = self.rawImage
        else:
            return None
        
        if preProcImage is not None:
            if self.holoRefocusCheck.isChecked(): 
                procImage = self.holo.process(preProcImage)
                if procImage is not None:
                    procImage = np.abs(procImage).astype('uint8')
            else:
                procImage = preProcImage
        else:
            return None
        
        
        
        
        
        return procImage
 
    def update_image_display(self):
        self.rawDisplay.set_mono_image(self.rawImage)
        self.procDisplay.set_mono_image(self.procImage)

 
    def calibrate_click(self):

        if self.backgroundImage is not None:
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.pyb.set_calib_image(self.backgroundImage)
            self.pyb.calibrate()
            QApplication.restoreOverrideCursor()

        else:
            QMessageBox.about(self, "Error", "Background image required")  
            

    def bundle_check_change(self):
        if self.bundleMode.isChecked():
            self.bundlePanel.show()
        else:
            self.bundlePanel.hide()
        self.update_processing()    
        self.update_image_display() 
        
   
    def locate_bundle_click(self):
        if self.backgroundImage is not None:
            loc = PyBundle.find_bundle(PyBundle.to8bit(self.backgroundImage))
            self.bundleCentreXInput.setValue(loc[0])
            self.bundleCentreYInput.setValue(loc[1])
            self.bundleRadiusInput.setValue(loc[2])
        elif self.rawImage is not None:
            loc = PyBundle.find_bundle(PyBundle.to8bit(self.rawImage))
            self.bundleCentreXInput.setValue(loc[0])
            self.bundleCentreYInput.setValue(loc[1])
            self.bundleRadiusInput.setValue(loc[2]) 
        else:
            QMessageBox.about(self, "Error", "There is no image to analyse.")  
            
            
            
    
    def load_image_click(self): 
        filename = QFileDialog.getOpenFileName(filter  = '*.tif')
        if len(filename[0]) > 0:
            try:
                im = self.load_image(filename[0])
                self.rawImage = im.astype('float')
            except:
                QMessageBox.information(self, 'Inline holography GUI', 'Cannot load file, check that it is a valid image.')
        self.update_processing()
        self.update_image_display()   
        
        
        
                
    def load_background_click(self): 
        filename = QFileDialog.getOpenFileName(filter  = '*.tif')
        if len(filename[0]) > 0:
            try:
                im = self.load_image(filename[0])
                self.backgroundImage = im   
            except:
                QMessageBox.information(self, 'Inline holography GUI', 'Cannot load file, check that it is a valid image.')
         
        self.update_processing()    
        self.update_image_display()    
        
        
        
            
    def save_image_click(self): 
        filename = QFileDialog.getSaveFileName(filter  = '*.tif; *.png')
        if len(filename[0]) > 0:
            #try:
            self.save_image(self.procImage, filename[0])
            #except:
            #    QMessageBox.information(self, 'Inline holography GUI', 'Cannot save to file, check that it is a valid filename.')
  
    
        
    def save_image(self, img, filename):
        im = Image.fromarray(img)
        im.save(filename)
            
     
    def load_image(self, filename):  
        im = Image.open(filename)
        return self.pil2np(im)
        
 


   
            
    
    def pil2np(self,im):
        return np.array(im.getdata()).reshape(im.size[1], im.size[0])
        

    def closeEvent(self, event):
        self.guisave()
        event.accept()

    def guisave(self):

      # Save geometry
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())
    
        for name, obj in inspect.getmembers(self):
          # if type(obj) is QComboBox:  # this works similar to isinstance, but missed some field... not sure why?
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

    def guirestore(self):

      # Restore geometry  
      #self.resize(self.settings.value('size', QtCore.QSize(500, 500)))
      #self.move(self.settings.value('pos', QtCore.QPoint(60, 60)))
    
      for name, obj in inspect.getmembers(self):
          if isinstance(obj, QComboBox):
              index = obj.currentIndex()  # get current region from combobox
              # text   = obj.itemText(index)   # get the text for new selected index
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

def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

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
   
   
   
   window=inline_GUI()
   window.show()
   sys.exit(app.exec_())

