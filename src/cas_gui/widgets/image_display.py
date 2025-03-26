# -*- coding: utf-8 -*-
"""
ImageDisplay is a widget for PyQT which provides a scientific image display
panel.

ImageDisplay is based on a QLabel widget.

@author: Mike Hughes
Applied Optics Group
School of Physics & Astronomoy
University of Kent
"""

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QImage, QPixmap, QPainter, QPen, QGuiApplication
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont, QFontMetrics

import numpy as np
from matplotlib import cm
import math
import time

import cv2 as cv

class ImageDisplay(QLabel):
    
   ELLIPSE = 0
   LINE = 1
   POINT = 2
   RECTANGLE = 3
   TEXT = 4
  
   MONO = 0
   RGB = 1
   GRAPH = 2
    
   mouseMoved = pyqtSignal(int, int)
   roiChanged = pyqtSignal()  


   imageSize = (0,0)
   
   isStatusBar = True
   autoScale = True
   enableZoom = True
   isRoiEnabled = True
   isZoomEnabled = True
   isZoomIndicator = True
   
   panning = False
   zoomLocation = None
   pmap = None
   dragging = False
   dragToX = None
   dragToY = None
   imageWidth = None
   imageHeight = None
   
   
   graph_line_width = 5
   graph_width = 512
   graph_height = 512
   displayMin = 0
   displayMax = 255
   zoomLevel = 0
   zoomStepDivider = 2   
    
   zoomIndicatorPen = QPen(Qt.white, 1, Qt.SolidLine)
   zoomIndicatorBrush = QBrush(Qt.white, Qt.SolidPattern)
   zoomIndicatorWidth = 60
   zoomIndicatorOffsetX = 20
   zoomIndicatorOffsetY = 20
   
   roiDragContrastPen = QPen(Qt.white, 2, Qt.SolidLine)
   roiDragPen = QPen(Qt.red, 2, Qt.DotLine)
   roiContrastPen = QPen(Qt.white, 2, Qt.SolidLine)
   roiPen = QPen(Qt.green, 2, Qt.DotLine)
   
   statusPen =  QPen(Qt.white, 2, Qt.SolidLine)
   statusBrush = QBrush(Qt.white, Qt.SolidPattern)
   statusTextPen = QPen(Qt.black, 2, Qt.SolidLine)
   

   graphPen = QPen(Qt.white, 1, Qt.SolidLine)
   graphCursorBrush = QBrush(Qt.white, Qt.SolidPattern)
   graphCursorPen = QPen(Qt.white, 2, Qt.SolidLine)
   graphCursorSize = 4
   graphLabelPen = QPen(Qt.white, 2, Qt.SolidLine)
   graphZeroPen = QPen(Qt.white, 1, Qt.DotLine)
   graphDisplayMin = None
   graphDisplayMax = None
   
   imageMode = MONO
   
   minAutoscaleUpper = -1e10
   
   overlays = []
   nOverlays = 0
   
   colortable = None
   roi = None
   
   lastFrameTime = 0


   
   
   def __init__(self, **kwargs):
       
       self.name = kwargs.get('name', 'noname')
       
       super().__init__()

       self.setMouseTracking(True)
       self.setCursor(Qt.CrossCursor)    
       self.mouseX = 0
       self.mouseY = 0
       
       self.set_image(np.zeros((20,20)))      
       #self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,  QtWidgets.QSizePolicy.MinimumExpanding))
       self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored,  QtWidgets.QSizePolicy.Ignored))

       self.setMaximumSize(2048, 2048)
       self.setMinimumSize(400, 400)

       
       self.setAlignment(Qt.AlignTop)
       self.installEventFilter(self)
       self.setStyleSheet("border:1px solid white")
       self.setAlignment(Qt.AlignCenter)
       
       #self.setSizePolicy(QSizePolicy.Ignored)
       
   
   def set_name(name):
       self.name = name
       
   
   def mouseMoveEvent(self, event):
       """ Record mouse positions and update status bar  """  

       if self.pmap is not None:
           
           self.mouseX, self.mouseY = self.image_coords(event.x(), event.y()) 


           if self.panning and self.is_mouse_on_image():
            
              newX, newY = self.mouseX, self.mouseY
              moveX = newX - self.panningX
              moveY = newY - self.panningY
              h,w = self.currentImage.shape[0:2]
            
              self.displayX = min(max(self.displayX - moveX,0), w - self.displayW)
              self.displayY = min(max(self.displayY - moveY,0), h - self.displayH)
              self.panningX, self.panningY = self.image_coords(event.x(), event.y())

              self.set_image(self.currentImage)
         
           if self.is_mouse_on_image():
               closestX,closestY = self.image_coords_closest(event.x(), event.y()) #self.mouseMoved.emit(self.mouseX, self.mouseY)
               self.dragToX = closestX
               self.dragToY = closestY
           else:
               self.mouseX = None
               self.mouseY = None
       self.update()     
           
          
   def mousePressEvent(self, event):
       """Start of ROI dragging """
       if event.buttons() == QtCore.Qt.LeftButton and self.isRoiEnabled and self.mouseX is not None and self.mouseY is not None:
           self.dragging = True
           self.roi = None
           self.dragX, self.dragY = self.image_coords_closest(event.x(), event.y()) #self.mouseMoved.emit(self.mouseX, self.mouseY)
           #self.dragX = closestX
           #self.dragY = closestY
           self.dragToX = self.dragX
           self.dragToY = self.dragY
       elif (event.buttons() == QtCore.Qt.MidButton or event.buttons() == QtCore.Qt.RightButton) and self.is_mouse_on_image():
           self.panning = True
           self.panningX, self.panningY = (self.mouseX, self.mouseY)
       
       
   def mouseReleaseEvent(self, event):
       """ End of ROI dragging """  
       if self.dragging:
           self.dragging = False
           if self.dragX != self.dragToX and self.dragY != self.dragToY:
               self.roi = int(round(min(self.dragX, self.dragToX))), int(round(min(self.dragY, self.dragToY))), int(round(max(self.dragX, self.dragToX))), int(round(max(self.dragY, self.dragToY)))
           else:
               self.roi = None
           self.roiChanged.emit()
           
            
       self.panning = False
       
       
   def wheelEvent(self,event):
       """ Updates zoom level when mouse wheel is scrolled"""
       if self.imageMode == self.GRAPH:
           self.zoomLevel = 0
           return

       if self.isZoomEnabled and self.mouseX:
           self.zoomLocation = (self.mouseX, self.mouseY)           
           self.zoomLevel = self.zoomLevel + round(event.angleDelta().y() / 120) / self.zoomStepDivider
           self.zoomLevel = max(self.zoomLevel, 0)
           self.set_image(self.currentImage)
  
           
   def is_mouse_on_image(self):
       """ Returns True if mouse if over image"""
       if self.mouseX is None or self.mouseY is None:
           
           return False
       
       if self.mouseX >=0 and self.mouseY >=0 and self.mouseX < self.imageSize[1] and self.mouseY < self.imageSize[0]:
           return True
       else:
           return False
       
        
   def set_graph(self, graph):
       self.graphData = graph       
       
       img = np.zeros((self.graph_width, self.graph_height))
       self.set_image(img)
       
       self.imageMode = self.GRAPH
       self.zoomLevel = 0



       
       
       
   def set_image(self,img):
       """ Sets the image `img` as the current image. `img` is a numpy array, if
       it has three dimensions then it is assumed that it is a colour images, and
       if it has two dimensions then it is assumed that is is a monochrome image."""
      
           
       if img.ndim > 2:
           self.set_rgb_image(img)
       else:
           self.set_mono_image(img)
           
           
   def set_mono_image(self, img):
       """ Sets a grayscale image as the current image """
       
       # Compare width and height with width and height of last image. If it
       # has changed then we adjust the displayX and displayY so we are looking
       # at the same area.
       if self.imageWidth is not None:       
           if np.shape(img)[1] != self.imageWidth:
               self.displayX = int(self.displayX / self.imageWidth * np.shape(img)[1])
           if np.shape(img)[0] != self.imageHeight:
               self.displayY = int(self.displayY / self.imageHeight * np.shape(img)[0])
           
       self.imageWidth = np.shape(img)[1]    
       self.imageHeight = np.shape(img)[0]    
       
       
       
       self.currentImage = img
       self.imageMode = self.MONO
       self.imageSize = np.shape(img)
       if img is not None and np.size(img) > 0:           
           
           t1 = time.perf_counter()
           if self.autoScale: #and np.max(img) != 0:
               img = img.astype('float32')
               img = img - np.min(img)
               m = max(np.max(img), self.minAutoscaleUpper)
               if m > 0:
                   sf =  255 / m
               else:
                   sf = 0
               img = img * sf
              
               #img = cv.normalize(img,0,255,cv.NORM_MINMAX)           
            
           img = img.astype('uint8')
           
           
           #if self.fixedView:
           #    self.getView(img)
               
           #else:    
           self.displayImage = self.zoom(img)          
            
           self.image = QtGui.QImage(self.displayImage.copy(), self.displayImage.shape[1], self.displayImage.shape[0], self.displayImage.shape[1], QtGui.QImage.Format_Indexed8)
                      
           # Set colormap
           if self.colortable is not None:
               self.image.setColorTable(self.colortable)
           
           scaledSize = QtCore.QSize(self.geometry().width(), self.geometry().height()-40)
           self.pmap = QtGui.QPixmap.fromImage(self.image).scaled(scaledSize, QtCore.Qt.KeepAspectRatio)
           self.setPixmap(self.pmap)
      
       else:

           self.pmap = None


   def set_rgb_image(self, img):
       """ Sets a colour RGB image as the current image """
       
       
       # Compare width and height with width and height of last image. If it
       # has changed then we adjust the displayX and displayY so we are looking
       # at the same area.
       if self.imageWidth is not None:       
           if np.shape(img)[1] != self.imageWidth:
               self.displayX = int(self.displayX / self.imageWidth * np.shape(img)[1])
           if np.shape(img)[0] != self.imageHeight:
               self.displayY = int(self.displayY / self.imageHeight * np.shape(img)[0])
           
       self.imageWidth = np.shape(img)[1]    
       self.imageHeight = np.shape(img)[0]    
       
       
       self.currentImage = img.astype(float)       
       self.imageMode = self.RGB       
       self.imageSize = np.shape(img)

       
       if img is not None and np.size(img) > 0:
           
           # img = img.astype('float')
           
           # if self.autoScale and np.max(img) != 0:
           #     img = img - np.min(img)
           #     img = (img / np.max(img) * 255)
           # else:
           #     img = img - self.displayMin
           #     img = (img / self.displayMax * 255)
           
           img = img.astype('uint8')

           imgZoom = self.zoom(img)
       
           self.displayImage = np.empty((imgZoom.shape[0], imgZoom.shape[1], 4), np.uint8, 'C')       
           self.displayImage[...,0] = imgZoom[...,2]
           self.displayImage[...,1] = imgZoom[...,1]
           self.displayImage[...,2] = imgZoom[...,0]
           self.displayImage[...,3].fill(255)
    
           self.displayImage2 = self.displayImage.copy()
           self.image = QtGui.QImage(self.displayImage2.copy(), self.displayImage.shape[1], self.displayImage.shape[0], QtGui.QImage.Format_RGB32)
           scaledSize = QtCore.QSize(self.geometry().width(), self.geometry().height()-40)

           self.pmap = QtGui.QPixmap.fromImage(self.image).scaled(scaledSize, QtCore.Qt.KeepAspectRatio)
    
           self.setPixmap(self.pmap)
       
       
       
   def zoom(self, img):
        """ Returns a zoomed version of the image for display.
        """

        if self.isZoomEnabled and self.zoomLevel > 0:               
            
            scaleFactor = 2**self.zoomLevel
            
            shape = np.array(img.shape)[0:2]
          
            # If we showing at least four pixels, calculate zoom
            if max(np.round(shape / (2**self.zoomLevel))) < 4:
                self.zoomLevel = round( np.log2(max(shape)/4) * self.zoomStepDivider  ) / self.zoomStepDivider
            
            zoomShape = np.round(shape / (2**self.zoomLevel))
            
            imageAspectRatio = np.shape(img)[1]/np.shape(img)[0]
            aspectRatio = self.geometry().width() / self.geometry().height() 
            
            
            if imageAspectRatio > aspectRatio:
                self.displayW = int(zoomShape[1]) 
                self.displayH =  min(shape[0], int(round(self.displayW / aspectRatio)))
     
            else:
                self.displayH = int(zoomShape[0]) 
                self.displayW = min(shape[1], int(round(self.displayH * aspectRatio))) 

            # Sets the current view position within the image based on the zoom
            # level and our scrolling position
            if self.zoomLocation is not None:
                h,w = self.currentImage.shape[0:2]
                                
                self.displayX = int(round(self.zoomLocation[0] - zoomShape[0] / 2))
                self.displayY = int(round(self.zoomLocation[1] - zoomShape[1] / 2))
                self.displayX = min(max(self.displayX ,0), w - self.displayW)
                self.displayY = min(max(self.displayY ,0), h - self.displayH)
               
                self.zoomLocation = None                          
           
            # Crop the image so we show only the zoomed area 
            if self.imageMode == self.RGB:
                imgCrop = img[self.displayY: self.displayY + self.displayH, self.displayX: self.displayX + self.displayW,:]
            else:
                imgCrop = img[self.displayY: self.displayY + self.displayH, self.displayX: self.displayX + self.displayW]

            zoomImage = imgCrop
            
            
        
        else:  #no Zoom
          
            self.displayX = 0
            self.displayY = 0
            self.displayW = img.shape[1]
            self.displayH = img.shape[0]
            zoomImage = img    
               
        return zoomImage
    
   
   def resizeEvent(self, new):
            """ Redraw if resized """
            self.set_image(self.currentImage)
       
      
   def screen_coords(self, x, y):
       """ Convert image co-ordinates to screen co-ordinates """
       if self.currentImage is None or self.pmap is None:
           return None, None
       else:
           xOffset, yOffset = self.screen_offsets()
           screenX = round((x - self.displayX) * (self.pmap.width()) / np.shape(self.displayImage)[1] + xOffset)
           screenY = round((y - self.displayY) * (self.pmap.height()) / np.shape(self.displayImage)[0] + yOffset)
           return screenX, screenY
       
       
   def image_coords(self, x, y):
       """ Convert screen co-ordinates to floor image co-ordinates """    

       if self.currentImage is None or self.pmap is None:
           return None, None
       else:
           xOffset, yOffset = self.screen_offsets()
           imageX = math.floor( (x - xOffset) / (self.pmap.width()) * np.shape(self.displayImage)[1] + self.displayX)
           imageY = math.floor( (y - yOffset) / (self.pmap.height()) * np.shape(self.displayImage)[0] + self.displayY)
           return imageX, imageY
   
        
   def image_coords_closest(self, x, y):
       """ Convert screen co-ordinates to cloest image co-ordinates """    

       if self.currentImage is None or self.pmap is None:
           return None, None
       else:
           xOffset, yOffset = self.screen_offsets()
           imageX = round( (x - xOffset) / (self.pmap.width()) * np.shape(self.displayImage)[1] + self.displayX)
           imageY = round( (y - yOffset) / (self.pmap.height()) * np.shape(self.displayImage)[0] + self.displayY)
           return int(imageX), int(imageY)
       
  
   def screen_offsets(self):  
           """ Returns the x and y co-ordinates of the top left of the image relative to Widget"""
           xOffset = (self.width() - self.pmap.width())/ 2 
           yOffset = (self.height() - self.pmap.height())/ 2 
           return int(xOffset), int(yOffset)
       
       
   def screen_size(self):  
           """ Returns the width and height of the view window in screen pixels"""
           return self.pmap.width(), self.pmap.height()
       
           
   def screen_dims(self, x,y):       
           """ Convert image dimensions to screen dimensions """
           screenX = round(x * (self.pmap.width()) / np.shape(self.displayImage)[1])
           screenY = round(y * (self.pmap.height()) / np.shape(self.displayImage)[0])               
           return int(screenX), int(screenY)
       
        
   def paintEvent(self, event):
       """ Handles drawing of widget, including labels, overlays etc.     """
       

       super().paintEvent(event)
       self.draw()


   def draw(self):
       """ This is where the whole thing is drawn"""       

       self.lastFrameTime = time.perf_counter()
       painter = QPainter(self)
       
       # Prevent drawing outside of image
       painter.setClipRect(QRect(*self.screen_offsets(), *self.screen_size() ))

       if self.imageMode == self.GRAPH:

           if self.graphData is not None:
               num_points = np.shape(self.graphData)[0]  
                 
               max_val = np.max(self.graphData)
               min_val = np.min(self.graphData)
               
               if self.graphDisplayMin is None:
                   graphMin = min_val
               else:
                   graphMin = self.graphDisplayMin
               
               if self.graphDisplayMax is None:
                   graphMax = max_val
               else:
                   graphMax = self.graphDisplayMax#
               plotX = np.linspace(0, self.graph_width, num_points)
               plotY = self.graph_height - (self.graphData - graphMin) / ( graphMax - graphMin) * self.graph_height
              
               painter.setPen(self.graphPen)

               for i in range(num_points - 1):
               
                   x,y = self.screen_coords(plotX[i],plotY[i])
                   x2,y2 = self.screen_coords(plotX[i + 1],plotY[i+1])
                   painter.drawLine(x,y,x2,y2)
                   
           font = painter.font()
           fm = QFontMetrics(font)        

           painter.setPen(self.graphLabelPen)
           prec = 3
           
           
           # Max val
           x,y = self.screen_coords(0,0)
           painter.drawText(x + 4, y + fm.height(), str(round(graphMax,prec)))
           painter.drawLine(x,y,x + 20,y) 
           
           # Min Val
           x,y = self.screen_coords(0,self.graph_height)
           painter.drawText(x + 4, y - fm.height(), str(round(graphMin,prec)))
           painter.drawLine(x,y,x + 20,y) 
           
           
           # Zero Line
           if graphMax > 0 and graphMin < 0:

               painter.setPen(self.graphZeroPen)

               x,y = self.screen_coords(0, self.graph_height - (0 - graphMin) / ( graphMax - graphMin) * self.graph_height)
               painter.drawLine(x,y,x + 100000,y) 
               
  

            
       #################### Draw overlays
       for overlay in self.overlays:
           
           painter.setPen(overlay.pen)
           if overlay.fill is not None:
               painter.setBrush(overlay.fill)
           
           # Convert the image co-ordinates to screen co-ordinates    
           x,y = self.screen_coords(overlay.x1, overlay.y1)
           w,h = self.screen_dims(overlay.x2, overlay.y2)
           
           if overlay.overlayType == self.ELLIPSE:    
               painter.drawEllipse(x,y,w,h)
           elif overlay.overlayType == self.RECTANGLE:
               painter.drawRect(x,y,w,h)
           elif overlay.overlayType == self.POINT:
               painter.drawPoint(x,y)
           elif overlay.overlayType == self.LINE:
               painter.drawLine(x,y,x + w,y + h)
           elif overlay.overlayType == self.TEXT:
               painter.drawText(x, y, overlay.text)
               
               
       ##################### Draw dragging ROI    
       if self.dragging and self.dragX != self.dragToX and self.dragY != self.dragToY:
           painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
          
           dragRoi = int(round(min(self.dragX, self.dragToX))), int(round(min(self.dragY, self.dragToY))), int(round(max(self.dragX, self.dragToX))), int(round(max(self.dragY, self.dragToY)))

           drawX, drawY = self.screen_coords(dragRoi[0], dragRoi[1])
           endX, endY = self.screen_coords(dragRoi[2], dragRoi[3])
           width = endX- drawX
           height = endY - drawY

           painter.setPen(self.roiDragContrastPen)
           painter.drawRect(drawX, drawY, width + 1, height + 1)
           painter.setPen(self.roiDragPen)
           painter.drawRect(drawX, drawY, width + 1, height + 1)
           
                
           
           
       ##################### Draw active ROI 
       if self.roi is not None:
           drawX, drawY = self.screen_coords(self.roi[0], self.roi[1])
           endX, endY = self.screen_coords(self.roi[2], self.roi[3])
           width = endX- drawX
           height = endY - drawY
           painter.setPen(self.roiContrastPen)
           painter.drawRect(drawX, drawY, width + 1, height + 1)
           painter.setPen(self.roiPen)
           painter.drawRect(drawX, drawY, width + 1, height + 1)

          
       # Stop clipping because now we want to draw status bar which is outside image
       painter.setClipRect(QRect(*self.screen_offsets(), self.screen_size()[0],100000))
       
       
       ##################### Draw Zoom Indicator ############
       if self.zoomLevel > 0 and self.isZoomIndicator:

           painter.setPen(self.zoomIndicatorPen)
           
           if self.imageHeight < self.imageWidth:
               x = self.width() - (self.width() - self.pmap.width()) / 2 - self.zoomIndicatorOffsetX - self.zoomIndicatorWidth
               y = (self.height() - self.pmap.height()) / 2 + self.zoomIndicatorOffsetY
               w = self.zoomIndicatorWidth
               h = self.imageSize[0] / self.imageSize[1] * w
           else:
               x = self.width() - (self.width() - self.pmap.width()) / 2 - self.zoomIndicatorOffsetX 
               y = (self.height() - self.pmap.height()) / 2 + self.zoomIndicatorOffsetY
               h = self.zoomIndicatorWidth
               w = self.imageSize[1] / self.imageSize[0] * h
               
           # Outer rect
           painter.drawRect(int(x), int(y), int(w), int(h)) 
           
           # Filled inner rect
           x2 = round(self.displayX / self.imageSize[1] * (w- 2))
           y2 = round(self.displayY / self.imageSize[0] * (h - 2))
           w2 = round(self.displayW / self.imageSize[1] * (w - 2) + 1)
           h2 = round(self.displayH / self.imageSize[0] * (h - 2) + 1)
           w2 = min(w - x2, w2 - x2) + x2
           h2 = min(h - y2, h2 - y2) + y2
         
           painter.setBrush(self.zoomIndicatorBrush)
           painter.drawRect(int(x + x2), int(y + y2), int(w2), int(h2))  

      
       ##################### Draw status bar 
       if self.isStatusBar and self.pmap is not None:
       
           font = painter.font()
           fm = QFontMetrics(font)
           if self.mouseX is not None and self.mouseY is not None and self.currentImage is not None:
               try:
                   mX = str(round(self.mouseX))
                   mY = str(round(self.mouseY))
                   if self.imageMode == self.MONO:
                       cursorVal = str(int(round(self.currentImage[round(self.mouseY), round(self.mouseX)],1)))
                   elif self.imageMode == self.RGB:
                       cursorVal = str(int(round(self.currentImage[round(self.mouseY), round(self.mouseX),0],0))) \
                                   + "," + str(int(round(self.currentImage[round(self.mouseY), round(self.mouseX),1],0))) \
                                   + "," + str(int(round(self.currentImage[round(self.mouseY), round(self.mouseX),2],0)))
                  
                   else:
                       cursorVal = '--'
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
               
           if self.currentImage is not None and self.roi is not None and self.roi is not []:
               roi = self.currentImage[self.roi[1] : self.roi[3], self.roi[0]: self.roi[2],...]
               self.roiMax = str(round(np.max(roi)))
               self.roiMin = str(round(np.min(roi)))
               self.roiMean = str(round(np.mean(roi),1))               
           
           if self.zoomLevel > 0:
               text = str(round(2**(self.zoomLevel))) + 'X '
           else:
               text = ''
               
           if self.imageMode is not self.GRAPH:    
               text = text + '(' + mX + ',' + mY + ') = ' + cursorVal + ' | [' + self.minPixel + '-' + self.maxPixel + ', Mean: ' + self.meanPixel + ']'
           
               if self.roi is not None:
                   text = text + ' | [ROI: (' + str(self.roi[0] ) + ',' + str(self.roi[1]) + ')-(' + str(self.roi[2] -1) + '-' + str(self.roi[3] -1) + '): ' + self.roiMin + '-' + self.roiMax + ', Mean: ' + self.roiMean + ']' 
            
               elif self.dragging and self.dragX != self.dragToX and self.dragY != self.dragToY:
                   text = text + ' | [Dragging ROI: (' + str(dragRoi[0]) + ',' + str(dragRoi[1] ) + ')-(' + str(dragRoi[2] -1) + '-' + str(dragRoi[3] -1) + ') ]'
           else: #GRAPH
               if self.mouseX is not None and self.mouseY is not None:
                   xP =  str(round(int(self.mouseX / self.graph_width * num_points) ))
                   yP =  str(round(self.graphData[int(self.mouseX / self.graph_width * num_points) ],3))
    
                   prec = 3
                   text = text + '(' + xP + ',' + yP + ') | [' + str(round(np.min(self.graphData),prec)) + ' -> ' + str(round(np.max(self.graphData),prec)) + ', Mean: ' + str(round(np.mean(self.graphData),prec)) + ']'
                    
                   x,y = self.screen_coords(self.mouseX,plotY[int(self.mouseX* num_points / self.graph_width)])
                   painter.setBrush(self.graphCursorBrush)
                   painter.setPen(self.graphCursorPen)
                   painter.drawEllipse(x-self.graphCursorSize,y -self.graphCursorSize, self.graphCursorSize * 2,self.graphCursorSize *2)

           xPos = int(round((self.width() - self.pmap.width()) /2))
           painter.setBrush(self.statusBrush)
           painter.setPen(self.statusPen)
           painter.drawRect(int(xPos + 1), int(self.height() - fm.height() - 5), int(self.pmap.width() - 2), int(fm.height() + 8))
           painter.setPen(self.statusTextPen)
           painter.drawText(int(xPos + 10), int(self.height() - 6), text)
          
       self.update() 
        
   def add_overlay(self, overlayType, *args):
       """ Adds an overlay to the list of visible overlays. overlayType can be ELLIPSE, RECTANGLE, POINT or LINE.
       add_overlay(ImageDisplay.ELLIPSE, x, y, width, height, pen, fill)
       add_overlay(ImageDisplay.RECTANGLE, x, y, width, height, pen, fill)
       add_overlay(ImageDisplay.LINE, x, y, width, height, pen, fill)
       add_overlay(ImageDisplay.POINT, x, y, pen, fill)
       add_overlay(ImageDisplay.TEXT, x, y, pen, text)       
       """       
       x = args[0]
       y = args[1]
       text = ''
       
       if overlayType == self.ELLIPSE or overlayType == self.RECTANGLE:
           w = args[2]
           h = args[3]
           pen = args[4]
           fill = args[5]
    
       elif overlayType == self.LINE:
           w = args[2]
           h = args[3]
           pen = args[4]
           fill = None
                    
       elif overlayType == self.POINT:
           w = 1
           h = 1
           pen = args[2]
           fill = None
      
           
       elif overlayType == self.TEXT:
           w = 1
           h = 1
           pen = args[2]
           fill = None
           text = args[3]
           
       else:
           overlayType = None
       
       if overlayType is not None:
           newOverlay = Overlay(overlayType, x, y, w, h, pen, fill, text)
           self.overlays.append(newOverlay)
           return newOverlay
       else:
           return None
       
   
   def remove_overlay(self, overlay):
       """ Removes overlay 'overlay' from the list of visible overlays
       """
       self.overlays.remove(overlay)
       self.update()
         
           
   def clear_overlays(self):
       """ Removes all overlays from the list of visible overlays
       """
       self.overlays = []
       self.update()
           
   
   def num_overlays(self):
       """ Returns the number of overlays in the list of visible overlays
       """
       return len(self.overlays)
   
    
   def set_auto_scale(self, autoScale):
       """ Determines whether or not images are brightness/contrast autoscaled to use the full dynamic range. True or False.
       """
       self.autoScale = autoScale
       self.update()
       
       
   def set_status_bar(self, isStatusBar):
       """ Set status bar visible (True) or hidden (False).
       """
       self.isStatusBar = isStatusBar
       self.update()
       
    
   def set_zoom_enabled(self, isZoomEnabled):
       """ Set whether zoom using mouse wheel is possible (True) or not (False).
       """
       self.isZoomEnabled = isZoomEnabled
       if not isZoomEnabled:
           self.zoomLevel = 0
       self.set_image(self.currentImage)
       self.update()

   def set_zoom_indicator_enabled(self, isIndicatorEnabled):
       """ Set whether the zoom indicator is shown (True) or not (False).
       """
       self.isZoomIndicator = isIndicatorEnabled
       self.set_image(self.currentImage)
       self.update()
       
    
   def set_roi_enabled(self, isRoiEnabled):
       """ Set whether zoom using mouse wheel is possible (True) or not (False).
       """
       self.isRoiEnabled = isRoiEnabled
       if not self.isRoiEnabled:
           self.roi = None
       self.update()
         
    
   def set_colormap(self, colormapName):
       """ Sets the colormap using a matplotlib colormap. Provide the colormap as a string containing the anme of the colormap.
       """

       if colormapName is None:
           self.colortable = None
       else:   
           colormap = cm.get_cmap(colormapName) 
           colormap._init()
           lut = (colormap._lut * 255).view(np.ndarray).astype('int16')  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
           lut = lut[:256,0:3]
           nCols = np.shape(lut)[0]   # Seem to be 513 x 4
               
           self.colortable = []
           for i in range(0, 256):
               col = int(round(i * nCols / 256))
               self.colortable.append(QtGui.qRgb(lut[col,0],lut[col,1],lut[col,2]))
       self.update()
       
       
   def set_display_range(self, lower, upper):
       """ Sets the intensity range used for display if set_auto_scale is False. Pixels
       of 'lower' or below will be mapped to 0, 'upper' and above to 255.
       """
       self.displayMin = lower
       self.displayMax = upper
       self.update()
       

   def get_display_range(self):
       """ Gets the intensity range used for display if set_auto_scale is False. Return
       a tuple of (lower, upper).
       Pixels of 'lower' or below will be mapped to 0, 'upper' and above to 255.
       """
       return self.displayMin, self.displayMax
   
       
   def set_zoom_step_divider(self, zoomDivider):
       """ Sets the zoom step divider. A bigger value makes the amount zoomed
       in by each mouse wheel step smaller.
       """
       if zoomDivider > 0:       
           self.zoomStepDivider = zoomDivider
           
         
class Overlay():
    """ Class to store details about an overlay.
    """
    
    x1 = None  
    x2 = None
    y1 = None
    y2 = None
    pen = None
    fill = None
    overlayType = None
    text = None
    
    def __init__(self, overlayType, x1, y1, x2, y2, pen, fill, text):

        self.overlayType = overlayType
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.pen = pen
        self.fill = fill
        self.text = text