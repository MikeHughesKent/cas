# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System
Camera interface for Flea Camera.

Mike Hughes, Applied Optics Group, University of Kent

"""
  

from GenericCamera import GenericCameraInterface
 
import PySpin

import time

       
class FleaCameraInterface(GenericCameraInterface):
    
    def __init__(self):        
        self.system = PySpin.System.GetInstance()
        self.camList = self.system.GetCameras()
        self.nCameras = self.camList.GetSize()
        
        self.cams = self.camList
            
        
    def get_camera_list(self):
        return self.system.GetCameras()
        
        
    def open_camera(self, camID):
        
        if len(self.cams) > camID:
            
            self.cam = self.cams[camID]
            
            # Retrieve TL device nodemap and print device information
            nodemap_tldevice = self.cam.GetTLDeviceNodeMap()
    
            #result &= FleaCamera.print_device_info(nodemap_tldevice)
    
            # Initialize camera
            self.cam.Init()
    
            # Retrieve GenICam nodemap
            nodemap = self.cam.GetNodeMap()
            
            nodemap_tldevice = self.cam.GetTLDeviceNodeMap()    
            
            node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                return False
    
            # Retrieve entry node from enumeration node
            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
                print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                return False
    
            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
    
            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
            
            self.cam.BeginAcquisition()
            
            
            return self.cam
        else:
            print("Camera not available.")
            return False

                
    def close_camera(self):
        
        self.cam.EndAcquisition()
        self.cam.DeInit()
        
    def dispose(self):
        
        # Clear camera list before releasing system
        self.camList.Clear()

        # Release system instance
        self.system.ReleaseInstance()
        
               
    def get_image(self):
        image = self.cam.GetNextImage(10000)
        if image.IsIncomplete():
            print('Image incomplete with image status %d ...' % image.GetImageStatus())


        #result &= acquire_images(cam, nodemap, nodemap_tldevice)
        imageData = image.GetNDArray()

        #cv.imshow("Camera Stream", cv.resize(self.imageData,(300,300)))
        #cv.waitKey(1)
        
        return imageData
    
    
    
    
    ###### Frame Rate

    def set_frame_rate_on(self):
        nodemap = self.cam.GetNodeMap()
        node = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionFrameRateAuto"))
        node.SetIntValue(0)
        return True        

    def set_frame_rate(self, fps):
        self.set_frame_rate_on()
        if self.cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
            self.cam.AcquisitionFrameRate.SetValue(fps)
            return True
        else:
            print("Auto FPS")
            return False 
    
    def get_frame_rate(self):
        return self.cam.AcquisitionFrameRate.GetValue()

    
    def get_frame_rate_range(self):
        return self.cam.AcquisitionFrameRate.GetMin(), self.cam.AcquisitionFrameRate.GetMax()         
    
    def is_frame_rate_enabled(self):
        print(self.cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW)
        return (self.cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW )
    
    def get_measured_frame_rate(self):
        return None 



    ##### Exposure
    def is_exposure_enabled(self):
        return False

    def set_exposure(self, exposure):
        self.cam.ExposureAuto.SetValue(0)
        
        if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
            self.cam.ExposureTime.SetValue(exposure)
            return True
        else:
            return False             
        
    def get_exposure(self):
        return self.cam.ExposureTime.GetValue() 
    
    def get_exposure_range(self):
        return self.cam.ExposureTime.GetMin(), self.cam.ExposureTime.GetMax()
 
    
        
    ##### Gain    
    def is_gain_enabled(self):
        return False
        
    def set_gain(self, gain):
        self.cam.GainAuto.SetValue(0)

        if self.cam.Gain.GetAccessMode() == PySpin.RW:
            self.cam.Gain.SetValue(gain)
            return True
        else:
            return False 
    
    def get_gain(self):
        return self.cam.Gain.GetValue() 
    
    def get_gain_range(self):
        return self.cam.Gain.GetMin(), self.cam.Gain.GetMax()
        
        

if __name__ == "__main__":
    cams = FleaCameraInterface()
    cams.init()
    cam = cams.open(0)
    if cam != False:
    
        cam.set_frame_rate(60)
        print(cam.get_exposure())
        print(cam.get_frame_rate())
        t1 = time.time()
        for i in range(120):
            im = cam.get_image()
        t2 = time.time()
        print(t2-t1)
        cam.dispose()  
        del(cam)
    cams.deInit()
