# -*- coding: utf-8 -*-
"""
#  HughesLab: im_tools

"""

import os
import math

import numpy as np
import numpy.ma as ma

from PIL import Image



def load_image(filename):
    """
    Loads an image or stack of images from a file. 
    
    Arguments:
        filename    : str or Path
                      path to file
    
    Returns:
        ndarray     : 2D, 3D or 4D numpy array representing image or stack  

    """
    im = Image.open(filename)
    
    if im.n_frames > 1:
        h,w = np.shape(im)
        dt = np.array(im).dtype
        stack = np.zeros((im.n_frames, h,w), dtype = dt)
        for i in range(im.n_frames):
            im.seek(i)
            stack[i,:,:] = np.array(im)
        return stack
    else:    
        return np.array(Image.open(filename))


def crop_zero(img):
    """ 
    Crops an image to the smallest rectangle that contains all non-zero
    pixels.
    
    Returns cropped image as 2D numpy array.
    
    Arguments:
        img      : ndarray
                   image as numpy array
                   
    Returns
        ndarray, cropped image                
    """
    
    hMax = np.amax(img, axis = 0)

    hCrop = (np.argwhere(hMax > 0)[0].item(), np.argwhere(hMax > 0)[-1].item() )
    
    vMax = np.amax(img, axis = 1)
    vCrop = (np.argwhere(vMax > 0)[0].item(), np.argwhere(vMax > 0)[-1].item() )
    
    img = img[vCrop[0]:vCrop[1],hCrop[0]:hCrop[1]]
    
    return img
    
    

def extract_central(img, boxSize = None):
    """ 
    Extract a central square from an image. The extracted square is centred
    on the input image, with size 2 * boxSize if possible, otherwise the largest
    square that can be extracted.
    
    Returns cropped image as 2D numpy array.
    
    Arguments:
        img     : input image as 2D numpy array
        
    Keyword Arguments:    
        boxSize : size of cropping square, default is largest possible
        
    Returns:
        ndarray, cropped image
    """

    w = np.shape(img)[0]
    h = np.shape(img)[1]

    if boxSize is None:
        boxSize = min(w,h)
    cx = w/2
    cy = h/2
    boxSemiSize = min(cx,cy,boxSize)
    
    imgOut = img[math.floor(cx - boxSemiSize):math.floor(cx + boxSemiSize), math.ceil(cy- boxSemiSize): math.ceil(cy + boxSemiSize)]
    
    return imgOut


def to8bit(img, minVal = None, maxVal = None):
    """ Returns an 8 bit representation of image. If min and max are specified,
    these pixel values in the original image are mapped to 0 and 255 
    respectively, otherwise the smallest and largest values in the 
    whole image are mapped to 0 and 255, respectively.
    
    Arguments:
            img    : ndarray
                     input image as 2D numpy array
        
    Keyword Arguments:    
            minVal : float
                     optional, pixel value to scale to 0
            maxVal : float
                     optional, pixel value to scale to 255
    """
 
    img = img.astype('float64')
       
    if minVal is None:
        minVal = np.min(img)
                    
    img = img - minVal
        
    if maxVal is None:
        maxVal = np.max(img)
    else:
        maxVal = maxVal - minVal
        
    img = img / maxVal * 255
    img = img.astype('uint8')
    
    return img


def to16bit(img, minVal = None, maxVal = None):
    """ Returns an 16 bit representation of image. If min and max are specified,
    these pixel values in the original image are mapped to 0 and 2^16 
    respectively, otherwise the smallest and largest values in the 
    whole image are mapped to 0 and 2^16 - 1, respectively.
    
    Arguments:
        img    : ndarray
                 input image as 2D numpy array
        
    Keyword Arguments:    
        minVal : float
                 optional, pixel value to scale to 0
        maxVal : float
                 optional, pixel value to scale to 2^16 - 1
                 
    Returns:
        ndarray, 16 bit image             
    """   
        
    img = img.astype('float64')
       
    if minVal is None:
        minVal = np.min(img)
                    
    img = img - minVal
        
    if maxVal is None:
        maxVal = np.max(img)
    else:
        maxVal = maxVal - minVal
        
    img = img / maxVal * (2^16 - 1)
    img = img.astype('uint16')
    
    return img


def radial_profile(img, centre):
    """ Produce angular averaged radial profile through image img centred on
    centre, a tuple of (x_centre, y_centre)
    
    Returns radial profile as 1D numpy array

    Arguments:
        img    : ndarray
                 input image as 2D numpy array
        centre : (int, int)
                 centre point for radial profile, tuple of (x,y)  
    Returns:
        ndarray, 1D profile             
    """
    
    y, x = np.indices((img.shape))
    r = np.sqrt((x - centre[1])**2 + (y - centre[0])**2)
    r = r.astype(int)
    
    tbin = np.bincount(r.ravel(), weights = img.ravel())
    nr = np.bincount(r.ravel())
    radialprofile = tbin  / nr
    
    return radialprofile 
 



def save_image8(img, filename):
    """ Saves image as 8 bit tif without scaling.
    
    Arguments:
         img      : ndarray, 
                    input image as 2D numpy array
                   
         filename : str
                    path to save to, folder must exist
    """
    
    im = Image.fromarray(img.astype('uint8'))
    im.save(filename)



def save_image16(img, filename):
    """ Saves image as 16 bit tif without scaling.
        
    Arguments:
         img      : ndarray, 
                    input image as 2D numpy array
                   
         filename : str
                    path to save to, folder must exist
    """
    im = Image.fromarray(img.astype('uint16'))
    im.save(filename)


     
def save_image8_scaled(img, filename):
    """ Saves image as 8 bit tif with scaling to use full dynamic range.
            
    Arguments:
         img      : ndarray, 
                    input image as 2D numpy array
                   
         filename : str
                    path to save to, folder must exist
    """
    
    im = Image.fromarray(to8bit(img))
    im.save(filename)
    
    
def save_image16_scaled(img, filename):
    """ Saves image as 16 bit tif with scaling to use full dynamic range.
            
    Arguments:
         img      : ndarray, 
                    input image as 2D numpy array
                   
         filename : str
                    path to save to, folder must exist
    """
        
    im = Image.fromarray(to16bit(img)[0])
    im.save(filename) 


def average_channels(img):
    """ Returns an image which is the the average pixel value across all channels of a colour image.
    It is safe to pass a 2D array which will be returned unchanged.
    
    
    Arguments:
        img:    ndarray
                 image as 2D/3D numpy array
            
    Returns:
        ndarray, averaged image        
    """     

    if img.ndim == 3:
        return np.mean(img, 2)
    else:
        return img
    
    
def max_channels(img):
    """ Returns an image which is the the maximum pixel value across all channels of a colour image.
    It is safe to pass a 2D array which will be returned unchanged.
    
    
    Arguments:
        img:   ndarray
               image as 2D/3D numpy array
               
    Returns:
        ndarray, max value image           
    """     

    if img.ndim == 3:
        return np.max(img, 2)
    else:
        return img
        
        
    

def load_stack(folder):
    """ Loads a stack of images from a folder into a 3D numpy array
    
    Arguments:
        folder      : str
                      path to folder
        status      : boolean
                      if True, updates status on console (default = True)              
                      
    Returns:
        ndarray, 3D numpy array (im, y, x)                     
    """    

    image_files = [f for f in os.listdir(folder)]
    
    nImages = len(image_files)    
    
    testIm = np.array(Image.open(os.path.join(folder,image_files[0])))
    
    h, w = np.shape(testIm)    
    
    data = np.zeros((nImages, h, w), dtype = testIm.dtype)
   
   
    
    for idx, image_file in enumerate(image_files):            
        data[idx,:,:] = np.array(Image.open(os.path.join(folder,image_file)))        
        
    return data   
  

def save_tif_stack(stack, filename, bit_depth = 8, auto_contrast = None, fixed_min = None):
    """ Writes stack of images from 3D numpy array to file. The array must 
    be orders (frame, y, x).
    
    Arguments:
        stack         : ndarray
                        3D numpy array (frame, y, x)
        filename      : str or Path
                        path to file name. Folder must exist.            
                       
    Keyword Arguments:
        bit_depth     : int
                        8 (default) or 16
        auto_contrast : str or None
                        Whether or not to scale images to use full bit depth
                        'image' to autoscale each image individually
                        'stack' to autoscale entire stack
                        None or 'none' for no autoscaling
        fixed_min     : int or None
                        if auto_contrast is 'image' or 'stack', setting this
                        value fixed the lower range of the saved image pixel
                        values rather than taking the minimum from the images.
                                         
    """
    if stack.ndim != 3:
       raise Exception("Stack must be 3D array.")

    if auto_contrast == 'stack':
       maxVal = np.max(stack)
       if fixed_min is None:
           minVal = np.min(stack)
       else:
           minVal = fixed_min
    elif auto_contrast == 'image' or auto_contrast == 'none' or auto_contrast is None:
        pass
    else:
        raise Exception("Keyword auto_contrast only accepts 'stack', 'image' or None.")

       
    if bit_depth == 16:
        dt = 'uint16'
    elif bit_depth == 8:
        dt = 'uint8'
    else:
        raise Exception("Bit depth can only be 8 or 16.")
    
    imlist = []
    for im in stack:
        
        if auto_contrast == 'image':
            maxVal = np.max(np.abs(im))
            if fixed_min is None:
                minVal = np.min(np.abs(im))
            else:
                minVal = fixed_min
                
        if auto_contrast is not None:
            im = im.astype('float64') - minVal
            intrange = maxVal - minVal
            if intrange > 0:
                im = im / intrange * (2**bit_depth - 1)
            else:
                im[:] = 2**bit_depth - 1
        imlist.append(Image.fromarray(im.astype(dt)))


    imlist[0].save(filename, compression="tiff_lzw", save_all=True,
           append_images=imlist[1:])
    
    


def log_scale_image(img, min_val = None):
    """ Generates a log-scaled image, adjusted for good visual appearance,
    particularly for OCT images.
    
    Arguments:
        img     : ndarray 
                  image as 2D numpy array
     
    Optional Keyword Arguments:
        min_val : float
                  if specified, 0 in image will correspond to this value 
                  in log scaled image before windowing
                  
    Returns:
        ndarray, log-scaled image (8 bit)             
                   .
    """

    if min_val is None:
        dispMin = log_scale_min(img)
        
    else:
        dispMin = min_val
    
    imgOut = np.log(img + 0.00001)
    imgOut = imgOut - dispMin
    maxVal = np.max(imgOut) * 0.9
    imgOut = imgOut / maxVal
    imgOut[imgOut < 0] = 0
    imgOut[imgOut > 1] = 1
    
    return imgOut


def log_scale_min(img):
    """Calculates minimum display value for a log-scaled image so that 
    it does no appear overly noisy.
    
    Arguments:
        img     : ndarray 
                  image as 2D numpy array
     
    
    Returns:
        float, minimum value           
                   .
    """    
    
    mask = img == 0
    im = np.log(img + 0.00001)
    imgOut = ma.masked_array(im, mask)
    valRange = np.max(imgOut) - ma.min(imgOut)

    lineAv = ma.mean(imgOut,0)
    sVals = np.sort(lineAv)

    minVal = sVals[min(10, len(sVals) - 1)]

    dispMin = minVal - valRange / 25
    if dispMin is not ma.masked:
        return dispMin
    else:
        return 0    