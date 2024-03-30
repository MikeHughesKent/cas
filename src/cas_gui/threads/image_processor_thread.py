# -*- coding: utf-8 -*-
"""
ImageProcessorThread
Part of Kent CAS-GUI: Camera Acquisition System GUI

Threading class for image processing for use in GUIs or or 
multi-threading applications. Sub-class and implement process_frame
to make a custom image processor.

@author: Mike Hughes
Applied Optics Group
University of Kent
"""

import queue
import threading
import time
import logging
import multiprocessing
import numpy as np

from cas_gui.threads.image_processor_process import ImageProcessorProcess


class ImageProcessorThread(threading.Thread):
    
    process = None
    updateQueue = None
    sharedMemory = None
    inputSharedMemory = None
    imSize = (0,0)
    
    def __init__(self, processor, inBufferSize, outBufferSize, **kwargs):
        
        # Caller passes the name of the camera class (which should be in a
        # module of the same name) in the variable camName. This is dynamically
        # imported here and an instance created as self.cam.
   
        super().__init__()
        
        self.processor = processor()
        self.inBufferSize = inBufferSize
        self.outBufferSize = outBufferSize
        self.inputQueue = kwargs.get('inputQueue', None)
        self.acquisitionLock = kwargs.get('acquisitionLock', None)
        self.multicore = kwargs.get('multicore', False)
        self.useSharedMemory = kwargs.get('sharedMemory', False)
        
        self.sharedMemoryArraySize = kwargs.get('sharedMemoryArraySize', (1024 ,1024))

      
        if self.inputQueue is None:
            self.inputQueue = multiprocessing.Queue(maxsize=self.inBufferSize)
        #self.inputQueue = queue.Queue(maxsize=self.inBufferSize)
        self.outputQueue = multiprocessing.Queue(maxsize=self.outBufferSize)

        self.currentOutputImage = None
        self.currentInputImage = None
        
        self.lastFrameTime = 0
        self.frameStepTime = 0
        self.currentFrame = None
        self.currentFrameNumber = 0
        self.isPaused = False
        self.isStarted = True
        self.batchProcessNum = 1
        
        # If we are going to use a different core to do processing, then we need
        # to start a process on that core.
        
        if self.multicore:
            # Queue for sending updates on how to do the processing
            self.updateQueue = multiprocessing.Queue()
            self.messageQueue = multiprocessing.Queue()
            
            # Create the process and set it running
            self.process = ImageProcessorProcess(self.inputQueue, self.outputQueue, self.updateQueue, 
                                                 self.messageQueue, sharedMemoryArraySize = self.sharedMemoryArraySize, 
                                                 useSharedMemory = self.useSharedMemory)
            self.process.start()
            self.updateQueue.put(self.processor)
           
        
    
        
    # This loop is run once the thread starts
    def run(self):

        
         # If we are doing multicore, we do nothing here because we should already
         # have the processor running on another core
         if self.multicore:
                               
             time.sleep(0.01)
         
         else:    
             while self.isStarted:                 
                 
                 if not self.isPaused:
                     
                     self.handle_flags()     
                     # Stop output queue overfilling
                     if self.outputQueue.full():
                         for i in range(self.batchProcessNum):
                             temp = self.outputQueue.get()
                   
                     if self.get_num_images_in_input_queue() >= self.batchProcessNum:
                         
    
                         if self.acquisitionLock is not None: self.acquisitionLock.acquire()
                         try:
                             if self.batchProcessNum > 1:
                                 img = self.inputQueue.get()
                                 self.currentInputImage = np.zeros((np.shape(img)[0], np.shape(img)[1], self.batchProcessNum))
                                 self.currentInputImage[:,:,0] = img
                                 for i in range(1, self.batchProcessNum):
                                     self.currentInputImage[:,:,i] = self.inputQueue.get()
                                 self.currentOutputImage = self.process_frame(self.currentInputImage)
                                 self.outputQueue.put(self.currentOutputImage)
    
    
                             else:
                                 self.currentInputImage = self.inputQueue.get()
                                 self.currentOutputImage = self.process_frame(self.currentInputImage)

                                 self.outputQueue.put(self.currentOutputImage)
    
                             # Timing
                             self.currentFrameNumber = self.currentFrameNumber + 1
                             self.currentFrameTime = time.perf_counter()
                             self.frameStepTime = self.currentFrameTime - self.lastFrameTime
                             self.lastFrameTime = self.currentFrameTime
                     
                         except queue.Empty:
                             print("No image in queue")
                         
                         if self.acquisitionLock is not None: self.acquisitionLock.release()
    
                     else:
                         time.sleep(0.01)
                   
    def pipe_message(self, command, parameter):
        if self.multicore:
            self.messageQueue.put((command, parameter))
        else:
            if self.processor is not None:
                self.processor.message(command, parameter)
                

                
    def get_processor(self):
        return self.processor
     
        
    ######### Override to provide code for processing the input frame
    def process_frame(self, inputFrame):
        
        ret = self.processor.process(inputFrame) 
        return ret
        
    
    ######### Override with code that should be run on each iteration
    def handle_flags(self):
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
        
        # If we are using shared memory then the image is always ready,
        # we just copy from the shared memory at whatever update rate we want.
        
        # Otherwise, if using queues, we need to check if there is something
        # in the queue
        
       # if self.useSharedMemory is True:
        #    return True
        if self.get_num_images_in_output_queue() > 0:
            return True
        else:
            return False
    
    
    def add_image(self, im):
        # Stop output input overfilling

        if self.inputQueue.full():
            temp = self.inputQueue.get()
        self.inputQueue.put_nowait(im)
    
    
    
    def get_next_image(self):
        
        # If we are using shared memory, check if there is anything in the queue
        # With shared memory, the queue just tells us the image size
        if self.useSharedMemory:
            
            if self.outputQueue.qsize() > 0:
                try:
                    self.imSize = self.outputQueue.get_nowait()
                except:
                    return None


        if self.useSharedMemory: 
            
           # Check we have been given a non-zero image size, the is initialised
           # to (0,0) so this will also stop us trying to read from shared memory
           # before it has been created
           if (self.imSize[0] > 0 or self.imSize[1] > 0):       
               
               # If we have not yet got a reference to the shared memory, get it now
               if self.sharedMemory is None:
                     self.sharedMemory = multiprocessing.shared_memory.SharedMemory(name="CASShare")
                     self.sharedMemoryArray = np.ndarray(self.sharedMemoryArraySize, dtype = 'float32', buffer = self.sharedMemory.buf)  
              
               imW = int(self.sharedMemoryArray[0,1])
               imH = int(self.sharedMemoryArray[0,0])

               # Pull the image from shared memory
               im = self.sharedMemoryArray[1:1+imH, :imW]
           
           else:
               im = None
       
        # Otherwise, if we are using queues:
        else:
            
            if self.is_image_ready() is True:   
                try:
                    im = self.outputQueue.get_nowait()   
                except:
                    im = None
        
        return im
            
    
    
    def get_inter_frame_time(self):
        return self.frameStepTime
    
    
    
    def get_actual_fps(self):
        
        if not self.multicore and self.frameStepTime > 0:
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
            
            
    def set_batch_process_num(self, num):
        self.batchProcessNum = num
        
    
    def flush_output_buffer(self):
        with self.outputQueue.mutex:
            self.outputQueue.queue.clear()    
   
            
    def pause(self):
        self.isPaused = True
        return

    def resume(self):
        self.isPaused = False
        return            
              
    def stop(self):
        print("stopping")
        self.isStarted = False
        if self.process is not None:
            print("stopping process")
            self.process.terminate()

  
    # This must be over-ridden by subclass if multicore is to be used.  
    def update_settings(self):
        if self.updateQueue is not None:
            self.updateQueue.put(self.processor)