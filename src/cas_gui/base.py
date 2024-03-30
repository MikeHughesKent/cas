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
from threading import Lock
from pathlib import Path
import time
from datetime import datetime
import math
import multiprocessing as mp

import numpy as np
import matplotlib.pyplot as plt

from PyQt5 import QtGui, QtCore, QtWidgets   
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtXml import QDomDocument, QDomElement

from PIL import Image, TiffImagePlugin

import cv2 as cv


# Add a path to ourselves in case this module is run
sys.path.append(r'..\\')  

from cas_gui.widgets.double_slider import DoubleSlider
from cas_gui.threads.image_acquisition_thread import ImageAcquisitionThread
from cas_gui.widgets.image_display import ImageDisplay
from cas_gui.threads.image_processor_thread import ImageProcessorThread
import cas_gui.res.resources
from cas_gui.cameras.FileInterface import FileInterface

cuda = True                 # Set to False to disable use of GPU
multicore = False           # Set to True to run processor on a different core

class CAS_GUI(QMainWindow):

    FILE_TYPE = 0
    REAL_TYPE = 1
    SIM_TYPE = 2
    
    windowTitle = "Kent Camera Acquisition System"

    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "CAS"

    # Locations for icons etc. 
    resPath = "..\\..\\res"
    logoFilename = None
    iconFilename = 'logo_256_red.png'
        
    # Define available cameras interface and their display names in the drop-down menu
    camNames = ['File', 'Simulated Camera', 'Flea Camera', 'Kiralux', 'Thorlabs DCX', 'Webcam', 'Colour Webcam']
    camSources = ['ProcessorInterface', 'SimulatedCamera', 'FleaCameraInterface', 'KiraluxCamera', 'DCXCameraInterface', 'WebCamera', 'WebCameraColour']
    camTypes = [FILE_TYPE, SIM_TYPE, REAL_TYPE, REAL_TYPE, REAL_TYPE, REAL_TYPE, REAL_TYPE]
     
    # Default source for simulated camera
    sourceFilename = None
    
    # The size of the queue for raw images from the camera. If this is exceeded
    # then the oldest image will be removed.
    rawImageBufferSize = 10
    
    # GUI display defaults
    imageDisplaySize = 300
    menuPanelSize = 300
    optionsPanelSize = 300
    
    # Timer interval defualts (ms)
    GUIupdateInterval = 100
    imagesUpdateInterval = 10
    
    processor = None
      
    # Defaults
    isPaused = False
    currentImage = None
    camOpen = False
    backgroundImage = None
    imageProcessor = None
    currentProcessedImage = None
    manualImageTransfer = True
    recording = False
    videoOut = None
    numFramesRecorded  = 0
    imageThread = None
    imageProcessor = None
    cam = None
    rawImage = None
    fallBackToRaw = True
    multiCore = False
    sharedMemory = False
    sharedMemoryArraySize = (1024,1024)
    settings = {}  
    panelsList = []
    menuButtonsList = []
    defaultBackgroundFile = "background.tif"
    backgroundSource = ""
    recordBuffer = []

    TIF = 0
    AVI = 1    
   
    def __init__(self, parent=None):   
        """ Initial setup of GUI.
        """
        
        super(CAS_GUI, self).__init__(parent)
        
        self.defaultIcon = os.path.join(self.resPath, self.iconFilename)
        self.recordFolder = Path.cwd().as_posix()
        
        # Create the GUI. This is generally over-ridden in sub-classes
        self.create_layout()        
        
        self.set_colour_scheme()
        
        file = os.path.join(self.resPath, 'cas_modern.css')
        with open(file,"r") as fh:
            self.setStyleSheet(fh.read())
        self.set_colour_scheme()            
        
        # Creates timers for GUI and camera acquisition
        self.create_timers()         
        self.acquisitionLock = Lock()

        # In case software is being used for first time, we can implement some
        # useful defaults (for example in a sub-class)
        self.apply_default_settings()      
    
        # Load last values for GUI from registry
        self.settings = QtCore.QSettings(self.authorName, self.appName)  
        self.gui_restore()
            
        # Put the window in a sensible position
        self.resize(1200,800)
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())        
                
        # Make sure the display is correct for whatever camera source 
        # we initiallylly have selected
        self.cam_source_changed()
        self.show()
        self.recordFolderLabel.setText(self.recordFolder)


        
        
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
        self.create_standard_layout(title = self.windowTitle, iconFilename = self.defaultIcon)


        # Create Main Menu Area
        self.menuPanel = QWidget(objectName="menu_panel")
        self.menuPanel.setMinimumSize(self.menuPanelSize, 400)
        self.menuPanel.setMaximumWidth(self.menuPanelSize)
        self.menuLayout = QVBoxLayout()
        self.menuPanel.setLayout(self.menuLayout)
        self.layout.addWidget(self.menuPanel)
        
        
        # Add Main Menu Buttons
        self.liveButton = self.create_menu_button("Live Imaging", QIcon(os.path.join(self.resPath, 'icons', 'play_white.svg')), self.live_button_clicked, True)
        self.sourceButton = self.create_menu_button("Image Source", QIcon(os.path.join(self.resPath, 'icons', 'camera_white.svg')), self.source_button_clicked, True, menuButton = True)
        self.saveAsButton = self.create_menu_button("Save Image As", QIcon(os.path.join(self.resPath, 'icons', 'save_white.svg')), self.save_as_button_clicked, False)
        self.snapButton = self.create_menu_button("Snap Image", QIcon(os.path.join(self.resPath, 'icons', 'download_white.svg')), self.snap_button_clicked, False )
        self.recordButton = self.create_menu_button("Record", QIcon(os.path.join(self.resPath, 'icons', 'film_white.svg')), self.record_button_clicked, False, menuButton = True)
        self.settingsButton = self.create_menu_button("Settings", QIcon(os.path.join(self.resPath, 'icons', 'settings_white.svg')), self.settings_button_clicked, True, menuButton = True)
        self.menuLayout.addStretch()
        self.exitButton = self.create_menu_button("Exit", QIcon(os.path.join(self.resPath, 'icons', 'exit_white.svg')), self.exit_button_clicked, False)


        # Create Expanding Menu Area
        self.optionsScrollArea = QScrollArea()
        self.optionsScrollArea.setContentsMargins(0, 0, 0, 0)
        self.optionsScrollArea.setWidgetResizable(True)
        self.optionsScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.optionsPanel = QWidget(objectName = "options_panel")
        self.optionsPanelLayout = QVBoxLayout()
        self.optionsPanel.setContentsMargins(0, 0, 0, 0)
        self.optionsPanelLayout.setContentsMargins(0, 0, 0, 0)

        self.optionsPanel.setLayout(self.optionsPanelLayout)        
        self.optionsPanelLayout.addWidget(self.optionsScrollArea)
        self.optionsPanel.setContentsMargins(0,0,0,0)
        self.optionsPanel.setMinimumWidth(self.optionsPanelSize)
        self.optionsPanel.setMaximumWidth(self.optionsPanelSize)
        
        self.multiMenu = QWidget()
        self.multiMenu.setContentsMargins(0,0,0,0)
        self.menus = QVBoxLayout()
        self.multiMenu.setLayout(self.menus)
        
        self.optionsScrollArea.setWidget(self.multiMenu)
        self.optionsPanel.setVisible(False)
        
        
        # Create Menu Panels
        self.settingsPanel = self.create_settings_panel()
        self.sourcePanel = self.create_source_panel()
        self.recordPanel = self.create_record_panel()              


        # Image Control Area
        self.contentPanel = QWidget()
        self.contentLayout = QHBoxLayout()
        self.contentPanel.setLayout(self.contentLayout)
        self.contentPanel.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        #self.contentPanel.setStyleSheet("QWidget{padding:20px;margin:20px;background-color:rgba(40,40,40,255);}")
       
        self.mainDisplay, self.mainDisplayFrame = self.create_image_display()    

        self.contentVertical = QWidget()
        self.contentVertical.setContentsMargins(0, 0, 0, 0)
        self.contentVerticalLayout = QVBoxLayout()    
        self.contentVertical.setLayout(self.contentVerticalLayout)

        self.contentVerticalLayout.addWidget(self.mainDisplay)
        self.contentLayout.addWidget(self.contentVertical)        
                
        self.layout.addWidget(self.optionsPanel)
        self.layout.addWidget(self.contentPanel)
        
        # Logo
        # if self.logoFilename is not None:
        #    self.create_logo_bar()
        
        
    def create_menu_button(self, text = "", icon = None, handler = None, hold = False, menuButton = False, position = None):
        """ Creates a main menu button.
        
        Keyword Arguments:
            text       : str
                         button text (default is no text)
            icon       : QIcon
                         icon to place on button (defualt is no icon)
            handler    : function
                         function to call when button is clicked (defualt is no handler)
            hold       : boolean
                         if True, button is checkable, i.e. can toggle on and off. 
                         (defualt is False)
            menuButton : boolean
                         if true, will be registered so that button will be unchecked                         
                         when another menu is opened
            position   : int
                         is specified, button will be inserted at this position from top             
        Returns:
            QButton    : reference to button 
        """    
        
        button = QPushButton(" " + text)
        if icon is not None: button.setIcon(icon)
        if handler is not None: button.clicked.connect(handler)
        button.setCheckable(hold)

        if position is None:
            self.menuLayout.addWidget(button)
        else:
            self.menuLayout.insertWidget(position, button)
        
        if menuButton:
            self.menuButtonsList.append(button)
        
        return button
    
    
    def create_standard_layout(self, title = "Kent Camera Acquisition System", iconFilename = None):
        """ Sets window title and icon, and creates main widget
        Keyword Arguments:
            title        : str
                           main window title, default is "Kent Camera Acquisition System"
            iconFilename : str      
                           path to application icon 
        """        
        
        self.setWindowTitle(title) 
        
        self.main_widget = QWidget()
        self.layout = QHBoxLayout()
        self.main_widget.setLayout(self.layout)
        
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.setCentralWidget(self.main_widget)
        
        if iconFilename is not None:
            self.setWindowIcon(QtGui.QIcon(iconFilename))
        
        return 

    def create_record_panel(self):
        """ Creates expanding panel for recording. 
        """
        
        panel, self.recordLayout = self.panel_helper(title = "Record")
        
         
        self.recordRawCheck = QCheckBox("Record Raw", objectName = 'recordRawCheck')
        self.recordLayout.addWidget(self.recordRawCheck)
        
        self.recordTifCheck = QCheckBox("Record Tif", objectName = 'recordTifCheck')
        self.recordLayout.addWidget(self.recordTifCheck)
        
        self.recordBufferCheck = QCheckBox("Buffered", objectName = 'recordBufferwCheck')
        self.recordLayout.addWidget(self.recordBufferCheck)
        
        self.recordBufferSpin = QSpinBox(objectName = "recordBufferSize")
        self.recordLayout.addWidget(QLabel("Buffer Size:"))
        self.recordLayout.addWidget(self.recordBufferSpin)
        self.recordBufferSpin.setMaximum(1000)
        
        self.recordLayout.addItem(QSpacerItem(60, 60, QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.recordFolderButton = QPushButton("Choose Folder")
        self.recordFolderButton.clicked.connect(self.record_folder_clicked)
        self.recordLayout.addWidget(self.recordFolderButton) 
       
        self.recordFolderLabel = QLabel()
        self.recordFolderLabel.setWordWrap(True)
        self.recordFolderLabel.setProperty("status", "true")
        self.recordFolderLabel.setTextFormat(Qt.RichText)
        self.recordLayout.addWidget(self.recordFolderLabel)
        self.recordLayout.addItem(QSpacerItem(60, 60, QSizePolicy.Minimum, QSizePolicy.Minimum))

        self.toggleRecordButton = QPushButton("Start Recording")
        self.toggleRecordButton.clicked.connect(self.toggle_record_button_clicked)
        self.recordLayout.addWidget(self.toggleRecordButton)
        
        self.recordStatusLabel = QLabel()
        self.recordStatusLabel.setWordWrap(True)
        self.recordStatusLabel.setProperty("status", "true")
        self.recordStatusLabel.setTextFormat(Qt.RichText)
        self.recordLayout.addWidget(self.recordStatusLabel)
        
        self.recordLayout.addStretch()        
        
        return panel


    def panel_helper(self, title = None):
        """ Helper to start off creation of a new expanding menu panel.
        
        Keyword arguments:
            title     : str
                        Header to go at top of panel
                        
        Returns:
            tuple of widget, layout. Add child widgets to the layout.
        """
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        if title is not None:
            titleLabel = QLabel(title)
            titleLabel.setProperty("header", "true")
            layout.addWidget(titleLabel)
            
        self.menus.addWidget(panel)
        self.panelsList.append(panel)    
            
        return panel, layout    
        
        
    def create_settings_panel(self):
        """ Creates expanding panel for settings. Override to create a 
        custom settings panel. The function must return a QWidget which
        contains all widgets in the panel.
        """
        
        panel, self.settingsLayout = self.panel_helper(title = "Settings")
        
        self.add_settings(self.settingsLayout)
                
        self.settingsLayout.addStretch()        
        
        return panel
    
    
    def create_record_panel(self):
        """ Creates expanding panel for recording. 
        """
        
        panel, self.recordLayout = self.panel_helper(title = "Record")
        
         
        self.recordRawCheck = QCheckBox("Record Raw")
        self.recordLayout.addWidget(self.recordRawCheck)
        
        self.recordTifCheck = QCheckBox("Record Tif")
        self.recordLayout.addWidget(self.recordTifCheck)
        
        self.recordBufferCheck = QCheckBox("Buffered")
        self.recordLayout.addWidget(self.recordBufferCheck)
        
        self.recordBufferSpin = QSpinBox(objectName = "Record Buffer Size")
        self.recordLayout.addWidget(QLabel("Buffer Size:"))
        self.recordLayout.addWidget(self.recordBufferSpin)
        self.recordBufferSpin.setMaximum(1000)
        
        self.recordLayout.addItem(QSpacerItem(60, 60, QSizePolicy.Minimum, QSizePolicy.Minimum))

                
        
        self.recordFolderButton = QPushButton("Choose Folder")
        self.recordFolderButton.clicked.connect(self.record_folder_clicked)
        self.recordLayout.addWidget(self.recordFolderButton) 
        
       
        self.recordFolderLabel = QLabel()
        self.recordFolderLabel.setWordWrap(True)
        self.recordFolderLabel.setProperty("status", "true")
        self.recordFolderLabel.setTextFormat(Qt.RichText)
        self.recordLayout.addWidget(self.recordFolderLabel)
        
        self.recordLayout.addItem(QSpacerItem(60, 60, QSizePolicy.Minimum, QSizePolicy.Minimum))

        
        self.toggleRecordButton = QPushButton("Start Recording")
        self.toggleRecordButton.clicked.connect(self.toggle_record_button_clicked)
        self.recordLayout.addWidget(self.toggleRecordButton)
        
        self.recordStatusLabel = QLabel()
        self.recordStatusLabel.setWordWrap(True)
        self.recordStatusLabel.setProperty("status", "true")
        self.recordStatusLabel.setTextFormat(Qt.RichText)
        self.recordLayout.addWidget(self.recordStatusLabel)
        
        self.recordLayout.addStretch()        
        
        return panel
    
    
    
    def add_settings(self, settingsLayout):
        """ Adds options to the settings panels. Override this function in 
        a sub-class to add custom options.
        """
        
        text = "This is a place holder. Applications derived from CAS-GUI can put their specific settings here."
        self.settingsPlaceholder = QLabel(text)
        self.settingsPlaceholder.setWordWrap(True)
        self.settingsPlaceholder.setMaximumWidth(200)
        settingsLayout.addWidget(self.settingsPlaceholder)
    
    
    def create_source_panel(self):
        """ Creates expanding panel for camera source.
        """
        
        # Initialise a panel
        widget, self.sourceLayout = self.panel_helper(title = "Image Source")
                
        # Source Selection           
        self.camSourceCombo = QComboBox(objectName = 'camSourceCombo')
        self.camSourceCombo.addItems(self.camNames)
        self.sourceLayout.addWidget(QLabel('Camera Source'))
        self.sourceLayout.addWidget(self.camSourceCombo)
        self.camSourceCombo.currentIndexChanged.connect(self.cam_source_changed)

        # Camera Settings Panel 
        self.camSettingsPanel = QWidget()
        self.camSettingsLayout = QVBoxLayout()
        self.camSettingsPanel.setLayout(self.camSettingsLayout)
        self.exposureInput = QDoubleSpinBox(objectName = 'exposureInput')
        self.exposureInput.setMaximum(0)
        self.exposureInput.setMaximum(100) 
        self.exposureInput.valueChanged[float].connect(self.exposure_slider_changed)
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
        self.frameRateInput.valueChanged[float].connect(self.frame_rate_slider_changed)
        self.frameRateInput.setKeyboardTracking(False)

        self.frameRateSlider = DoubleSlider(QtCore.Qt.Horizontal, objectName = 'frameRateSlider')
        self.frameRateSlider.setTickPosition(QSlider.TicksBelow)
        self.frameRateSlider.setTickInterval(100)
        self.frameRateSlider.setMaximum(100)
        self.frameRateSlider.doubleValueChanged[float].connect(self.frameRateInput.setValue)
                
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
        self.sourceLayout.addWidget(self.camSettingsPanel)
         
        # File input Sub-panel
        self.inputFilePanel = QWidget()
        inputFileLayout = QVBoxLayout()

        self.inputFilePanel.setLayout(inputFileLayout)
        inputFileLayout.setContentsMargins(0,0,0,0)
        
        self.filename_label = QLabel()
        self.filename_label.setWordWrap(True)
        self.filename_label.setProperty("status", "true")
        inputFileLayout.addWidget(self.filename_label)
        
        self.loadFileButton = QPushButton('Load File') 
        self.loadFileButton.clicked.connect(self.load_file_clicked)

        inputFileLayout.addWidget(self.loadFileButton)
        
        self.fileIdxWidget = QWidget()
        self.fileIdxWidgetLayout = QVBoxLayout()
        self.fileIdxWidgetLayout.addWidget(QLabel("Frame No.:"))
        self.fileIdxWidget.setLayout(self.fileIdxWidgetLayout)
        self.fileIdxWidget.setContentsMargins(0,0,0,0)
        
        self.fileIdxControl = QWidget()
        self.fileIdxControl.setContentsMargins(0,0,0,0)
        self.fileIdxControlLayout = QHBoxLayout()
        self.fileIdxControl.setLayout(self.fileIdxControlLayout)
        self.fileIdxWidgetLayout.addWidget(self.fileIdxControl)
        self.fileIdxSlider = QSlider(QtCore.Qt.Horizontal)
        self.fileIdxSlider.valueChanged[int].connect(self.file_index_slilder_changed)
        self.fileIdxControlLayout.addWidget(self.fileIdxSlider)
        self.fileIdxInput = QSpinBox()
        
        self.fileIdxControlLayout.addWidget(self.fileIdxInput)
        self.fileIdxControlLayout.addWidget(self.fileIdxControl)
        
        self.fileIdxInput.valueChanged[int].connect(self.file_index_changed)
        
        inputFileLayout.addWidget(self.fileIdxWidget)        
        self.fileIdxWidget.hide()
                
        self.sourceLayout.addWidget(self.inputFilePanel)


        # Camera Status
        self.bufferFillLabel = QLabel()
        self.frameRateLabel = QLabel()
        self.processRateLabel = QLabel()
        self.camStatusPanel = QWidget()
        self.camStatusPanel.setLayout(camStatusLayout:=QGridLayout())
           
        camStatusLayout.addWidget(self.bufferFillLabel,1,1)
        camStatusLayout.addWidget(self.frameRateLabel,3,1)
        camStatusLayout.addWidget(self.processRateLabel,4,1)
      
        camStatusLayout.addWidget(QLabel('Acq. Buffer:'),1,0)
        camStatusLayout.addWidget(QLabel('Acquisition fps:'),3,0)
        camStatusLayout.addWidget(QLabel('Processing fps:'),4,0)
        
        self.camSettingsLayout.addWidget(self.camStatusPanel)        
    
        # Add stretch at bottom
        self.sourceLayout.addStretch()
        
        return widget
   
    
    def expanding_menu_clicked(self, button, menu):
        """ Handles the press of a menu button which toggles the visibility 
        of a menu.
        
        Arguments:
            button  : QPushButton
                      Reference to the button
            menu    : QWidget
                      Reference to the menu
                      
                      
        Returns:
            True if menu has been opened, False if it has been closed.              
        """              
                      
        if not menu.isVisible():
           self.hide_all_control_panels()
           self.optionsPanel.setVisible(True)
           menu.setVisible(True)
           button.setChecked(True)
           return True
        else:
           self.hide_all_control_panels()
           button.setChecked(False) 
           return False
           
           

    def hide_all_control_panels(self): 
        """ Utility function to close all sub-menus.
        """
        self.optionsPanel.setVisible(False)

        for button in self.menuButtonsList:
            button.setChecked(False)

        for panel in self.panelsList:
            panel.setVisible(False)
         

    
    def create_image_display(self, name = "Image Display", statusBar = True, autoScale = True):
        """ Adds an image display to the standard layout. 
        
        Keyword Arguments:
            name : str
                   Object name of ImageDisplayQT widget, default is "Image Display"
            statusBar : Boolean
                        If True (default), image display has status bar
            autoScale : Boolean 
                        If True (default), image values will be autoscaled.
                        
        Returns:
            tuple of reference to image  display widget and reference to 
            container widget in which this sits. These references should be 
            kept in scope.
        """
        
        # Create an instance of an ImageDisplay with the required properties
        display = ImageDisplay(name = name)
        display.isStatusBar = statusBar
        display.autoScale = autoScale
        
        
        # Create an outer widget to put the display frame in
        displayFrame = QWidget()
        displayFrame.setLayout(layout:=QHBoxLayout())
        layout.addWidget(display)

        frameOuter = QWidget()
        frameOuterLayout = QVBoxLayout()
        frameOuter.setLayout(frameOuterLayout)
        frameOuterLayout.addWidget(displayFrame)

        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
       
        displayFrame.setSizePolicy(policy)
        
        return display, frameOuter
       
     
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
        self.fileIdxSlider.valueChanged[int].connect(self.file_index_slilder_changed)
        self.fileIdxWidgetLayout.addWidget(QLabel("Frame No.:"))
        self.fileIdxWidgetLayout.addWidget(self.fileIdxSlider)
        self.sourceLayout.addWidget(self.fileIdxWidget)        
        self.fileIdxInput = QSpinBox()
        self.fileIdxWidgetLayout.addWidget(self.fileIdxInput)
        self.fileIdxInput.valueChanged[int].connect(self.file_index_changed)
        
     
    
    def create_processors(self):
        """ If a processor has been defined, create an ImageProcessor thread
        and pass the details of the processor.
        """
        
        if self.processor is not None:
        
            # If manualImageTransfer is off We will use the queue that the image 
            # acquisition thread has created to act as the input queue, this 
            # avoids the need for any copying of images. However, we will then
            # no longer have access to the raw images since we can't pull them off
            # the queue without competing with the image processor, so for 
            # example we can't make a proper raw recording.
            if self.imageThread is not None and self.manualImageTransfer is False:
                inputQueue = self.imageThread.get_image_queue()
            else:
                inputQueue = None
           
            # Create the processor
            self.imageProcessor = ImageProcessorThread(self.processor, 10, 10, inputQueue = inputQueue, 
                                                       multicore = self.multiCore, 
                                                       sharedMemory = self.sharedMemory,
                                                       sharedMemoryArraySize = self.sharedMemoryArraySize)
            
            # Update the processor based on initial values of widgets
            self.processing_options_changed()
        
            # Start the thread
            if self.imageProcessor is not None:
                self.imageProcessor.start()
                                
    
        
    def processing_options_changed(self):
        """Subclasses should overload this to handle processing changes"""
               
        pass
    

    def set_colour_scheme(self):
        """ Sets the colour scheme for the GUI.
        """
        
        QtWidgets.QApplication.setStyle("Fusion")
        palette = QtWidgets.QApplication.palette()
        palette.setColor(QPalette.Base, QColor(255, 255, 255))      
        palette.setColor(QPalette.Window, QColor(60, 60, 90))
        palette.setColor(QPalette.WindowText, Qt.white)
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
                    self.currentImage = rawImage
                    
                    if rawImage is not None:
                        self.imageProcessor.add_image(rawImage)
                        gotRawImage = True


            # If there is a new processed image, pull it off the queue
            if self.imageProcessor.is_image_ready() is True:
                gotProcessedImage = True
                self.currentProcessedImage = self.imageProcessor.get_next_image()
        
        # We don't have a processor, so will be raw only:
        elif self.imageThread is not None:
            
            self.currentProcessedImage = None 

            if self.imageThread.is_image_ready():
                rawImage  = self.imageThread.get_latest_image()
        
        else:
            
            self.currentProcessedImage = None 

             
        if self.recording and self.videoOut is not None:
            
            if self.recordRaw is False and self.currentProcessedImage is not None and gotProcessedImage:
                imToSave = self.currentProcessedImage
            elif self.currentImage is not None and gotRawImage:  
                imToSave = self.currentImage
            else:
                imToSave = None 
            
            if imToSave is not None:
                if self.recordBuffered:
                    self.numFramesBuffered = self.numFramesBuffered + 1
                    if self.numFramesBuffered <= self.recordBufferSize:
                        self.recordBuffer.append(imToSave)
                        self.recordStatusLabel.setText(f"Buffered {self.numFramesBuffered} frames of {self.recordBufferSize}.")
                    else:
                        self.record_buffer_full()
                else:                                  
                    self.numFramesRecorded = self.numFramesRecorded + 1
                    if self.recordType == self.AVI:
                        outImg = self.im_to_vid_frame(imToSave)
                        self.videoOut.write(outImg)
                    if self.recordType == self.TIF:
                        im = Image.fromarray(imToSave)
                        im.save(self.videoOut)
                        self.videoOut.newFrame()

                    
                    self.recordStatusLabel.setText(f"Recorded {self.numFramesRecorded} frames.")


    def update_image_display(self):
       """ Displays the current raw image. 
       Sub-classes should overload this if additional display boxes used.
       """
       if self.currentProcessedImage is not None:           
           self.mainDisplay.set_image(self.currentProcessedImage) 

       elif self.currentImage is not None and self.fallBackToRaw:
           self.mainDisplay.set_image(self.currentImage)           
       
        
    def update_camera_status(self):
       """ Updates real-time camera frame rate display. If the source
       panel has not been created this will cause an error, in which case this 
       function must be overridden.
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
        to update the GUI with correct ranges and the current values.
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
        """ Write the currently selected frame rate, exposure and gain to the camera
        """
        if self.camOpen:             
            self.cam.set_frame_rate(self.frameRateInput.value())
            self.cam.set_gain(self.gainSlider.value())
            self.cam.set_exposure(self.exposureSlider.value())
    
        
    def update_GUI(self):
        """ Update the image(s) and the status displays
        """
        self.update_camera_status()
        self.update_image_display()
       # if self.recording is True:
       #     self.recordBtn.setText('Stop Recording')
       # else:
       #     self.recordBtn.setText('Start Recording')
        
    
    def start_acquire(self):       
        """ Begin acquiring images by creating an image acquiistion thread 
        and starting it. The image acquisition thread grabs images to a queue
        which can then be retrieved by the GUI for processing/display
        """
        # Take the camera source selected in the GUI
        self.camSource = self.camSources[self.camSourceCombo.currentIndex()]
        self.camType = self.camTypes[self.camSourceCombo.currentIndex()]

        if self.camType == self.SIM_TYPE:
            
            # If we are using a simulated camera, ask for a file if not hard-coded
            if self.sourceFilename is None:
                filename = QFileDialog.getOpenFileName(filter  = '*.tif')[0]
                if filename != "":
                    self.sourceFilename = filename

            if self.sourceFilename is not None:

                self.imageThread = ImageAcquisitionThread(self.camSource, self.rawImageBufferSize, self.acquisitionLock, filename=self.sourceFilename)                                                  
                self.cam = self.imageThread.get_camera()
                self.cam.pre_load(-1)
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.imageThread = ImageAcquisitionThread(self.camSource, self.rawImageBufferSize, self.acquisitionLock)
            QApplication.restoreOverrideCursor()
            


        # Sub-classes can overload create_processor to create processing threads
        if self.imageThread is not None:
            
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
                self.liveButton.setChecked(True)
            else:
                self.liveButton.setChecked(False)

    def pause_acquire(self):
        if self.camOpen:
            self.isPaused = True
            self.liveButton.setChecked(False)
            if self.imageThread is not None:
                self.imageThread.pause()
            if self.imageProcessor is not None:
                self.imageProcessor.pause()


    def resume_acquire(self):
        if self.camOpen:
            self.isPaused = False
            if self.imageThread is not None:
                self.liveButton.setChecked(True)
                self.imageThread.resume()
            if self.imageProcessor is not None:
                self.imageProcessor.resume()
        
        

    def end_acquire(self):  
        """ Stops the image acquisition by stopping the image acquirer thread
        """
        if self.camOpen == True:
            self.GUITimer.stop()
            self.imageTimer.stop()
            self.imageThread.stop()
            self.camOpen = False
            self.liveButton.setChecked(False)
            if self.cam is not None:
                self.cam.close_camera()
       # self.currentImage = np.zeros((10,10))
       
        self.filename_label.setText("")
    
    
    def snap(self):    
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
            

    def save_as(self):
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
            self.save_raw_as()

    def save_raw_as(self):
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
                if self.cam.get_number_images() > 1:
                    self.fileIdxInput.setMaximum(self.cam.get_number_images() - 1)
                    self.fileIdxSlider.setMaximum(self.cam.get_number_images() - 1)
                    self.fileIdxWidget.show()
                else:    
                    self.fileIdxWidget.hide()
                self.filename_label.setText(filename)

            else:
                QMessageBox.about(self, "Error", "Could not load file.") 
        

    def file_index_changed(self, event):
        """ Handles change in the spinbox which controls which image in a 
        multi-page tif is shown.
        """
        
        if self.cam is not None:
            self.cam.set_image_idx(self.fileIdxInput.value())
            self.update_file_processing()
        self.fileIdxSlider.setValue(self.fileIdxInput.value())
        
        
        
    def file_index_slilder_changed(self, event): 
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
        if self.camTypes[self.camSourceCombo.currentIndex()] == self.FILE_TYPE:
            try:
                self.currentImage = self.cam.get_image()
            except:
                pass
            if self.imageProcessor is not None and self.currentImage is not None:
                self.currentProcessedImage = self.imageProcessor.process_frame(self.currentImage)
            self.update_image_display()
            self.update_GUI()

    
    def exposure_slider_changed(self):
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
          
             
    def frame_rate_slider_changed(self):
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

    def load_file_clicked(self):
        self.load_file()     

    def load_background_clicked(self, event):
        self.load_background()        
        
    def load_background_from_clicked(self, event):
        self.load_background_from() 
                
    def save_background_clicked(self,event):
        self.save_background()
        
    def save_background_as_clicked(self,event):
        self.save_background_as()
        
    def acquire_background_clicked(self,event):
        self.acquire_background()
        
        
    def live_button_clicked(self):
        """ Handles press of 'Live Imaging' button.
        """
        if not self.camOpen:
            self.start_acquire()
            
        elif self.camOpen and self.isPaused:
            self.resume_acquire() 
            
        elif self.camOpen and not self.isPaused:
            self.pause_acquire()       
        

    def settings_button_clicked(self):
        """ Handles press of 'Settings' button.
        """
        self.expanding_menu_clicked(self.settingsButton, self.settingsPanel)
        
        
    def source_button_clicked(self):
        """ Handles press of 'Source' button.
        """
        self.expanding_menu_clicked(self.sourceButton, self.sourcePanel)
  

    def exit_button_clicked(self):
        """ Handles press of 'Exit' button.
        """
        self.close()     
    
    
    def save_as_button_clicked(self, event):
        self.save_as()

    
    def save_raw_as_button_clicked(self, event):
        self.save_raw_as()


    def snap_button_clicked(self, event):
        self.snap()

     

    def record_button_clicked(self):
        """ Handles click of record button.
        """
     
        self.expanding_menu_clicked(self.recordButton, self.recordPanel)

    
    def toggle_record_button_clicked(self):
        
        if self.recording is False:
            self.start_recording()
        else:
            if self.recordBuffered:
                self.record_buffer_full()

        self.update_GUI()    
    
    
    def record_folder_clicked(self):
         """ Requests folder to save recordings to
         """
         try:
             folder = QFileDialog.getExistingDirectory(self, 'Select filename to save to:')
         except:
             folder = None
         if folder is not None and folder != "":
             self.recordFolder = folder
             self.recordFolderLabel.setText(self.recordFolder)
         else:
             QMessageBox.about(self, "Error", "Invalid folder.")  

    def save_image_ac(self, img, fileName):
        """ Utility function to save 16 bit image 'img' to file 'fileName' with autoscaling """   
        if fileName:
            img = img.astype('float')
            img = img - np.min(img)
            img = (img / np.max(img) * 2**16).astype('uint16')
            im = Image.fromarray(img)
            im.save(fileName)
        
            
    def save_image(self, img, fileName):
        """ Utility function to save image 'img' to file 'fileName' with no scaling"""
        if fileName:            
            im = Image.fromarray(img)
            im.save(fileName)         
            
    
    def pil2np(self, im):
        """ Utility to convert PIL image 'im' to numpy array"""
        return np.asarray(im)        
    
    
    def load_background(self):
        """ Loads the default background file"""
        backIm = Image.open(self.defaultBackgroundFile)
        if backIm is not None:
             self.backgroundImage = self.pil2np(backIm)
             self.backgroundSource = self.defaultBackgroundFile
             

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
                self.backgroundSource = filename

                self.processing_options_changed()
        

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
            self.backgroundSource = f"Captured at {datetime.now()}."
            self.processing_options_changed()
        else:
            QMessageBox.about(self, "Error", "There is no current image to use as the background.")  


    def start_recording(self):
        
        if self.recordTifCheck.isChecked():
            self.recordType = self.TIF
        else:
            self.recordType = self.AVI
        
        now = datetime.now()
        if self.recordType == self.TIF:
            self.recordFilename = (self.recordFolder / Path(now.strftime('record_Y_%m_%d_%H_%M_%S.tif'))).as_posix()
        else:
            self.recordFilename = (self.recordFolder / Path(now.strftime('record_Y_%m_%d_%H_%M_%S.avi'))).as_posix()

        
        self.recordBuffered = self.recordBufferCheck.isChecked()
        self.recordBufferSize = self.recordBufferSpin.value()
        
        self.numFramesRecorded = 0
        self.numFramesBuffered = 0
        
        if self.recordRawCheck.isChecked() or self.imageProcessor is None:
            self.recordRaw = True
            recordImage = self.currentImage
        else:
            self.recordRaw = False
            recordImage = self.currentProcessedImage
            
        if recordImage is None:
            QMessageBox.about(self, "Error", f"There is no image to record.")
            return


        if self.recordType == self.TIF:
            self.videoOut = TiffImagePlugin.AppendingTiffWriter(self.recordFilename)
            success = True
        else:    
            success = self.create_video_file(recordImage)

        if success:
            self.recording = True
            self.toggleRecordButton.setText("Stop Recording")
            self.recordRawCheck.setEnabled(False)
            self.recordFolderButton.setEnabled(False)
        else:
            self.recording = False
            self.toggleRecordButton.setText("Start Recording")
            self.recordRawCheck.setEnabled(True)
            self.recordFolderButton.setEnabled(True)
            QMessageBox.about(self, "Error", f"Unable to create video file.")
            
            

    def create_video_file(self, exampleImage):
        
        try:
            fourcc = cv.VideoWriter_fourcc(*"MJPG")
            imSize = (np.shape(exampleImage)[1],np.shape(exampleImage)[0]) 
            self.numFramesRecorded = 0
            self.videoOut = cv.VideoWriter(self.recordFilename, fourcc, 20.0, imSize)
            
            return True

        except:
            return False
       
    
    def record_buffer_full(self):
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        self.recording = False

        for idx, imToSave in enumerate(self.recordBuffer):
          
            if imToSave is not None:
                self.numFramesRecorded = self.numFramesRecorded + 1
                
                if self.recordType == self.AVI:
                    outImg = self.im_to_vid_frame(imToSave)
                    self.videoOut.write(outImg)
                elif self.recordType == self.TIF:
                    im = Image.fromarray(imToSave)
                    im.save(self.videoOut)
                    self.videoOut.newFrame()
              
            self.recordStatusLabel.setText(f"Saved {idx + 1} frames.")
        self.recordBuffer = []
        self.numFramesBuffered = 0
        self.stop_recording()
        QApplication.restoreOverrideCursor()

        
        
    def stop_recording(self):
        if self.recordType == self.AVI and self.videoOut is not None:
            self.videoOut.release()
        self.videoOut = None
        self.recording = False
        self.toggleRecordButton.setText("Start Recording")
        self.recordRawCheck.setEnabled(True)
        self.recordFolderButton.setEnabled(True)


    def im_to_vid_frame(self, imToSave):
        
        if imToSave.ndim  == 3:
            return imToSave
        else:
            outImg = np.zeros((np.shape(imToSave)[0], np.shape(imToSave)[1], 3), dtype = 'uint8')
            outImg[:,:,0] = imToSave
            outImg[:,:,1] = imToSave
            outImg[:,:,2] = imToSave
            return outImg
        
    
    def cam_source_changed(self):
        """ Deals with user changing camera source option, including adjusting
        visibility of relevant widgets
        """
        self.end_acquire()
        if self.camSourceCombo.currentText() == 'File':
            self.end_acquire()

            # Hide camera controls, show file widgets          
            self.inputFilePanel.show()
            self.camSettingsPanel.hide()
            self.liveButton.hide()
            self.camStatusPanel.hide()
            self.inputFilePanel.show()

        else:
           
            # Show camera controls, hide file widgets
            self.camSettingsPanel.show()
            self.liveButton.show()
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

