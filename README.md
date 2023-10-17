# CAS and CAS-GUI - Kent Camera Acquisition System

CAS-GUI is a framework for building graphical user interfaces in Python that involves acquiring, processing and displaying images from cameras
or camera-type systems

CAS is a hardware abstraction layer for cameras.

CAS and CAS-GUI are developed in [Mike Hughes' lab](https://research.kent.ac.uk/applied-optics/hughes) in the [Applied Optics Group](https://research.kent.ac.uk/applied-optics/), School of Physics & Astronomy, University of Kent.

We use CAS-GUI as the basis of several imaging systems, including endomicroscopes and holographic
microscopes. External users are welcome to make use of this code for other purposes, but be aware that it
is not currently documented or tested outside of our specific applications and may be difficult to make sense of. If
you have an interesting use case we can provide some limited support.


## Rough Guide

Classes for handling camera communications are in the src/cameras folder. For a specific camera, a new class must
be created that inherits from GenericCamera. Override the functions from GenericCamera to implement the relevant 
functionality. See the other camera python files in the folder for examples.

CAS-GUI (in CAS_GUI_base.py) is the base class for camera GUIs. This can be run as is, and will provide
a simple camera image viewer with the possibility to adjust exposure, frame rate and
gain. Select the input camera from the drop-down menu and 'Start Acquire' to begin. It will obviously only
work for cameras you have set up on your system - try the webcam first.

To create a GUI for a specific purpose, create a new class that inherits from CAS_GUI. An example
is provided - CAS_GUI_BUNDLE which is designed for fibre bundle imaging.

GUIs are built using PyQt5. Images are displayed using an instance of [ImageDisplayQT](https://www.github.com/mikehugheskent/imagedisplayqt), a widget for
displaying scientific images.

## Supported Cameras

Camera classes exist for the following camera families. Functionality is implemented only as needed, so not every function is supported for every camera:

* Webcam (WebCamera.py) - Returns monochrome images from webcameras. Partial support for exposure and gain (how well these work depend on the specific camera). Requires OpenCV.
* Webcam Colour (WebCameraColour.py) - As Webcam, but returns colour images. Requires OpenCV.
* Thorlabs DCX Series Camaras (DCXCameraInterface.py) - Supports setting and getting frame rate, exposure and gain. Requires instrumental package.
* Thorlabs Kiralux Camera (KiraluxCamera.py) - Supports setting and getting frame rate, exposure and gain. Triggering not supported. Requires Thorlabs Scientific Cameras SDK.
* FLIR FLea Camera (FleaCameraInterface.py) - Testes with Flea Camera series, may work with other cameras that use the Spinnaker API. Supports setting and getting frame rate, exposure and gain and triggering. Requires Spinnaker SDK.

In addition, there are two other camera classes:

* File Interface (FileInterface.py) - Provides an interface to an image stored as a file which is compatible with the camera interfaces, simplifying GUIs which need to work with both videos streams from cameras and saved images.
* Camera Simulator (SimulatedCamera.py) - Simulates a camera using a saved tif stack of images. Images are served at the requested frame rate. Requires PIL.

## Requirements

CAS requirements depends on the specific camera used (see list above).

CAS-GUI requires:
* PIL (Python Image Library)
* OpenCV
* PyQt5

