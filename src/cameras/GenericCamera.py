# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System
Generic camera interface for Camera Acquisition Based GUIs.

Mike Hughes, Applied Optics Group, University of Kent

"""
  
                
        
class GenericCameraInterface:
    
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
    
    
    
    
    ###### Frame Rate

    def set_frame_rate_on(self):
        return None        

    def set_frame_rate(self, fps):
        return None 
    
    def get_frame_rate(self):
        return None 
    
    def get_frame_rate_range(self):
        return None         
    
    def is_frame_rate_enabled(self):
        return None 
    
    def get_measured_frame_rate(self):
        return None 



    ##### Exposure
    def is_exposure_enabled(self):
        return False

    def set_exposure(self, exposure):
        return None       
        
    def get_exposure(self):
        return None 
    
    def get_exposurerange(self):
        return None 
    
        
    ##### Gain    
    def is_gain_enabled(self):
        return False
        
    def set_gain(self, gain):
        return None 
    
    def get_gain(self):
        return None 
    
    def get_gain_range(self):
        return None 
        
      
        
    def set_image(self):
        pass
    
    def set_file(self):
        pass

if __name__ == "__main__":
    print("Test mode not implemented")