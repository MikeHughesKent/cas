Line Graphs
===========

ImageDisplayQT can display a simple line graph of a 1D numpy array. This functionality
is intended as a convenient way to display graphs in the same ImageDisplayQT
frame and offers only minimal functionality. For more complex graphs, packages 
such as PyQtGraph or Matplitlib should be used.


Import the ``ImageDisplay`` class::

    from image_display import ImageDisplay

Create an instance of ``ImageDisplay``::

    imDisplay = ImageDisplay()

and then add this widget to your GUI, eg. using ``addWidget``.

To display a graph, call::

    imDisplay.set_graph(graph)

where ``graph`` is a 1D numpy array.

Some customisation is provided by setting the following properties of the
instance of ImageDisplay:

* graphPen : QPen controlling appearance of graph line
* graphCursorBrush : QBrush controlling fill of cursor circle that appears when hovering over graph.
* graphCursorPen = QPen controlling appearance of cursor border
* graphCursorSize : int, size of cursor circle
* graphLabelPen : QPen for graph labels
* graphZeroPen : QPen for line drawn along y = 0
* graphDisplayMin : float, vertical scale minimum
* graphDisplayMax : float, vertical scale maximum

