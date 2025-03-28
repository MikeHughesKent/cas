# -*- coding: utf-8 -*-
"""
ImageProcessorThread
Part of CAS GUI: Camera Acquisition System GUI

Threading class for image processing for use in GUIs or or 
multi-threading applications. Sub-class and implement process_frame
to make a custom image processor.

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
    sharedMemoryArray = None
    inputSharedMemory = None
    imSize = (0,0)
    lastImNum = -1  
    numDropped = 0
    
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
        self.multiCore = kwargs.get('multiCore', False)
        self.useSharedMemory = kwargs.get('sharedMemory', False)        
        self.sharedMemoryArraySize = kwargs.get('sharedMemoryArraySize', (2048, 2048))

        if self.multiCore and not self.useSharedMemory:                
            self.outputQueue = multiprocessing.Queue(maxsize=self.outBufferSize)
        else:
            self.outputQueue = queue.Queue(maxsize=self.outBufferSize)
            
        self.statusQueue = multiprocessing.Queue(maxsize = 1000)    

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
        
        if self.multiCore:
            
            # Queue for sending updates on how to do the processing
            self.updateQueue = multiprocessing.Queue()
            self.messageQueue = multiprocessing.Queue()
            
            if self.useSharedMemory:
                outQueue = None
            else:
                outQueue = self.outputQueue
                
            self.shareName = str(np.random.randint(6400000, size = 1)[0])
            
            # Create the process and set it running
            self.process = ImageProcessorProcess(self.inputQueue, outQueue, self.updateQueue, 
                                                 self.messageQueue, sharedMemoryArraySize = self.sharedMemoryArraySize, 
                                                 useSharedMemory = self.useSharedMemory, statusQueue = self.statusQueue, shareName = self.shareName)
            self.process.start()
            time.sleep(0.1)
            self.updateQueue.put(self.processor)
           
        
    
        
    # This loop is run once the thread starts
    def run(self):

         while self.isStarted:                 

            
             if self.multiCore:
                                   
                 if self.useSharedMemory:
                 
                     # If we have not yet got a reference to the shared memory, get it now
                     if self.sharedMemory is None:
                         temp = np.ndarray(self.sharedMemoryArraySize, dtype = 'float32')
                         try:
                             self.sharedMemory = multiprocessing.shared_memory.SharedMemory(create=True, size=temp.nbytes, name = self.shareName)
                         except:
                             self.sharedMemory = multiprocessing.shared_memory.SharedMemory(size=temp.nbytes, name = self.shareName)

                         #try:
                             #self.sharedMemory = multiprocessing.shared_memory.SharedMemory(name="CASShare")
                         self.sharedMemoryArray = np.ndarray(self.sharedMemoryArraySize, dtype = 'float32', buffer = self.sharedMemory.buf)  
                         #except:
                          #   pass
                     else:
                         # The image width, height, processing step time, and frame number are
                         # stored in a corner of the shared memory
                         imW = int(self.sharedMemoryArray[0,1])
                         imH = int(self.sharedMemoryArray[0,0])                       
                        
                         imNum = int(self.sharedMemoryArray[0,3])
                         imIndex = int(self.sharedMemoryArray[0,4])

                         if imNum > self.lastImNum + 1:
                             self.numDropped += 1
                             
                             
                         # Only pull off and return an image if we haven't already returned this
                         if imNum > self.lastImNum  and imW > 0 and imH > 0:
                             im = self.sharedMemoryArray[1:1+imH, :imW] #.copy()
                             #m = np.zeros((10,10))
                             self.lastImNum = imNum           
                         
                             if self.outputQueue.full():
                                 temp = self.outputQueue.get()
                             
                             self.outputQueue.put_nowait((im, imIndex)) 
                             #print("got out image")
                         else:
                              time.sleep(0.01)

                              
                 else:  # self.useSharedMemory = False
                      # If we are not using shared memory we don't need to do anything here because
                      # the processed images will be put straight in the output queue by the ImageProcessorProcess
                      time.sleep(0.01)
             
             else:    
                 
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
                                 out = self.process_frame(self.currentInputImage)
                                 
                                 if isinstance(out, tuple):
                                     self.currentOutputImage = out[0]
                                 else:
                                     self.currentOutputImage = out
                                 
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
                         
    def acquire_set(self):
    
        img = self.inputQueue.get()

        self.currentInputImage = np.zeros((np.shape(img)[0], np.shape(img)[1], self.batchProcessNum))
        self.currentInputImage[:,:,0] = img
        
        for i in range(1, self.batchProcessNum):
            self.currentInputImage[:,:,i] = self.inputQueue.get()                 
        
        return self.currentInputImage[:,:,:]    
         
                   
    def pipe_message(self, command, parameter):
        """ Sends a message to update an attribute or call a function in the
        ImageProcessorClass.
        
        Arguments:
            command   : str
                        name of attribute or function
            parameter : tuple
                        if calling a function, this is a tuple containing
                        the arguments to be passed to the function. If setting
                        an attribute, this is the value to set
        """
        if self.multiCore:
            self.messageQueue.put((command, parameter))
        else:
            if self.processor is not None:
                self.processor.message(command, parameter)
                

                
    def get_processor(self):
        """ Returns reference to processor object"""
        return self.processor
     
        

    def process_frame(self, inputFrame):
        """ Processes a single frame and return processed frame. Both are
        numpy arrays"""
        
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
        """ Returns true if there is a new processed image ready to be read.
        """             
        if self.get_num_images_in_output_queue() > 0:
            return True
        else:
            return False
    
    
    def add_image(self, im):
        """ Adds a raw image to be processed.
        """
        # Stop output input overfilling
        if self.inputQueue.full():
            temp = self.inputQueue.get()

        self.inputQueue.put_nowait(im)
    
    
    
    def get_next_image(self):
        """ Returns the next available processed image.
        """        
        im = None         
        if self.is_image_ready() is True:   
            try:
                im = self.outputQueue.get_nowait()   
            except:
                im = None
        
        return im
            
        
    def get_actual_fps(self):
        """ Returns the processing frame rate.
        """
        
        # If using single core, we have already stored the frame step time
        if not self.multiCore and self.frameStepTime > 0:
            return (1 / self.frameStepTime)
        
        # If using shared memory we can pull this from the shared memory as the processor
        # stores it there
        elif self.multiCore and self.useSharedMemory and self.sharedMemoryArray is not None:
            if self.sharedMemoryArray[0,2] > 0:
                return (1 / self.sharedMemoryArray[0,2])
            else:
                return 0
        
        # If using multiCore without shared memory, we do not have access to frame rate, so
        # return 0
        else:
            return 0
        
    
    
    def get_latest_processed_image(self):
        """ Returns the last processed image that was obtained.
        """
        return self.currentOutputImage
    
   
    
    def get_latest_input_image(self):
        """ Returns the last raw image that was added.
        """
        return self.currentInputImage    
    
   
    
    def flush_input_buffer(self):
        """ Removes all raw images from queue.
        """
        with self.inputQueue.mutex:
            self.inputQueue.queue.clear()
            
    def flush_status_buffer(self):
        """ Removes all messages from status queue
        """
        while True:
            try:
                null = self.statusQueue.get_nowait()
            except:
                break
            
            
            
    def set_batch_process_num(self, num):
        """ Sets the size of the batch of images to be sent to the processor.
        """
        self.batchProcessNum = num
        if self.multiCore:
            self.pipe_message("set_batch_process_num", num)
        
    
    def flush_output_buffer(self):
        """ Removes all processed images from queue if not using shared memory
        """
        if self.useSharedMemory is False:
            with self.outputQueue.mutex:
                self.outputQueue.queue.clear()    
   
            
    def pause(self):
        """ Pauses the processing.
        """
        self.isPaused = True
        return
    

    def resume(self):
        """ Resumes paused processing.
        """
        self.isPaused = False
        return            
    
          
    def stop(self):
        """ Stops the process. 
        """
        self.isStarted = False
        if self.process is not None:
            print("Terminating process")
            self.process.terminate()
            self.process.join()

  
    def update_settings(self):
        """ Sends a copy of the processor class to the process running on
        another core. """
        if self.updateQueue is not None:
            self.updateQueue.put(self.processor)