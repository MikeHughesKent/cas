# -*- coding: utf-8 -*-
"""
CAS: Camera Acquisition System

Camera interface for Flea Cameras (may also work for other FLIR cameras).

"""

import cv2 as cv
import time
import sys

import os

path = os.path.split(__file__)[0] + r"\thorlab"
sys.path.append(path)

from cas_gui.cameras.thorlab.tl_camera import TLCameraSDK, TLCamera, Frame
from cas_gui.cameras.thorlab.tl_camera_enums import SENSOR_TYPE
from cas_gui.cameras.thorlab.tl_mono_to_color_processor import MonoToColorProcessorSDK
import numpy as np
from cas_gui.cameras.GenericCamera import GenericCameraInterface  
    
        
class KiraluxCamera(GenericCameraInterface):
    
    def __init__(self):
        
        self.sdk = TLCameraSDK()
            
        
    def get_camera_list(self):
        cameraList = self.sdk.discover_available_cameras()
        return cameraList
        
        
    def open_camera(self, camNum):
        cameraList = self.sdk.discover_available_cameras()
        self.camera = self.sdk.open_camera(cameraList[camNum]) 
        self.camera.frames_per_trigger_zero_for_unlimited = 0
        self.camera.arm(2)
        self.camera.issue_software_trigger()
        self.camera_open = True
        
        
    def close_camera(self):

        self.camera.dispose()
        
    def dispose(self):
        del(self.sdk)
               
        
    def get_image(self):
        
        self.frame = self.camera.get_pending_frame_or_null()
        if self.frame is not None:
            imageData = self.frame.image_buffer >> (self.camera.bit_depth - 8)
        else:
            imageData = None
        return imageData


   
    def set_frame_rate_on(self):
       
        return True
        

    def set_framerate(self, fps):
        self.is_frame_rate_control_enabled = True
        self.camera.frame_rate_control_value = fps
    
    def get_frame_rate(self):
        return self.camera.frame_rate_control_value
    
    def get_frame_rate_range(self):
        r = self.camera.frame_rate_control_value_range
        return r.min, r.max
    
    def get_measured_frame_rate(self):
        return self.camera.get_measured_frame_rate_fps()
        
        
    def is_frame_rate_enabled(self):
        min, max = self.get_frame_rate_range()
        if max <= 0:
            return False
        else:
            return True
        
    def set_exposure(self, exposure):
        self.camera.exposure_time_us = int(exposure)
        
        return True      
        
    def get_exposure(self):
        return self.camera.exposure_time_us
    
    def get_exposure_range(self):
        r = self.camera.exposure_time_range_us
        
        return r.min, r.max

       
       
    def set_gain(self, gain):
        self.camera.gain = gain
        return True
    
    def get_gain(self):
        return self.camera.gain
    

    def get_gain_range(self):
        r = self.camera.gain_range
        return r.min, r.max

        return True

        
        

if __name__ == "__main__":
    print("Test mode not implemented")