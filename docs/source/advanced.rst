Advanced Customisation
======================

Further customisation can be achieved by overriding additional functions and adding new ones. This page provides
some guidance to help with this process.

Changing GUI Appearance
^^^^^^^^^^^^^^^^^^^^^^^
The stylesheet in `res/style.css` can be used to change the appearance of the GUI. Elements of appearance
are also set in ``set_colour_scheme()`` which can be overridden to change these elements.


Image Acquisition and Camera Control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``ImageAcquisitionThread`` class runs as a thread to handle acquisition of frames from the camera. This thread
is started by the ``start_acquire()`` function of the GUI when when 'Live Imaging' is clicked. A reference
to this thread is stored in ``self.imageThread``, and a direct reference to the camera interface class is stored
in ``self.cam`` or can be obtained from ``self.imageThread.get_camera()``. This is the means by which camera
settings can be altered by the GUI class. See the ``update_camera_ranges_and_values()`` function for examples of 
getting camera properties, and ``exposure_slider_changed()``, ``gain_slider_changed()`` and 
``frame_rate_slider_changed()`` for examples of setting camera properties.

Each camera has its own class which subclasses the ``GenericCameraInterface`` class. See the Implementing Cameras page for more details
on how to create additional cameras.

The ``ImageAcquisitionThread`` thread opens the camera, using the ``open_camera()`` function of the selected camera, and then
continuously grabs images and places them into a queue. This queue is created in the GUI class (``self.inputQueue``) and passed to the ``ImageAcquisitionThread``. 
The queue is then also shared with the ``ImageProcessorThread`` so that this has direct access to the queue of images.


Image Handling
^^^^^^^^^^^^^^
The function ``handle_image()`` is called regularly by a timer. This function pulls the latest raw and 
processed images off their respective queues. It does not update the live image display which is handled
by a separate function running off a different timer, ``update_image_display()``. 

If direct recording is currently active, this function also calls the ``record()`` function to record the current frame, if recording to a buffer is currently active, this function
checks if the buffer has been filled with the required number of images, and if so calls ``stop_buffering()``.

No image processing should be done here to avoid slowing the user interface thread.


Image Saving
^^^^^^^^^^^^
The utility functions ``save_image()`` and ``save_image_ac()`` in the GUI are used to snap or save images and can
be used for other purposes. Both save 16 bit images, ``save_image_ac()`` rescales the image to use the full range before saving.


Background Images
^^^^^^^^^^^^^^^^^
As the need to acquire a background or reference image  is common, CAS GUI includes helper functions ``load_background()``, and ``save_background()``. These
load and save, respectively, the image stored in ``self.background`` to the filename stored in ``self.defaultBackgroundFile``, which by default is "background.tif".
Alternatively, ``load_background_from()`` and ``save_background_to()`` will use the filename passed as an argument.


Info Bar
^^^^^^^^
The bottom information bar is periodically updated by the ``update_info_bar()`` function, override
this to include custom information.


Recording
^^^^^^^^^
If recording raw images, a second queue (called the auxillary queue) is used. The ``ImageAcquisitionThread``
places a copy of raw images in this thread as well as the main thread. The function ``handle_image()`` periodically 
checks to see when this queue has been filled to the required number of frames, and ``record_buffer_full()`` is then
called to handle saving the images in the buffer to disk.


