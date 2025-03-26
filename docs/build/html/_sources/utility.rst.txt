
Utility Functions
=================

The CAS_GUI class contains a number of utility function that may be useful
to call directly.
To run the image processing on a separate core, we set the parameter::

    multiCore = True
    
CAS-GUI will then handle starting a process. For very simple processors,
which do not require changes of parameters or calibration, this is all that
is required.

CAS-GUI first creates an instance of the image processor class on the local
proces and then pipes it to the other process via a queue. This means that any 
subsequent changes to the local copy of the image processor class will not be
reflected in the copy in the other process. It is necessary to call the 
``update_settings()`` method of the instance of ``ImageProcessorThread`` a
reference to which is stored in the ``self.processor`` parameter. Therefore, following 
any change of settings, you should call::

    if self.processor is not None:
        self.processor.update_settings()

The easiest way to handle this is to have a single function that handles all
changes in settings-related widgets, allowing this to be called once after
all changes have been made. A check that ``self.processor is not None`` should
always be made because the processor is only instantiated when acquisition begins.

``update_settings()`` is a reasonably slow function, since the entire ``ImageProcessorThread``
must be pickled, piped to the other process, and depickled. Although this is not noticeable
for occasional dicrete settings changes, it may becomes obvious if the user is able
to continuously adjust some setting and observe the results (e.g. by dragging a slider).
A faster way to update settings on both the local and other copy of the Image Processor Class
is to to use ``pipe_message()``. This takes two arguments, the first is the name of a method
of the Image Processor Class to call, and the second is a tuple of arguments to pass to this method.
This means that setter methods can be created in the Image Processor Class to handle and settings
changes that need to be made rapidly.
         

    