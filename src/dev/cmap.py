# -*- coding: utf-8 -*-
"""
Created on Thu Aug  4 16:28:39 2022

@author: AOG
"""

from matplotlib import pyplot
from matplotlib import cm
import numpy as np
colormap = cm.get_cmap("twilight_shifted")  # cm.get_cmap("CMRmap")
colormap._init()
lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
#lut = lut[0:256,0:3]
           
#colortable = []
#for i in range(0, 255):
#    colortable[i] = QtGui.qRgb(lut[i,0],lut[i,1],lut[i,2])
    
