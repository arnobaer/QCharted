import argparse
import logging
import random
import sys
import time
import threading

import numpy as np
import namegenerator

from PyQt5 import QtCore, QtWidgets
from QCharted import DataSeries, Chart, ChartView

class FakeDataSeries(DataSeries):

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.__value = .50

    def fill(self, count):
        points = []
        for i in range(count):
            x = i + random.uniform(0.4, 0.5) + 1570000000.0
            self.__value += random.uniform(-.25,+.25)
            y = self.__value
            points.append((x, y))
        self.replace(points)

    def extend(self):
        self.__value += random.uniform(-.25,+.25)
        x = self.last()[0] + random.uniform(.4, .5)
        self.append(x, self.__value)

class FakeProducer(object):
    """Generates initial set of random data for series."""

    def __init__(self, count, samples):
        self.count = count
        self.samples = samples

    def generate(self):
        logging.info("start faking %sx%s samples...", self.count, self.samples)
        series = []
        for i in range(self.count):
            name = namegenerator.gen().split('-', 1)[-1]
            s = FakeDataSeries(name)
            logging.info("creating %s samples for series %s...", self.samples, s.name)
            s.fill(self.samples)
            series.append(s)
        logging.info("...done.")
        return series

class SourceThread(threading.Thread):
    """Keep pushing data to series."""

    interval = .5 # seconds

    def __init__(self, chart):
        super().__init__()
        self.chart = chart
        self.__active = True

    def stop(self):
        self.__active = False

    def run(self):
        while self.__active:
            series = self.chart.series()
            for i in range(len(series)):
                series[i].data().extend()
                # Update series horizontal range (showing live updates)
                series[i].fitHorizontal()
            # If not zoomed, fit data
            if not self.chart.isZoomed():
                self.chart.fit()
            logging.info("%s samples appended...", len(series))
            time.sleep(self.interval)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='count', type=int, default=16, help="series count (default 16)")
    parser.add_argument('-s', dest='samples', type=int, default=250000, help="samples count (default 250k)")
    parser.add_argument('-r', dest='resolution', type=int, default=600, help="plot resolution (default 600)")
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    app = QtWidgets.QApplication(sys.argv)

    # Create chart
    chart = Chart()
    chart.setResolution(args.resolution)
    chart.legend().setAlignment(QtCore.Qt.AlignRight)

    # Add X axis
    x = chart.addDateTimeAxis(QtCore.Qt.AlignBottom)
    x.setTitleText('Date/Time')

    # Add Y Axis
    y = chart.addValueAxis(QtCore.Qt.AlignLeft)
    y.setTitleText('Magnitude')

    # Create fake data series
    for s in FakeProducer(args.count, args.samples).generate():
        series = chart.addLineSeries(x, y)
        series.setName(s.name)
        series.setData(s)
        series.setPen(series.pen().color())

    # Fit all series
    chart.fit()

    # Run source thread, add data continuously
    thread = SourceThread(chart)
    thread.start()

    # Create chart view
    view = ChartView()
    view.setChart(chart)
    view.setWindowTitle("{} x {} Samples".format(args.count, args.samples))
    view.resize(900, 600)
    view.show()

    # Run application loop
    result = app.exec_()

    # Stop source thread
    thread.stop()
    thread.join()

    return result

if __name__ == '__main__':
    sys.exit(main())
