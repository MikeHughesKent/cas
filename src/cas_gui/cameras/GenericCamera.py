# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Generic camera interface for Camera Acquisition Based GUIs. Other
cameras should inherit from this and implement whatever methods
are required.

"""
                
        
class GenericCameraInterface:
    
    camera_open = False
    
    def __init__(self):        
        pass            
        
    def get_camera_list(self):
        pass        
        
    def open_camera(self, camID):
        pass            
                
    def close_camera(self):
        pass
        
    def dispose(self):
        pass
               
    def get_image(self):
        pass
        
    def is_camera_open(self):
        return self.camera_open
    
    ##### Parameter Value Setting    
    def get_nodes(self):
        return None
                
    def get_values(self, nodeName):
        return None
        
    def set_value(self, nodeName, value):
        return False
    
    def get_value(self, nodeName):
        return None
                    
    def get_nodes(self):
        return None    
    
    ###### Frame Rate
    def set_frame_rate_on(self):
        return None        

    def set_frame_rate(self, fps):
        return None 
    
    def get_frame_rate(self):
        return 0 
    
    def get_frame_rate_range(self):
        return (0,0)         
    
    def is_frame_rate_enabled(self):
        return False
    
    def get_measured_frame_rate(self):
        return 0 


    ##### Exposure
    def is_exposure_enabled(self):
        return False

    def set_exposure(self, exposure):
        return None       
        
    def get_exposure(self):
        return 0
    
    def get_exposurerange(self):
        return (0,0) 
    
        
    ##### Gain    
    def is_gain_enabled(self):
        return False
        
    def set_gain(self, gain):
        return None 
    
    def get_gain(self):
        return 0 
    
    def get_gain_range(self):
        return (0,0) 
        
    ##### Trigger
    
    def set_trigger_mode(self, triggerMode):
        pass
        
    def set_image(self):
        pass
    
    def set_file(self):
        pass
    
    
    def is_colour(self):
        return False
    
    
    #### Working with Files
    
    def set_image_idx(self, idx):
        pass
    
    def get_number_images(self):
        return 1

if __name__ == "__main__":
    print("Test mode not implemented")