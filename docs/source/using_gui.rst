Using the Default GUI
=====================

The following is a brief user-guide for the CAS GUI. Any GUI inheriting from
CAS GUI will have the same features unless these are over-riden.


Selecting the Image Source
^^^^^^^^^^^^^^^^^^^^^^^^^^
Click on the 'Image Source' button to open the Image Source menu. Select the required 
camera source from the drop-down menu. The 'File' camera allows on image to instead be 
loaded from a file. When this option is selected, a button will appear allowing the user 
to browse for this file. If the file is a tif stack, a slider will appear to allow the 
required image from the stack to be selected.

When using a real camera, the frame rate, exposure and gain can be set from the same menu.


Starting and Stopping Acquisition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Once the correct camera source has been selected, click on 'Live Imaging' to begin acquiring images. In the
base class this will display the raw images. Click 'Live Imaging' again to stop the acquisition.


Image Display
^^^^^^^^^^^^^
Hover over the image to view the pixel value in the information bar underneath the image. The pixel value range and mean are also shown. 
Click and drag to create a region of interest; the pixel value range and mean for the ROI will also then be provided 
in the information bar. Click again the image to clear the ROI. Use pinch zoom or a mouse wheel to zoom in and out.

Studies
^^^^^^^
Studies are used to organise saved images and videos. When started, the study is set as 'default'. To create
a new study click 'New Study'. A dialog box allows users to specify the name of the study, and, optionally, a description.

A new subfolder in the studies folder will be created with the specified name.


Saving and Recording
^^^^^^^^^^^^^^^^^^^^
Clicking 'Snap Image' saves the current image to the current study folder. Clicking 'Save As' allows you to
instead specify a filename.

Clicking 'Record' opens the recording menu. The folder to save recordings to is, by default, the current
study folder, but can be changed using the 'Choose Folder' button. The 'Record Raw' toggle only has an impact
if the base class is subclassed to include an image processor. 'Record Tif', if checked, will result in a Tif Stack,
otherwise images will be saved to an AVI. Checking 'Buffered' will cause the GUI to capture the specified number 
of images to memory before saving. If this is not toggled, the GUI will save continuously to the file until the 
'Stop Recording' button, which appears once recording starts, is clicked. This may drop frames depending on the 
disk write speed and the frame rate. 


