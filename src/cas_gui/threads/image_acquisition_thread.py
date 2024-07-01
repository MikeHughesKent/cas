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
import multiprocessing
from multiprocessing import shared_memory

import threading
import time
import importlib

class ImageAcquisitionThread(threading.Thread):
    
    def __init__(self, camName, bufferSize = 10, acquisitionLock = None, 
                 imageQueue = None, auxillaryQueue = None, **camArgs):
        
        # Caller passes the name of the camera class (which should be in a
        # module of the same name) in the variable camName. This is dynamically
        # imported here and an instance created as self.cam.
       # print(f"acq {inputQueue}")
        
        try:
            moduleName = "cas_gui.cameras." + camName
            print(moduleName)

            camModule = importlib.import_module(moduleName)

            self.cam = getattr(camModule, camName)(**camArgs)
        except:    
            moduleName = camName
            camModule = importlib.import_module(moduleName)

            self.cam = getattr(camModule, camName)(**camArgs)
            
            
            
        self.acquisitionLock = acquisitionLock
        super().__init__()
                
        self.cam.open_camera(0)
        self._stop_event = threading.Event()
        
        self.bufferSize = bufferSize
                
        self.imageQueue = imageQueue
        if self.imageQueue is None:
            self.imageQueue = multiprocessing.Queue(maxsize=self.bufferSize)
            
        self.auxillaryQueue = auxillaryQueue    
        if self.auxillaryQueue is None:
            self.auxillaryQueue = queue.Queue(maxsize=self.bufferSize)    
            
        self.numAuxillaryDroppedFrames = 0
        
        self.useAuxillaryQueue = False
        
        self.lastFrameTime = 0
        self.frameStepTime = 0
        self.currentFrame = None
        self.currentFrameNumber = 0
        self.isPaused = False
        self.isOpen = True
        #self.cam = None
        
        self.numRemoveWhenFull = 1
        self.numDroppedFrames = 0
        
        
    def run(self):
        """ The main loop. As long as the camera is open and we are not paused, we 
        first check that the queue is not full, and if so remove some images. Then
        we grab an image from the camera and add it to the queue. We also update some 
        records for calculating frame rate.
        """
        while self.isOpen:  

            if not self.isPaused:
                
                # Handles full queue
                if self.imageQueue.full():
                    if self.acquisitionLock is not None: self.acquisitionLock.acquire()

                    # Check for full queues
                    for idx in range(self.numRemoveWhenFull):
                        if self.imageQueue.qsize() > 0:
                            self.numDroppedFrames += 1
                            temp = self.imageQueue.get()
                            
                    if self.acquisitionLock is not None: self.acquisitionLock.release()
        
                
                if self.auxillaryQueue.full():
            
                    for idx in range(self.numRemoveWhenFull):
                        if self.auxillaryQueue.qsize() > 0:
                            self.numAuxillaryDroppedFrames += 1
                            temp = self.auxillaryQueue.get()        
                           

                # Try to get an image. If there is no image ready, this should
                # return None.
                frame = self.cam.get_image()

                if frame is not None:

                    self.currentFrameNumber = self.currentFrameNumber + 1
                    self.imageQueue.put(frame)
                    if self.useAuxillaryQueue:
                        self.auxillaryQueue.put(frame) 
                    self.currentFrame = frame
                    self.currentFrameTime = time.perf_counter()
                    self.frameStepTime = self.currentFrameTime - self.lastFrameTime
                    self.lastFrameTime = self.currentFrameTime
                else:
                    time.sleep(0.002)
            else:
                time.sleep(0.01)
        
    def get_camera(self):
        """ Returns a reference to the camera object.
        """
        return self.cam
    
    def get_image_queue(self):
        """ Returns a reference to the image output queue.
        """
        return self.imageQueue
    
    def get_num_images_in_queue(self):
        """ Returns the number of images in the output queue.
        """
        return self.imageQueue.qsize()
    
    
    def get_num_images_in_auxillary_queue(self):
        """ Returns the number of images in the auxillary queue.
        """
        return self.auxillaryQueue.qsize()
    
    
    def is_image_ready(self):
        """ Returns True if there is at least one image in the output queue.
        """
        if self.get_num_images_in_queue() > 0:
            return True
        else:
            return False
    
    def set_auxillary_queue_size(self, size):        
        """ Recreates auxillary queue with specified buffer size
        """
        self.auxillaryQueue = queue.Queue(maxsize = size)
        
        
    def is_auxillary_image_ready(self):
        """ Returns True if there is at least one image in the auxillary queue.
        """
        if self.get_num_images_in_auxillary_queue() > 0:
            return True
        else:
            return False    
    
    def get_next_image(self):
        """ Removes the next image from the queue and returns it.
        """
        if self.is_image_ready():
            try:
                im = self.imageQueue.get()
            except queue.Empty:
                print("Error - no image")
                return None
        
            return im
        else:
            return None
        
        
    def get_next_auxillary_image(self):
        """ Removes the next image from the auxillary queue and returns it.
        """
        if self.is_auxillary_image_ready():
            try:
                im = self.auxillaryQueue.get()
            except queue.Empty:
                print("Error - no image")
                return None
        
            return im
        else:
            return None    
    
    def get_next_image_wait(self):
        """ Wait until there is an image available in the queue and then return 
        it.
        """
        
        while self.is_image_ready() is False:
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
        """ Returns the time spacing between images being acquired (this should
        be inverse of frame rate).
        """
        return self.frameStepTime
    
    
    def get_actual_fps(self):
        """ Returns the observed frame rate.
        """
        if self.frameStepTime > 0:
            return (1 / self.frameStepTime)
        else:
            return 0
        
        
    def get_latest_image(self):
        """ Returns a reference to the latest image.
        """
        return self.currentFrame
    
    
    def set_num_removal_when_full(self, num):
        """ Sets the number of images to be removed from the queue when the
        queue is full. By default this is 1, i.e. 1 image will be removed. In
        some applications which acquire a sequency of images, it is usually
        desirable to remove a full sequence of images.
        """
        self.numRemoveWhenFull = num
        
    
    def set_use_auxillary_queue(self, use):
        """ Sets whether or not to populate auxillary queue.
        """
        self.useAuxillaryQueue = use
    
    
    def flush_buffer(self):
        """ Removes all images from output queue.
        """
        while not self.imageQueue.empty():
            try:
                self.imageQueue.get_nowait()  
            except:
                pass
    
    
    def flush_auxillary_buffer(self):
        """ Removes all images from auxillary queue.
        """
        while not self.auxillaryQueue.empty():
            try:
                self.auxillaryQueue.get_nowait()  
            except:
                pass
    
    
                
    def pause(self):
        """ Call to pause image acquisition.
        """
        self.isPaused = True
        self.flush_buffer()
        return
    

    def resume(self):
        """ Call to resume a paused image acquisition.
        """
        self.isPaused = False
        return    
        
              
    def stop(self):
        """ Shuts down the thread after closing camera.
        """
        self.isOpen = False
        time.sleep(0.5)
        if self.cam is not None:
            self.cam.close_camera()
            self.cam.dispose()
            del(self.cam)