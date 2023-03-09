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
    
    def __init__(self, camName, bufferSize, acquisitionLock, **camArgs):
        
        # Caller passes the name of the camera class (which should be in a
        # module of the same name) in the variable camName. This is dynamically
        # imported here and an instance created as self.cam.
        camModule = __import__(camName)
        self.cam = getattr(camModule, camName)(**camArgs)
        self.acquisitionLock = acquisitionLock
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
        
        self.numRemoveWhenFull = 1
        
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
            print(self.is_image_ready())

            pass
        try:
            if self.acquisitionLock is not None: self.acquisitionLock.acquire()
            im = self.imageQueue.get()
            if self.acquisitionLock is not None: self.acquisitionLock.release()

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
    
    def set_num_removal_when_full(self, num):
        self.numRemoveWhenFull = num
    
    
    def flush_buffer(self):
        while not self.imageQueue.empty():
            try:
                self.imageQueue.get_nowait()  
            except:
                pass
            
    
    def run(self):
        while self.isOpen:            

            if not self.isPaused:
                
                # Handles full queue
                if self.imageQueue.full():
                    if self.acquisitionLock is not None: self.acquisitionLock.acquire()

                    for idx in range(self.numRemoveWhenFull):
                        if self.imageQueue.qsize() > 0:
                            temp = self.imageQueue.get()
                           
                    if self.acquisitionLock is not None: self.acquisitionLock.release()

                frame = self.cam.get_image()

                if frame is not None:
                    #print("running")
                    self.currentFrameNumber = self.currentFrameNumber + 1
                    self.imageQueue.put(frame)
                    self.currentFrame = frame
                    self.currentFrameTime = time.perf_counter()
                    self.frameStepTime = self.currentFrameTime - self.lastFrameTime
                    self.lastFrameTime = self.currentFrameTime

                
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