# -*- coding: utf-8 -*-
"""
Camera Control Widget for CAS_GUI

@author: Mike Hughes, Applied Optics Group, University of Kent
"""

from PyQt5 import QtGui, QtCore, QtWidgets  
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtXml import QDomDocument, QDomElement
from DoubleSlider import *


def init_cam_control_panel(self, controlPanelSize, calibrate_button = False):
     
    self.camSourceCombo = QComboBox(objectName = 'camSourceCombo')
    self.camSourceCombo.addItems(self.camNames)
    
    self.loadFileButton = QPushButton('Load File') 

    self.startBtn=QPushButton('Start Acquisition')
    self.endBtn=QPushButton('Stop Acquisition')

    self.saveImageAsBtn=QPushButton('Save Image As')
    self.saveRawAsBtn=QPushButton('Save Raw As')
    self.snapImageBtn=QPushButton('Snap Image')
    self.recordBtn=QPushButton('Start Recording')  

    #self.endBtn.setEnabled(False)

    self.loadFileButton.clicked.connect(self.load_file_click)
    self.startBtn.clicked.connect(self.start_acquire)
    self.endBtn.clicked.connect(self.end_acquire)
    self.saveImageAsBtn.clicked.connect(self.save_image_as_button_click)
    self.saveRawAsBtn.clicked.connect(self.save_raw_as_button_click)
    self.snapImageBtn.clicked.connect(self.snap_image_button_click)
    self.recordBtn.clicked.connect(self.record_click)
    
    self.exposureInput = QDoubleSpinBox(objectName = 'exposureInput')
    self.exposureInput.setMaximum(0)
    self.exposureInput.setMaximum(100) 
    self.exposureInput.valueChanged[float].connect(self.handle_exposure_slider)
    self.exposureInput.setKeyboardTracking(False)
  
    self.exposureSlider = DoubleSlider(QtCore.Qt.Horizontal, objectName = 'exposureSlider')
    self.exposureSlider.setTickPosition(QSlider.TicksBelow)
    self.exposureSlider.setTickInterval(10)
    self.exposureSlider.setMaximum(100)
    self.exposureSlider.doubleValueChanged[float].connect(self.exposureInput.setValue)
    
    self.gainSlider = QSlider(QtCore.Qt.Horizontal, objectName = 'gainSlider')
    self.gainSlider.setTickPosition(QSlider.TicksBelow)
    self.gainSlider.setTickInterval(10)
    self.gainSlider.setMaximum(100)
    self.gainSlider.valueChanged[int].connect(self.handle_gain_slider)
    
    self.gainInput = QSpinBox(objectName = 'gainInput')
    self.gainInput.setMaximum(0)
    self.gainInput.setMaximum(100)
    self.gainInput.valueChanged[int].connect(self.gainSlider.setValue)
    self.gainInput.setKeyboardTracking(False)
   
    self.frameRateInput = QDoubleSpinBox(objectName = 'frameRateInput')
    self.frameRateInput.setMaximum(0)
    self.frameRateInput.setMaximum(100)
    self.frameRateInput.valueChanged[float].connect(self.handle_frame_rate_slider)
    self.frameRateInput.setKeyboardTracking(False)

    self.frameRateSlider = DoubleSlider(QtCore.Qt.Horizontal, objectName = 'frameRateSlider')
    self.frameRateSlider.setTickPosition(QSlider.TicksBelow)
    self.frameRateSlider.setTickInterval(100)
    self.frameRateSlider.setMaximum(100)
    self.frameRateSlider.doubleValueChanged[float].connect(self.frameRateInput.setValue)
   
    self.bufferFillLabel = QLabel()
    self.frameRateLabel = QLabel()
    self.processRateLabel = QLabel()
    self.procBufferFillLabel = QLabel()

    camControlPanel = QWidget()
    camControlPanel.setLayout(topLayout:=QVBoxLayout())
    camControlPanel.setMaximumWidth(controlPanelSize)
    camControlPanel.setMinimumWidth(controlPanelSize)    
    
    self.mainMenu = QGroupBox("Main Menu")
    topLayout.addWidget(self.mainMenu)
    
    self.camControlGroupBox = QGroupBox("Camera Control")
    topLayout.addWidget(self.camControlGroupBox)
    self.camLayout=QVBoxLayout()
    self.camControlGroupBox.setLayout(self.camLayout)   
  
    self.camSourceCombo.currentIndexChanged.connect(self.handle_cam_source_change)
    
    # File input Sub-panel
    self.inputFilePanel = QWidget()
    inputFileLayout = QVBoxLayout()
    self.inputFilePanel.setLayout(inputFileLayout)
    #self.inputFilePanel.setMaximumWidth(controlPanelSize - 50)
    #self.inputFilePanel.setMinimumWidth(controlPanelSize - 50)
    inputFileLayout.setContentsMargins(0,0,0,0)
   
    inputFileLayout.addWidget(self.loadFileButton)

    self.mainMenuLayout = QVBoxLayout()
    self.mainMenu.setLayout(self.mainMenuLayout)
    self.mainMenuLayout.addLayout(self.mainMenuLayout)
    self.mainMenuLayout.addWidget(QLabel('Camera Source'))
    self.mainMenuLayout.addWidget(self.camSourceCombo)
    self.mainMenuLayout.addWidget(self.inputFilePanel)
    
    self.mainMenuLayout.addWidget(self.startBtn)
    self.mainMenuLayout.addWidget(self.endBtn)
    self.mainMenuLayout.addItem(verticalSpacer:= QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))

    self.mainMenuLayout.addWidget(self.saveImageAsBtn)
    self.mainMenuLayout.addWidget(self.saveRawAsBtn)
    self.mainMenuLayout.addWidget(self.snapImageBtn)
    self.mainMenuLayout.addWidget(self.recordBtn)
    
    self.camSettingsPanel = QWidget()
    self.camSettingsLayout = QVBoxLayout()
    self.camSettingsPanel.setLayout(self.camSettingsLayout)
    self.camSettingsPanel.setMaximumWidth(controlPanelSize - 50)
    self.camSettingsPanel.setMinimumWidth(controlPanelSize - 50)
    
    self.camSettingsLayout.addWidget(QLabel('Exposure:'))
    exposureLayout = QHBoxLayout()
    exposureLayout.addWidget(self.exposureSlider)
    exposureLayout.addWidget(self.exposureInput)
    self.exposureInput.setMinimumWidth(90)
    self.camSettingsLayout.addLayout(exposureLayout)
        

    self.camSettingsLayout.addWidget(QLabel('Gain:'))
    gainLayout = QHBoxLayout()
    gainLayout.addWidget(self.gainSlider)
    gainLayout.addWidget(self.gainInput)
    self.gainInput.setMinimumWidth(90)
    self.camSettingsLayout.addLayout(gainLayout)

    
    self.camSettingsLayout.addWidget(QLabel('Frame Rate:'))
    frameRateLayout = QHBoxLayout()
    frameRateLayout.addWidget(self.frameRateSlider)
    frameRateLayout.addWidget(self.frameRateInput)
    self.frameRateInput.setMinimumWidth(90)
    self.camSettingsLayout.addLayout(frameRateLayout)

    self.camSettingsLayout.setContentsMargins(0,0,0,0)

    self.camLayout.addWidget(self.camSettingsPanel)
    
    self.camStatusPanel = QWidget()
    self.camStatusPanel.setLayout(camStatusLayout:=QGridLayout())
    self.camStatusPanel.setMaximumWidth(controlPanelSize)
    self.camStatusPanel.setMinimumWidth(controlPanelSize)


    camStatusLayout.addWidget(QLabel('Acq. Buffer:'),1,0)
    camStatusLayout.addWidget(QLabel('Acquisition fps:'),3,0)
    camStatusLayout.addWidget(QLabel('Processing fps:'),4,0)

    
    camStatusLayout.addWidget(self.bufferFillLabel,1,1)
    camStatusLayout.addWidget(self.frameRateLabel,3,1)
    camStatusLayout.addWidget(self.processRateLabel,4,1)

    
    self.camLayout.addWidget(self.camStatusPanel)
    
    
    topLayout.addStretch()
    
    
      

    return camControlPanel