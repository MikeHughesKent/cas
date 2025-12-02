# -*- coding: utf-8 -*-
"""
Widget for a labelled double spin box
"""

from PyQt5.QtWidgets import QWidget, QLabel, QDoubleSpinBox, QHBoxLayout, QApplication
import sys

class LabelDoubleSpinWidget(QWidget):
    def __init__(self, label_text, parent=None, objectName=None, connect=None, minVal = 0, maxVal = 100):
        super().__init__(parent)

        # Create the label and spinbox
        self.label = QLabel(label_text)
        self.spinbox = QDoubleSpinBox()

        # Optional: set object name
        if objectName:
            self.spinbox.setObjectName(objectName)
            self.setObjectName(objectName + "_container")

        # Layout setup
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.spinbox)

        # Optional: connect signal
        if connect is not None:
            self.spinbox.valueChanged.connect(connect)
            
        self.spinbox.setMaximum(maxVal)
        self.spinbox.setMinimum(minVal)
        

        self.setLayout(layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        total_width = self.width()
        spin_width = int(total_width * 0.5)
        self.spinbox.setFixedWidth(spin_width)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example usage
    def value_changed(v):
        print("Value:", v)

    window = LabelDoubleSpinWidget("Set value:", objectName="valueSpin", connect=value_changed)
    window.show()

    sys.exit(app.exec_())
