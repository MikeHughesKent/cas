# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Threading class for image acqusition and buffering for use in GUIs or or 
multi-threading applications.

@author: Mike Hughes
Applied Optics Group
University of Kent
"""

import queue
import threading
import time
import multiprocessing as mp

class ImageAcquisitionThread(threading.Thread):
    
    def __init__(self, camName, bufferSize, **camArgs):
        
        # Caller passes the name of the camera class (which should be in a
        # module of the same name) in the variable camName. This is dynamically
        # imported here and an instance created as self.cam.
        camModule = __import__(camName)
        self.cam = getattr(camModule, camName)(**camArgs)
        
        super().__init__()
                
        self.cam.open_camera(0)
        self._stop_event = threading.Event()
        
        self.bufferSize = bufferSize
                
        self.imageQueue = mp.Queue(maxsize=self.bufferSize)
        
        self.lastFrameTime = 0
        self.frameStepTime = 0
        self.currentFrame = None
        self.currentFrameNumber = 0
        self.isPaused = False
        self.isOpen = True
        
    def get_camera(self):
        return self.cam
    
    def get_image_queue(self):
        return self.imageQueue
    
    def get_num_images_in_queue(self):
        return self.imageQueue.qsize()
    
    def is_image_ready(self):
        if self.get_num_images_in_queue() > 0:
            return True
        else:
            return False
    
    def get_next_image(self):
        if self.is_image_ready():
            try:
                im = self.imageQueue.get()
            except queue.Empty:
                print("Error - no image")
                return None
        
            return im
        else:
            return None
    
    def get_next_image_wait(self):
        
        while self.is_image_ready() is False:
            pass
        try:
            im = self.imageQueue.get()
        except queue.Empty:
            print("Error - no image")
            return None
        
        return im
        
    
    def get_inter_frame_time(self):
        return self.frameStepTime
    
    def get_actual_fps(self):
        if self.frameStepTime > 0:
            return (1 / self.frameStepTime)
        else:
            return 0
        
    def get_latest_image(self):
        return self.currentFrame
    
    
    def flush_buffer(self):
        while not self.imageQueue.empty():
            try:
                self.imageQueue.get_nowait()  
            except:
                pass
            
    
    def run(self):
        while self.isOpen:            

            if not self.isPaused:
                if self.imageQueue.full():
                    if self.imageQueue.qsize() > 0:
                        temp = self.imageQueue.get()
                    if self.imageQueue.qsize() > 0:
                        temp = self.imageQueue.get()

                    t1 = time.time()
                t1 = time.perf_counter()    
                frame = self.cam.get_image()
                #print("Get image time: " + str(time.perf_counter() - t1))
                #
                if frame is not None:
                    self.currentFrameNumber = self.currentFrameNumber + 1
                    self.imageQueue.put(frame)
                    self.currentFrame = frame
                    self.currentFrameTime = time.perf_counter()
                    self.frameStepTime = self.currentFrameTime - self.lastFrameTime
                    self.lastFrameTime = self.currentFrameTime
                    #print(self.frameStepTime)
                
    def pause(self):
        self.isPaused = True
        return

    def resume(self):
        self.isPaused = False
        return            
              
    def stop(self):
        self.isOpen = False
        time.sleep(0.5)
        self.cam.close_camera()
        self.cam.dispose()
        del(self.cam)