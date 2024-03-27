# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System
Generic camera interface for Camera Acquisition Based GUIs.

Mike Hughes, Applied Optics Group, University of Kent

"""
  
from instrumental import instrument, list_instruments
from instrumental.drivers.cameras import uc480
   
        
class DCXCameraInterface:
    
    def __init__(self):    
        pass
            
        
    def get_camera_list(self):
        pass        
        
    def open_camera(self, camID):
        instruments = uc480.list_instruments()
        self.cam = uc480.UC480_Camera(instruments[0]) 

        #print(dir(self.cam))
        self.cam.pixelclock = '35 MHz'
        self.cam.start_live_video(exposure_time='2 ms')

                
    def close_camera(self):
        del(self.cam)
        pass
        
    def dispose(self):
        pass
               
    def get_image(self):
        self.cam.wait_for_frame()
        
        return self.cam.latest_frame()
    
    
    
    
    ###### Frame Rate

    def set_frame_rate_on(self):
        return None        

    def set_frame_rate(self, fps):
        #print('Trying to set frame rate to:', fps)
        frompsOut = self.cam._dev.SetFrameRate(fps)
        #print('Frame rate is now:', self.get_frame_rate())


        return True 
    
    def get_frame_rate(self):
        #print("Reprting frame rate as", self.cam.framerate.magnitude)
        return self.cam.framerate.magnitude 
    
    def get_frame_rate_range(self):
        return 0.1, 25   
    
    def is_frame_rate_enabled(self):
        return True 
    
    def get_measured_frame_rate(self):
        return None 



    ##### Exposure
    def is_exposure_enabled(self):
        return True

    def set_exposure(self, exposure):
        self.cam._set_exposure(str(exposure) + ' ms')
        #print(str(exposure) + ' ms')
        return True       
        
    def get_exposure(self):
        return self.cam._get_exposure().magnitude
 
    
    def get_exposure_range(self):
        #print("Min, Max Exposure: ", self.cam._get_exposure_inc().magnitude, 950/self.cam.framerate.magnitude)
        return self.cam._get_exposure_inc().magnitude, 950/self.cam.framerate.magnitude
    
        
    ##### Gain    
    def is_gain_enabled(self):
        return True
        
    def set_gain(self, gain):
        self.cam.master_gain = gain
        return True
    
    def get_gain(self):
        return self.cam.master_gain
    
    def get_gain_range(self):
        return 1, self.cam.max_master_gain
        
        

if __name__ == "__main__":
    cam= DCXCameraInterface()
    cam.open_camera(1)
    print(cam.cam._get_exposure().magnitude)
    print(cam.cam._get_exposure())
    cam.cam.master_gain = 3
    print(cam.cam.master_gain)
    cam.close_camera()
    
