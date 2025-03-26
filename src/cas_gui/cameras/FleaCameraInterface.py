# -*- coding: utf-8 -*-
"""
CAS: Camera Acquisition System

Camera interface for Flea Cameras (may also work for other FLIR cameras).

"""

import time
import warnings

import PySpin

from cas_gui.cameras.GenericCamera import GenericCameraInterface  
 

class FleaCameraInterface(GenericCameraInterface):
    
    _rw_modes = {
        PySpin.RO: "read only",
        PySpin.RW: "read/write",
        PySpin.WO: "write only",
        PySpin.NA: "not available"
    }

    _attr_types = {
        PySpin.intfIFloat: PySpin.CFloatPtr,
        PySpin.intfIBoolean: PySpin.CBooleanPtr,
        PySpin.intfIInteger: PySpin.CIntegerPtr,
        PySpin.intfIEnumeration: PySpin.CEnumerationPtr,
        PySpin.intfIString: PySpin.CStringPtr,
    }

    _attr_type_names = {
        PySpin.intfIFloat: 'float',
        PySpin.intfIBoolean: 'bool',
        PySpin.intfIInteger: 'int',
        PySpin.intfIEnumeration: 'enum',
        PySpin.intfIString: 'string',
        PySpin.intfICommand: 'command',
    }
    
    
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
            
            # Initialize camera
            self.cam.Init()
    
            self.set_value('AcquisitionMode', 'Continuous')
            
            self.cam.BeginAcquisition()            
            
            self.camera_open = True
        
            return self.cam

        else:

            return False

                
    def close_camera(self):
        
        self.cam.EndAcquisition()
        self.cam.DeInit()
        
        
    def set_value(self, nodeName, value):
        """ Writes a value to node.
        """
        
        nodemap = self.cam.GetNodeMap()        
        nodemap_tldevice = self.cam.GetTLDeviceNodeMap()  
        
        # Reference to node
        node = PySpin.CEnumerationPtr(nodemap.GetNode(nodeName))

        # Check node is writeable
        if not PySpin.IsAvailable(node) or not PySpin.IsWritable(node):
            return False
        
        # Get value we want to set
        nodeEntry = node.GetEntryByName(value)
        
        # Check this value can be written
        if not PySpin.IsAvailable(nodeEntry) or not PySpin.IsReadable(nodeEntry):
            return False
        
        nodeEntryValue = nodeEntry.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node.SetIntValue(nodeEntryValue)
        
        return True
    
    
    def get_nodes(self):
        
        for node in self.cam.GetNodeMap().GetNodes():
            pit = node.GetPrincipalInterfaceType()
            name = node.GetName()
            self.camera_node_types[name] = self._attr_type_names.get(pit, pit)
            if pit == PySpin.intfICommand:
                self.camera_methods[name] = PySpin.CCommandPtr(node)
            if pit in self._attr_types:
                self.camera_attributes[name] = self._attr_types[pit](node)
        
        
        
    def get_values(self, nodeName):
        """ Returns list of possible values to set for a node """
        
        nodemap = self.cam.GetNodeMap()        
        nodemap_tldevice = self.cam.GetTLDeviceNodeMap()  
        
        # Reference to node
        node = PySpin.CEnumerationPtr(nodemap.GetNode(nodeName))
        
        entryNames = []
        if hasattr(node, 'GetEntries'):
            for entry in node.GetEntries():
                entryNames.append(entry.GetName().split('_')[-1])   
            return entryNames
        else:
            return None
        
    
    def get_value(self, nodeName):
        """ Gets the value set for a node"""
        
        nodemap = self.cam.GetNodeMap()        
        nodemap_tldevice = self.cam.GetTLDeviceNodeMap()  
        
        # Reference to node
        node = PySpin.CEnumerationPtr(nodemap.GetNode(nodeName))
        
        
            
        if hasattr(node, "GetValue"):
            return node.GetValue()
        elif hasattr(node, "ToString"):
           return node.ToString()
        else:
            return None
        
        
    
    def get_nodes(self):
        """ Returns a list of nodes """
        
        nodes = []
        for node in self.cam.GetNodeMap().GetNodes():
            nodes.append(node.GetName())
         
        nodes.sort()    
        
        return nodes
        
       
    def dispose(self):
        del self.cam 
        
        # Clear camera list before releasing system
        self.camList.Clear()

        # Release system instance
        self.system.ReleaseInstance()
        
        
               
    def get_image(self, timeout = 10000):
        try:
            image = self.cam.GetNextImage(timeout)
        except:
            image = None
        
        if  image is None:
            return None
        else:
            imageData = image.GetNDArray()
            return imageData
    
    
    
    
    ###### Frame Rate

    def set_frame_rate_on(self):
        """ Enables or disables frame rate control """

        
        try:
            nodemap = self.cam.GetNodeMap()
            node = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionFrameRateAuto"))
            node.SetIntValue(0)
            return True  
        except:
            return False
        
        
    def set_trigger_mode(self, enabled):
        """ Enables or disables trigger mode """
        
        if enabled:
            return self.set_value('TriggerMode', 'On')
        else:
            return self.set_value('TriggerMode', 'Off')


    def set_frame_rate(self, fps):
                
        # Make sure auto frame rate is disabled, will return false if can't turn off 
        # auto frame rate
        success = self.set_frame_rate_on()
        
        try:                
            if self.cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
                self.cam.AcquisitionFrameRate.SetValue(fps)
                return True
        except:
                print("Can't set frame rate, in automatic frame rate mode.")
                return False    
    
    
    def get_frame_rate(self):
        
        if self.is_frame_rate_enabled():
            return self.cam.AcquisitionFrameRate.GetValue()
        else:
            return 0

    
    def get_frame_rate_range(self):
        
        return self.cam.AcquisitionFrameRate.GetMin(), self.cam.AcquisitionFrameRate.GetMax()      
    
    
    def is_frame_rate_enabled(self):
        
        return (self.cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW )
    
       
    def get_measured_frame_rate(self):
        
        return None 


    ##### Exposure
    def is_exposure_enabled(self):
        return False

    def set_exposure(self, exposure):
        
        # Ensure auto exposure is off
        self.cam.ExposureAuto.SetValue(0)
        
        if exposure < self.get_exposure_range()[0]: 
            exposure = self.get_exposure_range()[0]
            warnings.warn(f"Set exposure limited to minimum allowed value of {self.get_exposure_range()[0]}.")
        if exposure > self.get_exposure_range()[1]: 
            exposure = self.get_exposure_range()[1]
            warnings.warn(f"Set exposure limited to maximum allowed value of {self.get_exposure_range()[1]}.")
        
        if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
            try:
                self.cam.ExposureTime.SetValue(exposure)
                return True
            except:
                return False
                print(f"FleaCameraInterface: Cannot set exposure value of {exposure} us.")
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
        
        # Ensure auto gain is off
        self.cam.GainAuto.SetValue(0)  
        
        if gain < self.get_gain_range()[0]: 
            gain = self.get_gain_range()[0]
            warnings.warn(f"Set gain limited to minimum allowed value of {self.get_gain_range()[0]}.")
        if gain > self.get_gain_range()[1]: 
            gain = self.get_gain_range()[1]
            warnings.warn(f"Set gain limited to maximum allowed value of {self.get_gain_range()[1]}.")

        if self.cam.Gain.GetAccessMode() == PySpin.RW:
            try:
                self.cam.Gain.SetValue(gain)
                return True
            except:
                return False

            return True
        else:
            return False 
        

    
    def get_gain(self):
        return self.cam.Gain.GetValue() 
    
    
    def get_gain_range(self):
        return self.cam.Gain.GetMin(), self.cam.Gain.GetMax()
        
        

if __name__ == "__main__":
    
    ### Performs a test acquisition
    cams = FleaCameraInterface()
    cams.init()
    cam = cams.open(0)
    
    if cam != False:
    
        cam.set_frame_rate(60)
        print(f"Exposure: {cam.get_exposure()}")
        print(f"Frame Rate: {cam.get_frame_rate()}")
        t1 = time.time()
        for i in range(120):
            im = cam.get_image()
        t2 = time.time()
        print(f"Time to get 120 frames: {t2-t1}")
        cam.dispose()  
        del(cam)
    
    cams.deInit()
