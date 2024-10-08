# CAS and CAS-GUI - Kent Camera Acquisition System

CAS is hardware abstraction layers for camera acquisition and control in Python.

CAS-GUI is a framework for building graphical user interfaces in Python that 
involves acquiring, processing and displaying images from cameras or 
camera-type systems


CAS and CAS-GUI are developed in 
[Mike Hughes' lab](https://research.kent.ac.uk/applied-optics/hughes) 
in the [Applied Optics Group](https://research.kent.ac.uk/applied-optics/), 
School of Physics & Astronomy, University of Kent.

We use CAS-GUI as the basis of several imaging systems, including endomicroscopes 
and holographic microscopes. External users are welcome to make use of this 
code for other purposes, but be aware that it is not currently fully documented or 
tested outside of our specific applications. There are three examples of custom 
GUIs in the 'examples' folder. and if you  have an interesting use case we can 
provide some limited support.


## Rough Guide

The CAS-GUI class (in src/cas_gui/base.py) is the base class for camera GUIs. This can be run 
as is, and will provide a simple camera image viewer with the possibility to 
adjust exposure, frame rate and gain. Select the input camera from the 
drop-down menu in the 'Source' menu and click 'Live Imaging' to begin. 
It will obviously only work for cameras you have set up on your system - try 
the Webcam (if you have one) or Simulated Camera first. The Simulated Camera 
can load a sequence of images from a tif stack in order to simulate camera 
acquisition. Alternatively, select the 'File' source to load in a saved image
or tif stack.

Classes for handling camera communications are in the 'src/cas_gui/cameras' folder. For 
a specific camera, a new class must be created that inherits from GenericCamera. 
Override the functions from GenericCamera to implement the relevant 
functionality. See the other camera python files in the folder for examples.

GUIs are built using PyQt5. Images are displayed using an instance of 
[ImageDisplayQT](https://www.github.com/mikehugheskent/imagedisplayqt), a widget 
for displaying scientific images.

To create a GUI for a specific purpose, create a new class that inherits from 
CAS_GUI in base.py. Three simple example are provided in the examples folder - 
[gui_example](https://github.com/MikeHughesKent/cas/blob/main/examples/gui_example.py), 
[gui_example_multi_frame](https://github.com/MikeHughesKent/cas/blob/main/examples/gui_example_multi_frame.py)
and [gui_example_multi_core](https://github.com/MikeHughesKent/cas/blob/main/examples/gui_example_multi_core.py).

gui_example demonstrates how a Gaussian smoothing filter can be applied to the 
images grabbed from a camera, while the gui_example_multi_frame demonstrates 
averaging of frames. gui_example_multi_core is the same as gui_example except
that the processing is performed on a different core for improved speed using
multiprocessing. These GUIs can be used as templates to begin building GUIs with 
custom image processing pipelines.

There is also an example of a more complex GUI, [CAS_GUI_Bundle](https://github.com/MikeHughesKent/cas/blob/main/src/cas_gui/subclasses/cas_bundle.py), 
in the subclasses folder, but this is not fully documented.


## Supported Cameras

Camera classes exist for the following camera families. Functionality is 
implemented only as needed, so not every function is supported for every camera:

* Webcam (WebCamera.py) - Returns monochrome images from webcameras. Partial support for exposure and gain (how well these work depend on the specific camera). Requires OpenCV.
* Webcam Colour (WebCameraColour.py) - As Webcam, but returns colour images. Requires OpenCV.
* Thorlabs DCX Series Camaras (DCXCameraInterface.py) - Supports setting and getting frame rate, exposure and gain. Requires instrumental package.
* Thorlabs Kiralux Camera (KiraluxCamera.py) - Supports setting and getting frame rate, exposure and gain. Triggering not supported. Requires Thorlabs Scientific Cameras SDK.
* FLIR FLea Camera (FleaCameraInterface.py) - Tested with Flea Camera series, may work with other cameras that use the Spinnaker API. Supports setting and getting frame rate, exposure and gain and triggering. Requires Spinnaker SDK.

In addition, there are two other camera classes:

* File Interface (FileInterface.py) - Provides an interface to an image stored as a file which is compatible with the camera interfaces, simplifying GUIs which need to work with both videos streams from cameras and saved images.
* Camera Simulator (SimulatedCamera.py) - Simulates a camera using a saved tif stack of images. Images are served at the requested frame rate. Requires PIL.

## Examples

Examples of basic use of CAS are in the examples folder:

* GUI Example - Demonstrates how to sub-class CAS-GUI to produce a simple
GUI which applies a smoothing filter to the live video display.
* GUI Multi Core Example - The same as GUI Example, but uses multiprocessing.
* GUI Example Multi Frame - Demonstrates how to sub-class CAS-GUI to produce a simple
GUI which averages multiple frames from the live video display.
* Simulated Camera Example - Demonstrates how to capture images from a simulated camera which streams images from a tif stack file.
* Webcamera Example - Demonstrates how to capture monochrome images from a web camera.
* Flea Camera Example - Demonstrates how to capture images from a FLIR camera, including setting and getting various parameters and triggering.

## Requirements

CAS requirements depends on the specific camera used (see list above).

CAS-GUI requires:
* PIL (Python Image Library)
* OpenCV
* PyQt5
* Numpy
* Matplotlib

