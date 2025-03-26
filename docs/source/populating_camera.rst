Using Cameras
=============

Populating the Camera List
^^^^^^^^^^^^^^^^^^^^^^^^^^
The camera list drop-down menu on the Image Source menu is populated from a cameras.csv file. The default file
is in the 'res' folder in the 'cas' folder. For custom GUIs, a different cameras.csv files
can be created and placed either in '../res/cameras.csv' relative the python GUI file or
in a custom location by specifying the full path in the GUI class attribute ``camFile``.

Each line of the CSV file represents one cameras has the following structure:

Camera Display Name, Camera Interface Name, Camera Type

The Display Name is the the name displayed in the drop-down menu, the Camera Interface Name
is the name of the Class providing the interface (which must be in a file of the same name) and
Camera Type is either 0 (for a File Interface), 1 (for a real camera), or 2 (for a Simulated Camera).


Using the Simulated Camera
^^^^^^^^^^^^^^^^^^^^^^^^^^
The simulated camera takes a series of images from a file and returns them as if they
were frames from a camera. The images are pre-loaded, allowing very high frames rates. This is
mostly useful to test software using a set of known test images or when camera hardware is not
connected.

The filename to be used can be specified using the GUI class attribute ``sourceFilename``.