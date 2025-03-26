Overlays
========

Five types of overlay are supported:

* Rectangle
* Ellipse
* Line
* Point
* Text

Overlays are added using the ``add_overlay`` function. This returns a reference to the overlay. 
This can be later passed to ``remove_overlay`` to delete the overlay.
Alternatively, all overlays can be removed using ``clear_overlays``.

To create a rectangular overlay::

   from image_display import ImageDisplay
   imDisplay = ImageDisplay()
   
   imDisplay.add_overlay(ImageDisplay.RECTANGLE, x, y, w, h, pen, fill)
      
where ``x`` and ``y`` are the x and y co-ordinates of the top left of the rectangle, respectively, and ``w`` and ``h`` are the width and height. 
These co-ordinates are specified in terms of pixels in the original image (i.e. not screen pixels). 
Co-ordinates outside the image can be specified in which case the overlay will be clipped. 

The ``pen`` and ``fill`` should be a ``QPen`` and ``QBrush`` respectively. For example::
   
   overlay = imDisplay.add_overlay(ImageDisplay.RECTANGLE, 90, 100, 30, 40, QPen(Qt.blue, 2, Qt.SolidLine), QBrush(Qt.red))

generates a rectangle with a blue solid outer line of thickness 2 and a red fill. For a transparent fill, pass ``None`` for ``fill``.   

To add an ellipse, the structure is::

   overlay = imDisplay.add_overlay(ImageDisplay.ELLIPSE, x, y, w, h, pen, fill)

For a line::

   overlay = imDisplay.add_overlay(ImageDisplay.LINE, x, y, w, h, pen)
   
For a point::   

   overlay = imDisplay.add_overlay(ImageDisplay.POINT, x, y, pen)
   
Note that no ``fill`` is specified for lines and points.

To add a text overlay::

   overlay = imDisplay.add_overlay(ImageDisplay.TEXT, x, y, pen, text)
   
where ``text`` is the string to add. The co-ordinates are the lower left of the bounding rectangle of the text box.   

To remove any overlay, use::

   imDisplay.remove_overlay(overlay)
   
where ``overlay`` is the reference returned when creating the overlay using ``add_overlay``. 

To clear all overlays use::

   imDisplay.clear_overlays()

   