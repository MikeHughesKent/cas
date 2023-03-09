# -*- coding: utf-8 -*-
"""
Simple GUI in Tkinter to illustrate grabbing and displaying camera frames.

@author: Mike Hughes
Applied Optics Group
University of Kent

"""
from tkinter import ttk
from tkinter import *
from tkinter.ttk import *
import tkinter.scrolledtext



import numpy as np
import time
import cv2 as cv
import math
    
from PIL import ImageTk, Image  
from tkinter.ttk import Frame, Button, Label, Style
from ImageAcquisitionThread import ImageAcquisitionThread


class CAS_gui(Tk):
    
     
   
    
    def __init__(self):
        
        self.acquiring = False
        
        super().__init__()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)


        style = ttk.Style()
        current_theme = style.theme_use('clam')
        
        self.title('Camera Acquisition System - Test GUI')
        
        self.geometry("500x500")
        
        self.imageDispSize = 400
        self.lastUpdateTime = 0
        
        self.fr = Frame(self)
        self.fr.pack(fill=BOTH, expand=True)
        
        #self.button1 = tk.Button(self.fr, text= 'test')
        #self.button1.pack()
        
        # label
        self.fr.columnconfigure(0, weight=1)
        self.fr.columnconfigure(3, pad=7)
        self.fr.rowconfigure(3, weight=1)
        self.fr.rowconfigure(3, pad=7)
        
        
        
        
       
        
        self.statusText = Label(self.fr, text = "No Image")
        self.statusText.grid(row = 1, column = 0, padx = 10, sticky='w')
        
        
        self.logTextTitle = Label(self.fr, text='Log I:')
        self.logTextTitle.grid(row = 2, column = 0)
        
        
        
        
       
        self.logText = tkinter.scrolledtext.ScrolledText(self.fr, wrap = WORD, 
                                     # width = 120, 
                                      #height = 8, 
                                      font = ("Verdana", 10))
        self.logText.grid(row = 3, column = 0, padx = 10, sticky='ewns')
       
        
        
        blankImage = Image.new('L', (self.imageDispSize, self.imageDispSize))
        self.displayImage = ImageTk.PhotoImage(blankImage)
        self.imageDisplay = Label(self.fr, image = self.displayImage)
        self.imageDisplay.grid(row = 0, column = 0)
        
        
        self.conPanel = Frame(self.fr)
        self.conPanel.grid(column = 2, row = 0)
        
        self.openButton = Button(self.conPanel, text="Open Camera", command = self.open_cam)
        self.openButton.pack(fill=BOTH)
        
        self.closeButton = Button(self.conPanel, text="Close Camera", command = self.close_cam)
        self.closeButton.pack(fill=BOTH)
        
       
        
       
        
        tkvar = StringVar(self)

        # Dictionary with options
        choices = {'Simulated','Kiralux','DCx'}
        tkvar.set('Simulated') # set the default option
        Label(self.conPanel, text = "Camera:").pack(fill=BOTH)
        self.camSelect = OptionMenu(self.conPanel, tkvar, *choices)
        self.camSelect.pack()
       

        
        return
    
    def open_cam(self):
        
        # Creates an ImageAcquisitionThread and starts it.
    
        filename = r"..\tests\test_data\stack_10.tif"
        self.imThread = ImageAcquisitionThread('SimulatedCamera', 10, filename = filename)
        self.imThread.get_camera().pre_load(10)
        self.imThread.start()
        
        self.acquiring = True
        self.update_image()
    
        return
        
    
    
    def close_cam(self):
        
        if self.acquiring:
            self.imThread.stop()
            self.acquiring = False

       
        return
    
    
           
    def update_image(self):
        
        
        if self.acquiring:
            
            frame = self.imThread.get_latest_image()
            if frame is not None:
                  
                maxDim = max(np.shape(frame))
                newW = math.floor(np.shape(frame)[1] / maxDim * self.imageDispSize)
                newH = math.floor(np.shape(frame)[0] / maxDim * self.imageDispSize)
                im = Image.fromarray(frame)
                im = im.resize((newW, newH))
                

                self.displayImage = ImageTk.PhotoImage(im)
                self.imageDisplay.configure(image = self.displayImage) 
              
                self.imWidth = np.shape(frame)[0]
                self.imHeight = np.shape(frame)[1]
                
                self.currentUpdateTime = time.perf_counter()
                self.updateRate = 1 / (self.currentUpdateTime - self.lastUpdateTime)
                self.lastUpdateTime = self.currentUpdateTime

            
                imStatus = 'W:' + str(self.imWidth) + ', H: ' + str(self.imHeight)  \
                           + ', fps: ' + str(round(self.imThread.get_actual_fps(),1)) \
                           + ', buffered: ' + str(self.imThread.get_num_images_in_queue()) \
                            + ', display fps: ' + str(round(self.updateRate,1))   


                self.statusText.configure(text=imStatus) 
                
            self.after(round(1000/self.imThread.get_camera().get_frame_rate()), self.update_image)
                
                
    def on_closing(self):
        self.close_cam()
        self.destroy()

if __name__=='__main__':    
    app = CAS_gui()
    app.mainloop()