# -*- coding: utf-8 -*-
"""
ImageDisplay extend QLable to provide a widget for scientific image display
in PyQT GUIs

@author: Mike Hughes
Applied Optics Group
University of Kent
"""
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont, QFontMetrics

import numpy as np
import cv2 as cv

import time

import matplotlib.pyplot as plt
from matplotlib import cm
import math
import cmocean

class ImageDisplay(QLabel):
    
   mouseMoved = pyqtSignal(int, int)
   circle = False
   imageSize = (0,0)
   isStatusBar = False
   autoScale = True
       
   pmap = None
   displayMin = 0
   displayMax = 255
   
   ELLIPSE = 0
   LINE = 1
   POINT = 2
   RECTANGLE = 3
   
   overlays = []
   
   nOverlays = 0
   
   colortable = None
   roi = None
  
   def __init__(self, **kwargs):
       self.name = kwargs.get('name', 'noname')
       super().__init__()
       self.setMouseTracking(True)
       self.setCursor(Qt.CrossCursor)    
       self.mouseX = 0
       self.mouseY = 0
       self.set_mono_image(np.zeros((20,20)))
       self.setMinimumSize(1,1)
       self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,  QtWidgets.QSizePolicy.MinimumExpanding))
       self.setMaximumSize(2048, 2048)
       self.setAlignment(Qt.AlignTop)
       self.installEventFilter(self)
       self.setStyleSheet("border:1px solid white")
       self.setAlignment(Qt.AlignCenter)
       self.dragging = False
       self.roi = None
       self.dragToX = None
       self.dragToY = None
   
   def set_name(name):
       self.name = name
   
   # Rceord mouse positions for next update of status bar    
   def mouseMoveEvent(self, event):
       if self.pmap is not None:
           self.mouseX, self.mouseY = self.image_coords(event.x(), event.y())
      
           if self.mouseX > 0 and self.mouseX < np.shape(self.currentImage)[1] and self.mouseY > 0 and self.mouseY < np.shape(self.currentImage)[0] :
               self.mouseMoved.emit(self.mouseX, self.mouseY)
               self.dragToX = self.mouseX
               self.dragToY = self.mouseY
           else:
               self.mouseX = None
               self.mouseY = None
       self.update()     
           
          
   # Start of ROI dragging        
   def mousePressEvent(self, event):
       self.dragging = True
       self.roi = None
       self.dragX = self.mouseX
       self.dragY = self.mouseY
       self.dragToX = self.dragX
       self.dragToY = self.dragY
       
       
   # End of ROI dragging   
   def mouseReleaseEvent(self, event):
       self.dragging = False
       if self.dragX != self.dragToX or self.dragY != self.dragToY:
           self.roi = int(round(min(self.dragX, self.dragToX))), int(round(min(self.dragY, self.dragToY))), int(round(max(self.dragX, self.dragToX))), int(round(max(self.dragY, self.dragToY)))
       else:
           self.roi = None
       
   def set_mono_image(self, img):
       
       #print(self.name, " Set Mono Image")
       self.currentImage = img
       self.imageSize = np.shape(img)
       
       if img is not None and np.size(img) > 0:
           if self.autoScale and np.max(img) != 0:
               img = img - np.min(img)
               img = (img / np.max(img) * 255)
           else:
               img = img - self.displayMin
               img = (img / self.displayMax * 255)
           
           img = img.astype('uint8')
           
           self.dispImg = img           
           
           self.image = QtGui.QImage(img.copy(), img.shape[1], img.shape[0], img.shape[1], QtGui.QImage.Format_Indexed8)
           
           if self.colortable is not None:
               self.image.setColorTable(self.colortable)
           scaledSize = QtCore.QSize(self.geometry().width(), self.geometry().height()-40)
           
           self.pmap = QtGui.QPixmap.fromImage(self.image).scaled(scaledSize, QtCore.Qt.KeepAspectRatio)

           self.setPixmap(self.pmap)
       else:
           self.pmap = None

        
   # redraw if resized    
   def resizeEvent(self, new):
       self.set_mono_image(self.currentImage)
       
      
   # convert image co-ordinates to screen co-ordinates     
   def screen_coords(self, x, y):
       if self.currentImage is None or self.pmap is None:
           return None, None
       else:
           xOffset = (self.width() - self.pmap.width())/ 2 
           yOffset = (self.height() - self.pmap.height())/ 2 
           screenX = round(x * (self.pmap.width()) / np.shape(self.currentImage)[1] + xOffset)
           screenY = round(y * (self.pmap.height()) / np.shape(self.currentImage)[0] + yOffset)
           return screenX, screenY
       
   # convert screen co-ordinates to image co-ordinates    
   def image_coords(self, x,y):
       if self.currentImage is None or self.pmap is None:
           return None, None
       else:
           xOffset = (self.width() - self.pmap.width())/ 2 
           yOffset = (self.height() - self.pmap.height())/ 2 
           imageX = round((x - xOffset) / (self.pmap.width()) * np.shape(self.currentImage)[1])
           imageY = round((y - yOffset) / (self.pmap.height()) * np.shape(self.currentImage)[0])
           return imageX, imageY
     
   # covert images dimensions to screen dimensions
   def screen_dims(self, x,y):
           screenX = round(x * (self.pmap.width()) / np.shape(self.currentImage)[1])
           screenY = round(y * (self.pmap.height()) / np.shape(self.currentImage)[0])               
           return screenX, screenY
       
  
        
   def paintEvent(self, event):
       
       super().paintEvent(event)

       painter = QPainter(self)
       
       ### Draw overlays
       for overlay in self.overlays:
           painter.setPen(overlay.pen)
           painter.setBrush(overlay.fill)
           x,y = self.screen_coords(overlay.x1, overlay.y1)
           w,h = self.screen_dims(overlay.x2, overlay.y2)
           
           if overlay.overlayType == self.ELLIPSE:              
               painter.drawEllipse(x,y,w,h)
           elif overlay.overlayType == self.RECTANGLE:
               painter.drawRect(x,y,w,h)
           elif overlay.overlayType == self.POINT:
               painter.drawPoint(x,y)
           elif overlay.overlayType == self.LINE:
               painter.drawLine(x,y,w,h)
               
       if self.dragging:
           painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
           startX, startY = self.screen_coords(self.dragX, self.dragY)
           endX, endY = self.screen_coords(self.dragToX, self.dragToY)
           if startX is not None and startY is not None and endX is not None and endY is not None:
               painter.drawRect(startX, startY, endX- startX, endY- startY)
           
           
           
       if self.roi is not None:
           drawX, drawY = self.screen_coords(self.roi[0], self.roi[1])
           endX, endY = self.screen_coords(self.roi[2], self.roi[3])
           width = endX- drawX
           height = endY - drawY
           painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
           painter.drawRect(drawX, drawY, width, height)
           #sprint(drawX, drawY, width, height)
           
     
        
       if self.isStatusBar and self.pmap is not None:

           font = painter.font()
           fm = QFontMetrics(font)
           
           if self.mouseX is not None and self.mouseY is not None and self.currentImage is not None:
               try:
                   mX = str(round(self.mouseX))
                   mY = str(round(self.mouseY))
                   #cursorVal = str(round(self.currentImage[round(self.mouseY), round(self.mouseX)]))
                   
                   cursorVal = str(round(self.currentImage[round(self.mouseY), round(self.mouseX)],1))
               except:
                   mX = '-'
                   mY = '-'
                   cursorVal = '--'
           else:
               mX = '-'
               mY = '-'
               cursorVal = '--'
               
           if self.currentImage is not None:
               self.meanPixel = str(round(np.mean(self.currentImage),1))
               self.maxPixel = str(round(np.max(self.currentImage)))
               self.minPixel = str(round(np.min(self.currentImage)))
           else:
               self.meanPixel = '-'
               self.maxPixel = '-'
               self.minPixel = '-'
               
           if self.currentImage is not None and self.roi is not None:
               roi = self.currentImage[self.roi[0] : self.roi[2], self.roi[1]: self.roi[3]]
               self.roiMax = str(round(np.max(roi)))
               self.roiMin = str(round(np.min(roi)))
               self.roiMean = str(round(np.mean(roi),1))               
               
           text = '(' + mX + ',' + mY + ') = ' + cursorVal + ' | [' + self.minPixel + '-' + self.maxPixel + ', Mean: ' + self.meanPixel + ']'
           
           if self.roi is not None:
               text = text + ' | [ROI: (' + str(self.roi[0]) + ',' + str(self.roi[1]) + ')-(' + str(self.roi[2]) + '-' + str(self.roi[3]) + '): ' + self.roiMin + '-' + self.roiMax + ', Mean: ' + self.roiMean + ']' 
           elif self.dragging:    
               text = text + ' | [ROI: (' + str(self.dragX) + ',' + str(self.dragY) + ')-(' + str(self.dragToX) + '-' + str(self.dragToY) + ')'

           xPos = (self.width() - self.pmap.width()) /2
           painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
           painter.drawRect(xPos + 1, self.height() - fm.height() - 5, self.pmap.width() - 2, self.pmap.height())
           painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
           painter.drawText(xPos + 10,self.height() - 5, text)
          
               
        
   def add_overlay(self, overlayType, *args):
       
       x1 = args[0]
       y1 = args[1]
       if overlayType == self.ELLIPSE or overlayType == self.RECTANGLE:
           w = args[2]
           h = args[3]
           pen = args[4]
           fill = args[5]

    
       if overlayType == self.POINT or overlayType == self.LINE:
           w = 1
           h = 1
           pen = args[4]
           fill = args[5]
           
       newOverlay = overlay(overlayType, x1, y1, w, h, pen, fill)
       
       self.overlays.append(newOverlay)
       return newOverlay
       
   
   def remove_overlay(self, overlay):
       self.overlays.remove(overlay)          
           
   def clear_overlays(self):
       self.overlays = []
           
   
   def num_overlays(self):
       return len(self.overlays)
   
   def set_auto_scale(self, autoScale):
       self.autoScale = autoScale
   
   def set_scale_limit(self, scaleMin, scaleMax):
       self.displayMax = scaleMax
       self.displayMin = scaleMin
    
   # Converts a named matplotlib colormap to a QImage colormap
   def set_colormap(self, colormapName):
       if colormapName is None:
           self.colortable = None
       else:   
           colormap = cm.get_cmap(colormapName) 
           colormap._init()
           lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
           lut = lut[:,0:3]
           nCols = np.shape(lut)[0]   # Seem to be 513 x 4
               
           self.colortable = []
           for i in range(0, 256):
               col = round(i * nCols / 256)
               self.colortable.append(QtGui.qRgb(lut[col,0],lut[col,1],lut[col,2]))
    

class overlay():
    x1 = None
    x2 = None
    y1 = None
    y2 = None
    pen = None
    fill = None
    overlayType = None
    idx = None
    def __init__(self, overlayType, x1, y1, x2, y2, pen, fill):
        #self.idx = idx
        self.overlayType = overlayType
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.pen = pen
        self.fill = fill