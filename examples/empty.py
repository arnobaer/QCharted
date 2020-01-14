import sys

from PyQt5 import QtCore, QtWidgets
from QCharted import Chart, ChartView

def main():
    app = QtWidgets.QApplication(sys.argv)

    # Create chart view
    view = ChartView()
    view.setWindowTitle("Empty")
    view.resize(800, 600)
    view.show()

    # Run application loop
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
