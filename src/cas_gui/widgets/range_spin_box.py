from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox

class RangeSpinBox(QWidget):
    def __init__(self, label_text="", range_min=0.0, range_max=100.0, objectName="doubleSpinBoxWidget", connect = None, step = 0.01, parent=None):
        super().__init__(parent)

        # Set object name
        self.setObjectName(objectName)

        # Create label
        self.label = QLabel(label_text)

        # Create double spin boxes
        self.lower = QDoubleSpinBox()
        self.upper = QDoubleSpinBox()

        # Set ranges and step sizes for both spinboxes
        self.lower.setRange(range_min, range_max)
        self.upper.setRange(range_min, range_max)
        self.upper.setSingleStep(step)
        self.lower.setSingleStep(step)

        # Set object names for spinboxes
        self.lower.setObjectName(f"{objectName}_lower")
        self.upper.setObjectName(f"{objectName}_upper")

        # Layouts
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.spinbox_layout = QHBoxLayout()
        self.spinbox_layout.setContentsMargins(0, 0, 0, 0)

        # Add widgets to layouts
        self.main_layout.addWidget(self.label)
        self.main_layout.addLayout(self.spinbox_layout)
        self.spinbox_layout.addWidget(self.lower)
        self.spinbox_layout.addWidget(QLabel("to"))
        self.spinbox_layout.addWidget(self.upper)

        # Set the layout
        self.setLayout(self.main_layout)

        # Set connection
        if connect is not None:
            self.lower.valueChanged.connect(connect)
            self.upper.valueChanged.connect(connect)

    def set_step(self, step):
        self.upper.setSingleStep(step)
        self.lower.setSingleStep(step)

    def disable(self):
        self.lower.setEnabled(False)
        self.upper.setEnabled(False)

    def enable(self):
        self.lower.setEnabled(True)
        self.upper.setEnabled(True)


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    widget = RangeSpinBox(
        label_text="Set the range:",
        range_min=0.0,
        range_max=50.0,
        objectName="customRangeWidget"
    )
    widget.show()

    sys.exit(app.exec_())
