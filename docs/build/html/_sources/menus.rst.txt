Adding Menus and Menu Items
===========================

By default there is a settings menu in the GUI which can be used to put widgets
to control the image processing (or for any other purpose). To add items to this menu, 
the ``add_settings`` method is be over-ridden. This must take
one parameter which is the PyQt layout for the settings menu. Widgets should be created
in the normal way in PyQt and then added to this layout. For example ::

  def add_settings(self, settingsLayout):
     """ We override this function to add custom options to the setings menu
     panel.
     """
     
     # Filter Checkbox
     self.filterCheckBox = QCheckBox("Apply Filter", objectName = 'FilterCheck')
     settingsLayout.addWidget(self.filterCheckBox)  
     self.filterCheckBox.stateChanged.connect(self.processing_options_changed)
         
    
In this example, a checkbox has been added to the menu. It is normally useful
to store a reference to the widget, which is done simply by assigning it to a variable
within ``self``, i.e. the GUI class. This can then be accessed from anywhere within the class.

The function used to handle a change of the state of the widget should also be added. Here
this has been defined as ``self.processing_options_changed``. This needs to be defined::

  def processing_options_changed(self,event):
      """ Function to handle a change in the state of one or more widgets """
      
In this example, the state of the checkbox could then be obtained from ``self.filterCheckBox.isChecked()``.

Entirely new menu options can also be created. This requires over-riding the ``create_layout`` method. To obtain a new expanding menu we can use::

    def create_layout(self):
        
        super().create_layout()
        self.myPanelButton = self.create_menu_button(text = "My Menu", 
                                                     handler = self.my_menu_button_clicked, 
                                                     menuButton = True, 
                                                     position = 2)
            
        self.myPanel = self.create_my_panel()
        
Note that we first call ``super().create_layout()``, otherwise we will prevent the rest of the layout from being created. Then we create the menu button using
``self.create_menu_button``. We specify the ``text`` for the button, the ``handler`` function to be called when the button is clicked, the ``position`` for the button on the menu bar (0 is at the top, etc.). 
We have also specified ``menuButton = True``. This will cause the button to work to toggle the expanding menu on or off.
     
We now have to create the explanding menu and set it to open when the button is clicked. We implement::

    def my_menu_button_clicked(self):
        
        self.expanding_menu_clicked(self.myMenuButton, self.myPanel)

which makes use of the helper function ``expanding_menu_clicked()``. 

We also need to define the method to create the panel::

    def create_my_panel(self):
   
        widget, layout = self.panel_helper(title = "My Menu")
       
        # Filter Checkbox
        self.filterCheckBox = QCheckBox("Apply Filter", objectName = 'FilterCheck')
        layout.addWidget(self.filterCheckBox)  
        self.filterCheckBox.stateChanged.connect(self.processing_options_changed)  
        
        layout.addStretch()
           
        return widget
        
Note that this function needs to create a container widget and layout using the ``panel_helper`` method. We then add whatever
widgets we like to the layout, with connections to handler functions. Finally we add a stretch and then the function must return 
a reference to the container widget.

We can also add menu buttons that do not open an expanding menu, but perform some other task. In this case we simply
add the button::

  def create_layout(self):
      
      super().create_layout()
      self.myMenuButton = self.create_menu_button(text = "My Button", 
                                                  handler = self.my_button_clicked, 
                                                  position = 2)
     
where we have no longer set ``menuButton = True``. We then need to implement ``my_button_clicked`` with the required functionality.     

We can make the button latch by passing ``hold = True``. In this case we toggle the button between on and off
with each click. The handler function can check whether the button is toggled on or off using ``self.myPanelButton.isChecked()`` or change the state
using ``self.myPanelButton.setChecked(True/False)``.

A complete example of a GUI with custom buttons and a menu and used a menu items to control
the image processing is in 'examples/gui_example_menus.py'.

