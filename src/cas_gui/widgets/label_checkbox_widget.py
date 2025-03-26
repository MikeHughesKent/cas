from PyQt5.QtWidgets import QWidget, QLabel, QCheckBox, QHBoxLayout, QApplication
import sys

class LabelCheckboxWidget(QWidget):
    def __init__(self, label_text, parent=None, objectName=None, connect = None):
        super().__init__(parent)

        # Create the label and checkbox
        self.label = QLabel(label_text)
        self.checkbox = QCheckBox()

        # Set object names if provided
        if objectName:
            self.checkbox.setObjectName(objectName)
            self.setObjectName(objectName + "_container")

        # Set up the layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addStretch()  # Ensures proper alignment

        layout.addWidget(self.checkbox)

        if connect is not None:
            self.checkbox.stateChanged.connect(connect)

        # Apply the layout to the widget
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example usage
    window = LabelCheckboxWidget("Enable feature:", object_name="enableFeature")
    window.show()

    sys.exit(app.exec_())
