
Using Multiple Cores
====================

An example of using multiple cores is in the example 'examples/gui_examples_multicore'.

To set the image processing to run on a separate core, set the GUI class variable::

    multiCore = True
    
CAS GUI will then handle starting a process. For very simple processors,
which do not require changes of parameters or calibration, this is all that
is required.


Processor Object Mirroring
^^^^^^^^^^^^^^^^^^^^^^^^^^
By default, CAS GUI first creates an instance of the image processor class on the local
process and then pipes a copy of it to the other process via a queue. This means that any 
subsequent changes to the local copy of the image processor class will not be
reflected in the copy in the other process. Therefore, if any changes are made
to the processor class, it is necessary to call the 
``update_settings()`` method of the instance of ``ImageProcessorThread`` a
reference to which is stored in the ``self.processor`` parameter. Therefore, following 
any change of settings, you should call::

    if self.processor is not None:
        self.processor.update_settings()

The easiest way to ensure this is always done is to have a single function that handles all
changes in settings-related widgets, allowing this to be called once after
all changes have been made. A check that ``self.processor is not None`` should
always be made because the processor is only instantiated when acquisition begins.

``update_settings()`` is a reasonably slow function, since the entire ``ImageProcessorThread``
must be pickled, piped to the other process, and depickled. Although this is not noticeable
for occasional discrete settings changes, it may becomes obvious if the user is able
to continuously adjust some setting and observe the results (e.g. by dragging a slider), 
in which case the alternative approach below can be used. Additionally, if the processor
class needs to keep track of anything it is not desirable to over-write it with the local
copy whenever settings are changed.

Remote-only Processor Object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A alternative way to update settings on the remote copy of the Image Processor Class
is to to use ``pipe_message()``. This takes two arguments, the first is the name of a method or attribute
of the Image Processor Class to call, and the second is a tuple of arguments to pass to this method or to set 
the attribute equal to. The local copy is not updated, and would need to be updated separately if
the two are to be kept in sync. It is usually best to choose one method of maintaining the remote processor class and stick to it, to avoid
diffcult to identify bugs. i.e., if using pipe_message() to update the remote Image Processor Class, the
local copy should no longer be used.

Shared Memory
^^^^^^^^^^^^^
By default, processed images will be returned from the Image Processor Class via a queue. For certain applications
where the returned image is very large, this can be slow. CAS GUI has the option to instead return the processed
image via an area of memory shared between the two cores by setting the GUI class attribute

    sharedMemory = True
    
While faster, there is now no longer any queue of returned images and dropped frame or race conditions are possible.



         

    