# CAS and CAS-GUI - Kent Camera Acquisition System

CAS-GUI is a framework for building graphical user interfaces in Python that involves acquiring, processing and displaying images from cameras
or camera-type systems

It is built on CAS, a hardware abstraction layer for cameras.

CAS-GUI is developed at [Mike Hughes' lab'](https://research.kent.ac.uk/applied-optics/hughes)  
in the [Applied Optics Group](https://research.kent.ac.uk/applied-optics/), School of Physics & Astronomy, University of Kent.
We use CAS-GUI as the basis of several imaging systems, including endomicroscopes and holographic
microscopes. Externals users are welcome to make use of this code for other purposes, but be aware that it
is not currently documented or tested outside of our specific applications and may be difficult to make sense of.


## Rough Guide

Classes for handling camera communications are in the src/cameras folder. For a specific camera, a new class must
be created that inherits from GenericCamera. Override the functions from GenericCamera to implement the relevant 
functionality. See the other camera python files in the folder for examples.

CAS-GUI (in CAS_GUI_base.py) is the base class for camera GUIs. This can be run as is, and will provide
a simple camera image viewer with the possibility to adjust exposure, frame rate and
gain. Select the input camera from the drop-down menu and 'Start Acquire' to begin.

To create a GUI for a specific purpose, create a new class that inherits from CAS_GUI. An example
is provided - CAS_GUI_BUNDLE which is designed for fibre bundle imaging.

GUIS are built using PyQ. Images are displayed using an instance of ImageDisplayQT, a widget for
displaying scientific images.


