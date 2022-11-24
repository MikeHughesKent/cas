# -*- coding: utf-8 -*-
"""
ImageProcessorHandler
Part of Kent CAS-GUI: Camera Acquisition System GUI

Base class for interacting with ImageProcessorProcess. ImageProcessorProcess
is designed to run in a separate process, ImageProcessorHandler is an object
which creates this process, including creating the queues needed for 
communication.

At creation, the sizes of the input and output buffers for ImageProcessorProcess
are specified. Alternatively, existing queued can be specified with
the optional arguments 'inputQueue' and 'outputQueue', in which case the
relevant queue sizes are ignored. This allows, for example, the ouput queue
from the camera acquisition thread to be used directly.

@author: Mike Hughes
Applied Optics Group
University of Kent
"""
#
#import queue
#import threading
import multiprocessing
import time
import logging
import ImageProcessorProcess
import queue

class ImageProcessorHandler:  
    
    
    
    def __init__(self, inBufferSize, outBufferSize, **kwargs):
        
   
        super().__init__()
        
                
        self.inBufferSize = inBufferSize
        self.outBufferSize = outBufferSize
        
        # Use supplied queues or create if not supplied
        self.inputQueue = kwargs.get('inputQueue', multiprocessing.Queue(maxsize=self.inBufferSize))
        self.outputQueue = kwargs.get('outputQueue', multiprocessing.Queue(maxsize=self.outBufferSize))

        
        self.updateQueue = multiprocessing.Queue()
        
        # Create the process and set it running
        self.process = ImageProcessorProcess.ImageProcessorProcess(self.inputQueue, self.outputQueue, self.updateQueue)
        self.process.start()

        self.currentOutputImage = None
        self.currentInputImage = None
        
        self.lastFrameTime = 0
        self.frameStepTime = 0
        self.currentFrame = None
        self.currentFrameNumber = 0
        self.isPaused = False
        self.isStarted = True
        
        
    # To be over-ridden
    def update_settings(self):
        pass
        
       
    def get_input_queue(self):
        return self.inputQueue
    
    
    def get_ouput_queue(self):
        return self.outputQueue
    
    
    def get_num_images_in_input_queue(self):
        return self.inputQueue.qsize()
    
    
    def get_num_images_in_output_queue(self):
        return self.outputQueue.qsize()
        
    
    def is_image_ready(self):
        if self.get_num_images_in_output_queue() > 0:
            return True
        else:
            return False
        
    
    # Adds image to processing input queue
    def add_image(self, im):
        # Stop output input overfilling
        if self.inputQueue.full():
            temp = self.inputQueue.get()
            #t1 = time.time()
        self.inputQueue.put_nowait(im)
        #print("Image added at", time.perf_counter())
    
   
    # Retrives next image from processing output queue, returns None 
    # if no image ready
    def get_next_image(self):


        try:
            im = self.outputQueue.get()
        except queue.Empty:
            #print("No output images in queue")
            return None
        return im
    
    
    def get_inter_frame_time(self):
        return self.frameStepTime
    
    
    def get_actual_fps(self):
        if self.frameStepTime > 0:
            return (1 / self.frameStepTime)
        else:
            return 0
        
    
    def get_latest_processed_image(self):
        return self.currentOutputImage
    
    
    def get_latest_input_image(self):
        return self.currentInputImage    
    
   
    def flush_input_buffer(self):
        with self.inputQueue.mutex:
            self.inputQueue.queue.clear()
            
    
    def flush_output_buffer(self):
        with self.outputQueue.mutex:
            self.outputQueue.queue.clear()
        
     
           
              
    def stop(self):
        self.isStarted = False
        self.process.terminate()
        
    
    # These three options currently have no option, kept for compatibility
    def handle_flags(self):
        pass
            
    def pause(self):
        self.isPaused = True
        return

    def resume(self):
        self.isPaused = False
        return    

