Customisation
=============

The widget appearance and behaviour can be customised as follows without sub-classing.

Overall Appearance
------------------

At creation, the following stylesheet is applied to the widget::

     setStyleSheet("border:1px solid white")
     
Apply a different stylesheet to change the overall appearance, e.g. to change or remove the border.
    

Status Bar
----------

Set the visibility of the status bar (visible by default)::

    set_status_bar(True/False)
    
    
To customise colours of the status bar, the following values can be set directly:  

* ``statusPen`` The border colour/style, provide a ``QPen``, such as ``QPen(Qt.white, 2, Qt.SolidLine)``.
* ``statusBrush`` The fill colour/style, provide a ``QBrush``, such as ``QBrush(Qt.white, Qt.SolidPattern)``.
* ``statusTextPen`` The font colour, provide a ``QPen``, such as ``QPen(Qt.black, 2, Qt.SolidLine)``.
    

Zoom 
---- 
 
To enable or disable zooming (enabled by default)::

    set_zoom_enabled(True/False)

To control how much a mouse wheel scroll or pinch zoom changes the zoom, use::

    set_zoom_step_divider(zoomDivider)
      
where a bigger value of ``zoomDivider`` makes the amount zoomed in by each mouse wheel click smaller. The zoom is (base 2) logarithmic. A value of ``1`` means the zoom will go as 1X, 2X, 4X, 8X, 16X etc. Default is 2.
 
Set the visibility of the zoom indicator using::

    set_zoom_indicator_enabled(True/False)

To customise colours of the zoom indicator, the following values can be set directly:  

* ``zoomIndicatorPen`` The colour of the zoom indicator, provide a ``QPen`` such as  ``QPen(Qt.white, 1, Qt.SolidLine)``.
* ``zoomIndicatorBrush`` The fill colour of the zoom indicator, provide a ``QBrush`` such as ``QBrush(Qt.white, Qt.SolidPattern)``.
* ``zoomIndicatorWidth`` With of zoom indicator, default 60.
* ``zoomIndicatorOffsetX`` Horizontal position of zoom indicator, relative to top right corner of image, default 20.
* ``zoomIndicatorOffsetY`` Vertical position of zoom indicator, relative to top right corner of image, default 20.


Region of Interest (ROI)
-------------------------
Set whether a ROI can be dragged using::

    set_roi_enabled(True/False)

To customise colours, the following values can be set directly:  

* ``roiDragContrastPen`` The colour/style of the first rectangle to be drawn while the ROI is being dragged, provide a ``QPen`` such as ``QPen(Qt.white, 2, Qt.SolidLine)``.
* ``roiDragPen`` The colour/style of the second rectangle to be drawn while the ROI is being dragged. This is drawn over the first rectangle and so should usually be a dotted/dashed line of a different colour to help improve visibility when colour images are displayed. Provide a ``QPen`` such as ``QPen(Qt.red, 2, Qt.DotLine)``.
* ``roiContrastPen`` The colour/style of the first rectangle to be drawn of an ROI which has been set. Provide a ``QPen`` such as ``Pen(Qt.white, 2, Qt.SolidLine)``.
* ``roiPen`` The colour/style of the second rectangle to be drawn of an ROI which has been set. This is drawn over the first rectangle and so should usually be a dotted/dashed line of a different colour to help improve visibility when colour images are displayed. Provide a ``QPen`` such as ``QPen(Qt.green, 2, Qt.DotLine)``.
