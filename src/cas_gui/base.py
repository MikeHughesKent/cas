# -*- coding: utf-8 -*-
"""
CAS GUI Base

CAS GUI is a graphical user interface built around the 
Camera Acquisition System (CAS).

By itself, this class allows camera images or files to be viewed in real time. 

It is intended as a base class to be extended by more complete programs that
provide further functionality.

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
from PyQt5.QtGui import QTextOption, QIcon, QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtXml import QDomDocument, QDomElement

from PIL import Image, TiffImagePlugin

import cv2 as cv

# Add a path one level up to allow imports from the main CAS package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cas_gui.widgets.double_slider import DoubleSlider
from cas_gui.threads.image_acquisition_thread import ImageAcquisitionThread
from cas_gui.widgets.image_display import ImageDisplay
from cas_gui.threads.image_processor_thread import ImageProcessorThread
import cas_gui.res.resources
from cas_gui.cameras.FileInterface import FileInterface
from cas_gui.utils.im_tools import to8bit, to16bit
from cas_gui.widgets.label_checkbox_widget import LabelCheckboxWidget    
from cas_gui.widgets.range_spin_box import RangeSpinBox


class CAS_GUI(QMainWindow):

    FILE_TYPE = 0
    REAL_TYPE = 1
    SIM_TYPE = 2
    TIF = 0
    AVI = 1    
   
    # Window Appearance
    windowTitle = "Camera Acquisition System"
    windowSize = (1200,800)
    windowMinHeight = 800

    # The values for the fields are stored in the registry using these IDs:
    authorName = "AOG"
    appName = "CAS"

    # Locations for icons etc. 
    resPath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'res'))
    logoFilename = None
    iconFilename = 'logo_256_red.png'
    studyRoot = "studies"
    studyPath = "studies/default"
    studyName = "default"
            

    # Other Options
    restoreGUI = True         # True to load widget values from registry
    fallBackToRaw = True      # True to display raw images if no processed images
    multiCore = False         # True to run processing on a different core
    sharedMemory = False      # True to use shared memory to transfer processed image when using multiCore
    showInfoBar = True        # True to show bar at bottom of screen
    defaultBackgroundFile = "background.tif"
    sharedMemoryArraySize = (2048,2048)

    # Default source for simulated camera
    sourceFilename = os.path.abspath(os.path.join(os.path.dirname(__file__), 'example_data/vid_example.tif'))

    # The size of the queue for raw images from the camera. If this is exceeded
    # then the oldest image will be removed.
    rawImageBufferSize = 10
    
    # GUI display defaults
    imageDisplaySize = 300
    menuPanelSize = 300
    optionsPanelSize = 300
    
    # Timer interval defualts (ms)
    GUIupdateInterval = 50
    imagesUpdateInterval = 10
    
    # Defaults
    processor = None
    isPaused = False
    currentImage = None
    camOpen = False
    backgroundImage = None
    imageProcessor = None
    currentProcessedImage = None
    settings = {}  
    panelsList = []
    menuButtonsList = []
    recording = False
    videoOut = None
    numFramesRecorded  = 0
    imageThread = None
    imageProcessor = None
    cam = None
    rawImage = None
    buffering = False
    backgroundSource = ""
    recordBuffer = []
    imageId = 0
    camFile = f"../res/cameras.csv"
    
    def __init__(self, parent = None):   
        """ Initial setup of GUI.
        """
        
        super(CAS_GUI, self).__init__(parent)
        
        self.defaultIcon = os.path.join(self.resPath, self.iconFilename)

        self.recordFolder = os.path.join(Path.cwd().as_posix(), self.studyPath)

        self.load_camera_names()
        
        # Create the GUI. 
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
        if self.restoreGUI:
            self.gui_restore()
            
        # Put the window in a sensible position
        self.resize(*self.windowSize)
        self.setMinimumHeight(self.windowMinHeight)
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())        
                
        # Make sure the display is correct for whatever camera source 
        # we initially have selected
        self.cam_source_changed()
        self.recordFolderLabel.setText(self.recordFolder)
        
        self.inputQueue = mp.Queue(maxsize=self.rawImageBufferSize)
        self.create_processors()
        self.show()
        self.update_GUI()        
        
        if not os.path.exists(self.studyRoot):
            try:
                os.makedirs(self.studyRoot)
            except:
                QMessageBox.about(self, "Error", f"Save folder {self.studyRoot} does not exist and cannot be created.")   
            
        
    def apply_default_settings(self):
        """ Overload this function in sub-class to provide defaults"""
        self.frameRateInput.setValue(30)
        self.camSourceCombo.setCurrentIndex(1)
    
    
    def load_camera_names(self):
        """ Load in CamNames, CamSources and CamTypes from a file. This allows the user 
        to add new cameras without changing the code. The file should be a CSV 
        file with the following format:
            
            Camera Name, Camera Source, Camera Type

        The Camera Name is the name that will appear in the drop-down menu
        The Camera Source is the name of the class that implements the camera interface
        The Camera Type is 0 for file, 1 for real camera and 2 for simulated camera
        """
        
        self.camNames = []
        self.camSources = []
        self.camTypes = []

        if not os.path.exists(self.camFile):
            self.camFile = os.path.join(self.resPath, 'cameras.csv')
        if os.path.exists(self.camFile):
            with open(self.camFile, 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    self.camNames.append(str.strip(parts[0]))
                    self.camSources.append(str.strip(parts[1]))
                    self.camTypes.append(int(parts[2]))

        # Otherwise use the defaults:
        if len(self.camNames) == 0:
            camNames = ['File', 'Simulated Camera', 'Webcam', 'Colour Webcam']
            camSources = ['ProcessorInterface', 'SimulatedCamera', 'WebCamera', 'WebCameraColour']
            camTypes = [self.FILE_TYPE, self.SIM_TYPE, self.REAL_TYPE, self.REAL_TYPE]



    def create_timers(self):
        """ Creates timers used for image acquisition and GUI updates"""

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
        self.studyMenuButton = self.create_menu_button("New Study", QIcon(os.path.join(self.resPath, 'icons', 'study_white.svg')), self.study_menu_clicked, False, False, position = 0)
        self.liveButton = self.create_menu_button("Live Imaging", QIcon(os.path.join(self.resPath, 'icons', 'play_white.svg')), self.live_button_clicked, True)
        self.sourceButton = self.create_menu_button("Image Source", QIcon(os.path.join(self.resPath, 'icons', 'camera_white.svg')), self.source_button_clicked, True, menuButton = True)
        self.snapButton = self.create_menu_button("Snap Image", QIcon(os.path.join(self.resPath, 'icons', 'download_white.svg')), self.snap_button_clicked, False )
        self.saveAsButton = self.create_menu_button("Save Image As", QIcon(os.path.join(self.resPath, 'icons', 'save_white.svg')), self.save_as_button_clicked, False)
        self.recordButton = self.create_menu_button("Record", QIcon(os.path.join(self.resPath, 'icons', 'film_white.svg')), self.record_button_clicked, True, menuButton = True)
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
       
        self.mainDisplay, self.mainDisplayFrame = self.create_image_display()    

        self.contentVertical = QWidget()
        self.contentVertical.setContentsMargins(0, 0, 0, 0)
        self.contentVerticalLayout = QVBoxLayout()    
        self.contentVertical.setLayout(self.contentVerticalLayout)

        self.contentVerticalLayout.addWidget(self.mainDisplay)
        self.contentLayout.addWidget(self.contentVertical)        
                
        self.layout.addWidget(self.optionsPanel)
        self.layout.addWidget(self.contentPanel)
        
        self.infoBar = QLabel()
        self.infoBar.setStyleSheet("font-size: 15px;")       
        self.infoBar.setMaximumHeight(30)
        self.contentVerticalLayout.insertWidget(2, self.infoBar)
        self.infoBar.setText("Initialising ...")
        self.infoBar.setVisible(self.showInfoBar)
        
        
    def create_menu_button(self, text = "", icon = None, handler = None, 
                           hold = False, menuButton = False, position = None):
        """ Creates a button and adds it to the main menu.
        
        Optional Keyword Arguments:
            text       : str
                         button text (default is no text)
            icon       : QIcon
                         icon to place on button (default is no icon)
            handler    : function
                         function to call when button is clicked (defualt is no handler)
            hold       : boolean
                         if True, button is checkable, i.e. can toggle on and off
                         (defualt is False)
            menuButton : boolean
                         if true, will be registered so that button will be unchecked                         
                         when another menu is opened
            position   : int
                         if specified, button will be inserted at this position from top             
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
    
    
    def create_standard_layout(self, title = "Camera Acquisition System", 
                               iconFilename = None):
        """ Sets window title and icon, and creates main widget.
        
        Optional Keyword Arguments:
            title        : str
                           main window title, default is "Camera Acquisition System"
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

   

    def panel_helper(self, title = None):
        """ Helper to start off creation of a new expanding menu panel.
        
        Optional Keyword Arguments:
            title     : str
                        Text of header to go at top of panel
                        
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
        custom settings panel, or use add_settings to add items to the
        default panel. The function must return a QWidget which
        contains all widgets in the panel.
        """
        
        panel, self.settingsLayout = self.panel_helper(title = "Settings")
        
        self.add_settings(self.settingsLayout)
                
        self.settingsLayout.addStretch()        
        
        return panel
    
    
    def create_record_panel(self):
        """ Creates expanding panel for use with recording options. 
        """
        
        panel, self.recordLayout = self.panel_helper(title = "Record")
         
        self.recordRawCheck = QCheckBox("Record Raw", objectName = "RecordRaw")
        self.recordLayout.addWidget(self.recordRawCheck)
        self.recordRawCheck.stateChanged.connect(self.record_options_changed)
        
        self.recordTifCheck = QCheckBox("Record Tif", objectName = "RecordTif")
        self.recordLayout.addWidget(self.recordTifCheck)
        
        self.recordBufferCheck = QCheckBox("Buffered", objectName = "RecordBuffered")
        self.recordLayout.addWidget(self.recordBufferCheck)
        self.recordBufferCheck.stateChanged.connect(self.record_options_changed)
        
        self.recordBufferSpin = QSpinBox(objectName = "Record Buffer Size")
        self.recordBufferSizeLabel = QLabel("Buffer Size:")
        self.recordLayout.addWidget( self.recordBufferSizeLabel)
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

        Arguments:
            settingsLayout : QVBoxLayout
                             Layout to which the widgets should be added.
        """
        
        text = "This is a place holder. Applications derived from CAS-GUI can put their specific settings here."
        self.settingsPlaceholder = QLabel(text)
        self.settingsPlaceholder.setWordWrap(True)
        self.settingsPlaceholder.setMaximumWidth(200)
        settingsLayout.addWidget(self.settingsPlaceholder)
    
    
    def create_source_panel(self):
        """ Creates expanding panel for camera source options.
        """        
        # Initialise a panel
        widget, self.sourceLayout = self.panel_helper(title = "Image Source")
                
        # Source Selection           
        self.camSourceCombo = QComboBox(objectName = 'camSourceCombo')
        self.camSourceCombo.addItems(self.camNames)
        self.sourceLayout.addWidget(QLabel('Camera Source'))
        self.sourceLayout.addWidget(self.camSourceCombo)
        self.camSourceCombo.currentIndexChanged.connect(self.cam_source_changed)
        
        self.cameraIDSpin = QSpinBox(objectName = 'cameraIDSpin')
        self.cameraIDLabel = QLabel("Camera ID No.:")
        self.sourceLayout.addWidget(self.cameraIDLabel)
        self.sourceLayout.addWidget(self.cameraIDSpin)        

        # Camera Settings Panel 
        self.camSettingsPanel = QWidget()
        self.camSettingsLayout = QVBoxLayout()
        self.camSettingsPanel.setLayout(self.camSettingsLayout)
        self.exposureInput = QDoubleSpinBox(objectName = 'exposureInput')
        self.exposureInput.setMaximum(0)
        self.exposureInput.setMaximum(10**6) 
        self.exposureInput.valueChanged[float].connect(self.exposure_slider_changed)
        self.exposureInput.setKeyboardTracking(False)
      
        self.exposureSlider = DoubleSlider(QtCore.Qt.Horizontal, objectName = 'exposureSlider')
        self.exposureSlider.setTickPosition(QSlider.TicksBelow)
        self.exposureSlider.setTickInterval(10)
        self.exposureSlider.setMaximum(10**6)
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
        self.frameRateInput.setMaximum(1000)
        self.frameRateInput.valueChanged[float].connect(self.frame_rate_slider_changed)
        self.frameRateInput.setKeyboardTracking(False)

        self.frameRateSlider = DoubleSlider(QtCore.Qt.Horizontal, objectName = 'frameRateSlider')
        self.frameRateSlider.setTickPosition(QSlider.TicksBelow)
        self.frameRateSlider.setTickInterval(100)
        self.frameRateSlider.setMaximum(1000)
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
        #self.filename_label.setWordWrapMode(QTextOption.WrapAnywhere)
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
        self.droppedFramesLabel = QLabel()
        self.skippedFramesLabel = QLabel()

        self.camStatusPanel.setLayout(camStatusLayout:=QGridLayout())
           
        camStatusLayout.addWidget(self.bufferFillLabel,1,1)
        camStatusLayout.addWidget(self.frameRateLabel,2,1)
        camStatusLayout.addWidget(self.processRateLabel,3,1)
        camStatusLayout.addWidget(self.skippedFramesLabel,4,1)
        camStatusLayout.addWidget(self.droppedFramesLabel,5,1)        
      
        camStatusLayout.addWidget(QLabel('Acq. Buffer:'),1,0)
        camStatusLayout.addWidget(QLabel('Acquisition fps:'),2,0)
        camStatusLayout.addWidget(QLabel('Processing fps:'),3,0)
        camStatusLayout.addWidget(QLabel('Skipped Frames:'),4,0)
        camStatusLayout.addWidget(QLabel('Dropped Frames:'),5,0)
        
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
         
            
    def study_menu_clicked(self):
        """ Creates and displays the 'New Study' dialog. When the dialog
        returns, creates a folder for the study, including a readme file
        with the date and decsriptions.
        """
        
        dialog = NewStudyDialog(res_path = self.resPath)
        
        if dialog.exec():
            try:
                
                now = datetime.now()

                timestamp = now.strftime('%Y_%m_%d_%H_%M_%S_')
                studyPath = os.path.join(self.studyRoot, timestamp + dialog.studyNameInput.text())
                os.mkdir(studyPath)
                self.studyName = timestamp + dialog.studyNameInput.text()
                self.studyPath = studyPath
                p = Path(self.studyPath)
                self.studyReadmePath = os.path.join(self.studyPath, "readme.txt")
                self.recordFolderLabel.setText(str(p))
                self.recordFolder = self.studyPath

                f = open(self.studyReadmePath, "w")
                f.write(self.appName + "\r")
                f.write("Date: " + now.strftime('%Y %m %d, %H: %M: %S \r'))
                f.write("Description: " + dialog.studyDescriptionInput.toPlainText() + "\r")
                f.close()
            except:
                QMessageBox.about(self, "Error", "Cannot create study folder. Check study name does not contain special characters.")   
          
    
    def create_image_display(self, name = "Image Display", statusBar = True, autoScale = True):
        """ Adds a image display to the standard layout. 
        
        Keyword Arguments:
            name      : str
                        Object name of ImageDisplayQT widget, default is "Image Display"
            statusBar : Boolean
                        If True (default), image display has status bar
            autoScale : Boolean 
                        If True (default), image values will be autoscaled.
                        
        Returns:
            (QWidget, QWidget) : tuple of reference to image display widget and 
                                 reference to container widget in which this 
                                 sits. These references should be kept in scope.
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
           
            # Create the processor
            self.imageProcessor = ImageProcessorThread(self.processor, 10, 10, inputQueue = self.inputQueue, 
                                                       multiCore = self.multiCore, 
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
        self.gotRawImage = False
        self.gotProcessedImage = False
        rawImage = None
        im = None
        
        if self.imageThread is not None:
            rawImage = self.imageThread.get_latest_image()        
            self.currentImage = self.imageThread.get_latest_image()
            self.gotRawImage = True
        else:
            self.currentImage = None   
        
        if self.imageProcessor is not None:
      
            # If there is a new processed image, pull it off the queue
            im = self.imageProcessor.get_next_image()
            
            # Some processors return a tuple containing other information. If
            # we get a tuple then the first element is always the image and the second
            # element is an ID number for the image
            if isinstance(im, tuple):
                self.imageId = im[1]
                im = im[0]           
            
            if im is not None:
                self.currentProcessedImage = im
                self.gotProcessedImage = True
                
        else:
            
            self.currentProcessedImage = None         
            
        if self.recording:
            self.record() 
            
        if self.buffering and self.imageThread is not None:
            if self.imageThread.get_num_images_in_auxillary_queue() >= self.buffering_num_frames:
                self.stop_buffering()
                

    def record(self):
        """ If we are recording, handles recording of a frame.
        """
            
        if self.recording and self.videoOut is not None:
            
            imToSave = None
            if self.recordRaw is False:
                if self.currentProcessedImage is not None and self.gotProcessedImage:
                    imToSave = self.currentProcessedImage.copy()

            elif not self.recordBuffered:
                #if self.currentImage is not None and self.gotRawImage:  
                 #   imToSave = self.currentImage
                imToSave = self.imageThread.get_next_auxillary_image() 
            
            
            if self.recordBuffered:
                self.numFramesBuffered = self.imageThread.get_num_images_in_auxillary_queue()
                if self.numFramesBuffered < self.recordBufferSize:
                    self.recordStatusLabel.setText(f"Buffered {self.numFramesBuffered} frames of {self.recordBufferSize}.")
                else:
                    self.record_buffer_full()
            else:
                if imToSave is not None:
                
                    self.numFramesRecorded = self.numFramesRecorded + 1
                    if self.recordType == self.AVI:
                        outImg = self.im_to_vid_frame(imToSave)
                        self.videoOut.write(outImg)
                    if self.recordType == self.TIF:
                        im = Image.fromarray(to16bit(imToSave))
                        im.save(self.videoOut)
                        self.videoOut.newFrame()
                    self.recordStatusLabel.setText(f"Recorded {self.numFramesRecorded} frames.")


    def update_image_display(self):
       """ Displays the current raw image. Sub-classes should overload this 
       if additional display boxes used.
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
           numSkipped = self.imageProcessor.numDropped
           self.processRateLabel.setText(str(round(procFps,1)))
           self.skippedFramesLabel.setText(str(numSkipped))
      
       if self.imageThread is not None: 
           nWaiting = self.imageThread.get_num_images_in_queue()
           fps = self.imageThread.get_actual_fps()
           if self.imageProcessor is not None:
               # Dropped frames only has meaning if we have a processor.
               # otherwise we drop all the frames, there is nothing to do with them
               numDropped = self.imageThread.numDroppedFrames
               self.droppedFramesLabel.setText(str(numDropped))
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
        self.update_info_bar()
      

    def update_info_bar(self):
        """ Writes information to the bottom status bar.
        """
        
        text = ""
        
        text = text + f"Study: {self.studyName}     "
        if self.imageThread is not None:
            if self.imageThread.get_camera().camera_open:
                text = text + "Camera: Open"
                text = text + f"     Frame: {self.imageThread.currentFrameNumber}"
            else:
                text = text + "Camera: Closed"            
            
        else:
            text = text + "Camera: Closed"            
            
        self.infoBar.setText(text)  
        

    def record_options_changed(self):
        """ Handles a change in recording options which necessitate a change
        in which futher options are visible on the record panel.
        """

        if self.recordRawCheck.isChecked():
            self.recordBufferCheck.show()
        else:   
            self.recordBufferCheck.hide()
            
        if self.recordRawCheck.isChecked() and self.recordBufferCheck.isChecked():
            self.recordBufferSpin.show()
            self.recordBufferSizeLabel.show()
        else:   
            self.recordBufferSpin.hide()
            self.recordBufferSizeLabel.hide()            

    
    def start_acquire(self):       
        """ Begin acquiring images by creating an image acquisition thread 
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

                self.imageThread = ImageAcquisitionThread(self.camSource, self.rawImageBufferSize, self.acquisitionLock, imageQueue = self.inputQueue, filename=self.sourceFilename)                                                  
                self.cam = self.imageThread.get_camera()
                self.cam.pre_load(-1)
        else:
            self.imageThread = ImageAcquisitionThread(self.camSource, self.rawImageBufferSize, self.acquisitionLock,imageQueue = self.inputQueue, cameraID = self.cameraIDSpin.value())
            
        # Sub-classes can overload create_processor to create processing threads
        if self.imageThread is not None:            

            self.cam = self.imageThread.get_camera()
    
            if self.cam is not None and self.cam.camera_open:
       
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
                QMessageBox.about(self, "Error", "Unable to connect to camera, check connections.")   

                self.liveButton.setChecked(False)
                

    def pause_acquire(self):
        """ Pauses acquisition and processing threads
        """
        if self.camOpen:
            self.isPaused = True
            self.liveButton.setChecked(False)
            if self.imageThread is not None:
                self.imageThread.pause()
            if self.imageProcessor is not None:
                self.imageProcessor.pause()


    def resume_acquire(self):
        """ Resumes acquisition and processing threads.
        """
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
                 
        self.filename_label.setText("")
    
    
    def snap(self):    
        """ Saves current raw, processed and background images, if they
        exist, to timestamped files in the snaps folder.
        """   
        now = datetime.now()
        
        timestamp = now.strftime('%Y_%m_%d_%H_%M_%S')

        rawFile = os.path.join(self.studyPath, timestamp + '_raw.tif')
        procFile = os.path.join(self.studyPath, timestamp + '_proc.tif')
        backFile = os.path.join(self.studyPath, timestamp + '_back.tif')

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
            
        
    def load_file(self, filename = None):        
        """Gets a filename. If it is valid, switches to file mode, stops timers 
        and image threads, loads in image and starts processor.
                
        Can be called using keyword argument to automatically load a file, useful for
        debugging.

        Optioanl Keyword Arguments:
            filename : str
                       Full path to file to load, including extension
        """
        
        if filename is None:
            filename, filter = QFileDialog.getOpenFileName(parent=self, caption='Select file', filter='*.tif; *.png')
        
        if filename != "":
            if self.camOpen:
                try:
                    self.imageThread.stop()
                    self.imageTimer.stop()
                    self.GUITimer.stop()
                except:
                    pass
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
        images and GUI . 
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
        """ Called when gain slider is moved. Updates the camera gain.
        """
        self.gainInput.setValue(int(self.gainSlider.value()))
        if self.camOpen == True: 
            self.cam.set_gain(self.gainSlider.value())
            self.update_camera_ranges()
          
             
    def frame_rate_slider_changed(self):
        """ Called when frame rate slider is moved. Updates the camera frame rate.
        """
        self.frameRateSlider.setValue(self.frameRateInput.value())
        if self.camOpen:             
            self.cam.set_frame_rate(self.frameRateInput.value())
            fps = self.cam.get_frame_rate()
            self.update_camera_ranges()
    
        
    def closeEvent(self, event):
        """ Called when main window closed.
        """ 
        self.gui_save()

        if self.camOpen:
            self.end_acquire()
            
        if self.imageProcessor is not None:
            self.imageProcessor.stop() 
          
        
        active = mp.active_children()
        for child in active:
            child.terminate()           
             

    def save_image_ac(self, img, fileName):
        """ Utility function to save 16 bit image 'img' to file 'fileName' with autoscaling:
            
        Arguments:
            img      : numpy.array
                       image as numpy array, either 2D for monochrome or 3D
                       for colour
            fileName : full path to file, including extension. Extension will 
                       determine file type, see PIL Image documentation for
                       details. Must be a format that supports 16 bit images
                       such as tif.
        """   
        if fileName:
            img = img.astype('float')
            img = img - np.min(img)
            img = (img / np.max(img) * (2**16 - 1)).astype('uint16')
            im = Image.fromarray(img)
            im.save(fileName)
        
            
    def save_image(self, img, fileName):
        """ Utility function to save image 'img' to file 'fileName' with no scaling.
        
        Arguments:
            img      : numpy.array
                       image as numpy array, either 2D for monochrome or 3D
                       for colour
            fileName : full path to file, including extension. Extension will 
                       determine file type, see PIL Image documentation for
                       details.
        """
        if fileName:            
            im = Image.fromarray(img)
            im.save(fileName)         
            
    
    def pil2np(self, im):
        """ Utility to convert PIL image 'im' to numpy array
        """
        return np.asarray(im)        
    
    
    def load_background(self):
        """ Loads the default background file
        """
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
        """ Handles the start of a recording either directly to a file or to
        a buffer.
        """
        
        if self.recordTifCheck.isChecked():
            self.recordType = self.TIF
        else:
            self.recordType = self.AVI
        
        now = datetime.now()
        if self.recordType == self.TIF:
            self.recordFilename = (self.recordFolder / Path(now.strftime('record_%Y_%m_%d_%H_%M_%S.tif'))).as_posix()
        else:
            self.recordFilename = (self.recordFolder / Path(now.strftime('record_%Y_%m_%d_%H_%M_%S.avi'))).as_posix()
        
        self.recordBuffered = self.recordBufferCheck.isChecked() and self.recordRawCheck.isChecked()
        self.recordBufferSize = self.recordBufferSpin.value()
        
        self.numFramesRecorded = 0
        self.numFramesBuffered = 0
        
        if self.recordRawCheck.isChecked() or self.imageProcessor is None:
            if self.imageThread is not None:
                self.recordRaw = True
                recordImage = self.currentImage
                self.imageThread.flush_auxillary_buffer()
                self.imageThread.set_use_auxillary_queue(True)
                if self.recordBuffered:
                    # Create it one larger, otherwise image acquisition thread sees it
                    # full after last frame and tries to make space by removing the first frame
                    self.imageThread.set_auxillary_queue_size(self.recordBufferSize + 1)
            else:
                QMessageBox.about(self, "Error", f"Images not being acquired.")
                    
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
            
            

    def create_video_file(self, exampleImage, frameRate = 20.0):
        """ Creates a MJPEG video file.
        
        Arguments:
            exampleImage  : numpy.ndarray
                            example image frame used to determine image size
        
        Keyword Arguments:
            frameRate     : float
                            framte rate of video file in Hz
                            
        Returns: 
            Boolean       : True if video created successfully, otherwise False                    
        """
        
        try:
            fourcc = cv.VideoWriter_fourcc(*"MJPG")
            imSize = (np.shape(exampleImage)[1],np.shape(exampleImage)[0]) 
            self.numFramesRecorded = 0
            self.videoOut = cv.VideoWriter(self.recordFilename, fourcc, frameRate, imSize)            
            return True

        except:
            return False
       
    
    def record_buffer_full(self):
        """ When the recording buffer has been filled, writes the buffer to 
        the video recording file.
        """
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        self.recording = False

        self.imageThread.set_use_auxillary_queue(False)
            
        for idx in range(self.numFramesBuffered):  
            imToSave = self.imageThread.get_next_auxillary_image()
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
        self.imageThread.set_use_auxillary_queue(False)

        QApplication.restoreOverrideCursor()

        
        
    def stop_recording(self):
        """ Handles everything needed to stop a recording.
        """
        if self.recordType == self.AVI and self.videoOut is not None:
            self.videoOut.release()
        self.imageThread.set_use_auxillary_queue(False)
        self.videoOut = None
        self.recording = False
        self.toggleRecordButton.setText("Start Recording")
        self.recordRawCheck.setEnabled(True)
        self.recordFolderButton.setEnabled(True)


    def im_to_vid_frame(self, imToSave):
        """ Converts image to video frame that can be recorded using video
        writer.
        """
        
        if imToSave.ndim  == 3:
            return to8it(imToSave)
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
        if self.camTypes[self.camSourceCombo.currentIndex()] == self.FILE_TYPE:
            self.end_acquire()

            # Hide camera controls, show file widgets  
            self.cameraIDSpin.hide()
            self.cameraIDLabel.hide()

            self.inputFilePanel.show()
            self.camSettingsPanel.hide()
            self.liveButton.hide()
            self.camStatusPanel.hide()
            self.inputFilePanel.show()

        else:
           
            # Show camera controls, hide file widgets
            self.cameraIDSpin.show()

            self.camSettingsPanel.show()
            self.cameraIDLabel.show()

            self.liveButton.show()
            self.camStatusPanel.show()
            self.inputFilePanel.hide()
            self.fileIdxWidget.hide()

    
    def gui_save(self):
        """ Saves all current values in the GUI widgets to registry"""
        
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
              value = obj.isChecked()  
              self.settings.setValue(name, value)

          if isinstance(obj, LabelCheckboxWidget):
              name = obj.checkbox.objectName()
              state = obj.checkbox.isChecked()  
              self.settings.setValue(name, state)

          if isinstance(obj, RangeSpinBox):
              name = obj.lower.objectName()
              value = obj.lower.value() 
              self.settings.setValue(name, value)
              name = obj.upper.objectName()
              value = obj.upper.value() 
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
                  value = (self.settings.value(name))  # get stored value from registry
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
                  if obj.maximum() < int(value):
                      obj.setMaximum(int(value))
                  if obj.minimum() > int(value):
                      obj.setMinimum(int(value))
                  obj.setValue(int(value)) 
    
          if isinstance(obj, QRadioButton):
             name = obj.objectName()
             value = self.settings.value(name)  # get stored value from registry
             if value != None:
                 obj.setChecked(str2bool(value))   

          if isinstance(obj, LabelCheckboxWidget):
             name = obj.checkbox.objectName()
             value = self.settings.value(name)  # get stored value from registry
             if value != None:
                 obj.checkbox.setChecked(str2bool(value))  


          if isinstance(obj, RangeSpinBox):
             name = obj.lower.objectName()
             value = self.settings.value(name)  # get stored value from registry
             if value != None:
                 obj.lower.setValue(float(value) )
             
             name = obj.upper.objectName()
             value = self.settings.value(name)  # get stored value from registry
             if value != None:
                 obj.upper.setValue(float(value) )
                                     
              
    
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
        if not self.camOpen:
            self.start_acquire()
            
        elif self.camOpen and self.isPaused:
            self.resume_acquire() 
            
        elif self.camOpen and not self.isPaused:
            self.pause_acquire()  

    def settings_button_clicked(self):
        self.expanding_menu_clicked(self.settingsButton, self.settingsPanel)
        
    def source_button_clicked(self):
        self.expanding_menu_clicked(self.sourceButton, self.sourcePanel)
  
    def exit_button_clicked(self):
        self.close()     
    
    def save_as_button_clicked(self, event):
        self.save_as()
  
    def save_raw_as_button_clicked(self, event):
        self.save_raw_as()

    def snap_button_clicked(self, event):
        self.snap()

    def record_button_clicked(self):
        self.expanding_menu_clicked(self.recordButton, self.recordPanel)
    
    def toggle_record_button_clicked(self):
        if self.recording is False:
            self.start_recording()
        else:
            if self.recordBuffered:
                self.record_buffer_full()
            else:
                self.stop_recording()
        self.update_GUI()    
    
    
    def record_folder_clicked(self):

         try:
             folder = QFileDialog.getExistingDirectory(self, 'Select filename to save to:', self.recordFolder)
         except:
             folder = None
         if folder is not None and folder != "":
             self.recordFolder = folder
             self.recordFolderLabel.setText(self.recordFolder)
         else:
             QMessageBox.about(self, "Error", "Invalid folder.") 
             
             
    def start_buffering(self, num_frames, finish_call):
        """ Starts buffering of frames in the auxillary queue. Any existing
        frames in the queue will be lost.
        
        Arguments:
            num_frames  : total number of frames to buffer
            finish_call : function to call once buffer is full.
        """
        if self.imageProcessor is not None:
            self.buffering = True
            self.buffering_num_frames = num_frames
            self.buffering_end_call = finish_call
            self.imageThread.set_auxillary_queue_size(num_frames)
            self.imageThread.flush_auxillary_buffer()
            self.imageThread.set_use_auxillary_queue(True)
            
        
    def stop_buffering(self):
        """ Stops buffering of frames in the auxillary queue. Called 
        automatically once buffer is full.
        """
        self.buffering = False
        self.imageThread.set_use_auxillary_queue(False)
        if self.buffering_end_call is not None:
            self.buffering_end_call()
            
            
    def get_auxillary_stack(self):
        """ Obtains all the frames in the auxillary queue as a numpy array
        """
        frames = []
        for i in range(self.buffering_num_frames):
            frames.append(self.imageThread.get_next_auxillary_image())  
        return np.array(frames)    
        

        

class NewStudyDialog(QDialog):
    """ Dialog box to create a new study."
    """
    
    def __init__(self, res_path = None):
        super().__init__()
        self.res_path = res_path
        
        iconFilename = 'logo_256_red.png'
        
        if iconFilename is not None:
            self.setWindowIcon(QtGui.QIcon(iconFilename))
        
        file=os.path.join(self.res_path, 'cas_modern.css')
        with open(file,"r") as fh:
            self.setStyleSheet(fh.read())

        self.setWindowTitle("New Study")
        self.setMinimumWidth(500)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()

        self.studyNameInput = QLineEdit()
        
        self.studyDescriptionInput = QPlainTextEdit()

        label1 = QLabel("Study Name:")
        label1.setProperty("subheader", "true")
        self.layout.addWidget(label1)
        
        self.layout.addWidget(self.studyNameInput)
          
        label2 = QLabel("Notes:")
        self.layout.addWidget(label2)
        label2.setProperty("subheader", "true")

        self.layout.addWidget(self.studyDescriptionInput)
        
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


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
