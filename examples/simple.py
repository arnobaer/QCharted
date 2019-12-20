import random
import sys

from PyQt5 import QtCore, QtWidgets
from QCharted import ChartView

def main():
    app = QtWidgets.QApplication(sys.argv)

    view = ChartView()
    view.resize(800, 600)

    chart = view.chart()
    chart.legend().setAlignment(QtCore.Qt.AlignBottom)

    x = chart.addDateTimeAxis(QtCore.Qt.AlignBottom)
    y1 = chart.addValueAxis(QtCore.Qt.AlignLeft)
    y1.setTitleText("Temp [degC]")
    y1.setLinePenColor(QtCore.Qt.red)
    y2 = chart.addValueAxis(QtCore.Qt.AlignRight)
    y2.setTitleText("Humid [%rH]")
    y2.setLinePenColor(QtCore.Qt.blue)

    temp = chart.addLineSeries(x, y1)
    temp.setName("Temp")
    temp.setPen(QtCore.Qt.red)
    humid = chart.addLineSeries(x, y2)
    humid.setName("Humid")
    humid.setPen(QtCore.Qt.blue)

    temp.data().replace([(i, random.uniform(22, 25)) for i in range(32)])
    humid.data().replace([(i, random.uniform(50, 55)) for i in range(32)])

    view.show()
    chart.fit()

    app.exec_()

if __name__ == '__main__':
    sys.exit(main())
