import sys

from PyQt5 import QtCore, QtWidgets
from QCharted import ChartView

def main():
    app = QtWidgets.QApplication(sys.argv)

    view = ChartView()
    view.setWindowTitle("Empty")
    view.resize(800, 600)
    chart = view.chart()

    # Reset view
    chart.fit()

    # Show window
    view.show()

    # Run application loop
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
