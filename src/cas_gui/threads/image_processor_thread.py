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
             time.sleep(0.1)
         
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
        if self.get_num_images_in_output_queue() > 0:
            return True
        else:
            return False
    
    
    def add_image(self, im):
        # Stop output input overfilling

        if self.inputQueue.full():
            temp = self.inputQueue.get()
            t1 = time.time()
        self.inputQueue.put_nowait(im)
        #print("Image added at", time.perf_counter())
    
    
    
    def get_next_image(self):
        
        if self.is_image_ready() is True:
            try:
                im = self.outputQueue.get()
                
                if self.useSharedMemory:
                    # If using shared memory, the im returned is a tuple giving the size of the image. The actual
                    # image is in the shared memory
                    imSize = im
                    #print("Taking image from buffer")
                    if self.sharedMemory is None:
                        self.sharedMemory = multiprocessing.shared_memory.SharedMemory(name="CASShare")
                        self.sharedMemoryArray = np.ndarray(self.sharedMemoryArraySize, dtype = 'float32', buffer = self.sharedMemory.buf)  
                    im = self.sharedMemoryArray[:imSize[0], :imSize[1]]
                    #im = np.zeros((10,10))
                    #print(im[30,30])
                    #im2 = im[:imSize[0],:imSize[1]]
                    im = np.copy(im)

            except queue.Empty:
                return None
        else:
            return None
        
        
        
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