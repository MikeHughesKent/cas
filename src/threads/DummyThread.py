# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 17:46:33 2022

@author: AOG
"""

from ImageProcessorThread import ImageProcessorThread

class DummyThread(ImageProcessorThread):
    
    def get_image_queue(self):
        return None