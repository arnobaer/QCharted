import numpy as np

import math
import threading
import re

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets, QtChart

__version__ = '1.1.1'

__all__ = ['ChartView', 'Chart']

milliseconds = 1000.

def toDateTime(seconds):
    """Returns seconds as QDateTime object."""
    return QtCore.QDateTime.fromMSecsSinceEpoch(seconds * milliseconds)

def toSecs(datetime):
    """Returns QDateTime object as seconds."""
    return datetime.toMSecsSinceEpoch() / milliseconds

def toMSecs(seconds):
    """Returns QDateTime object as milli seconds."""
    return seconds * milliseconds

def stripHtml(html):
    html = re.sub(r'<[^>]+>', ' ', html)
    html = re.sub(r'&[^;]*;', ' ', html)
    html = re.sub(r'\s+', ' ', html)
    return html

class DataSeries:
    """2D data series using numpy arrays.

    >>> series = DataSeries([(0, 1), (2, 3)])
    >>> series.append(4, 5)
    >>> series.replace([(2, 3), (4, 5), (6, 7)])
    >>> series.bounds()
    ((2, 3), (6, 7))
    """

    def __init__(self, points=[]):
        self.replace(points)

    def clear(self):
        self.__x = np.array([])
        self.__y = np.array([])
        self.__xmin = None
        self.__xmax = None
        self.__ymin = None
        self.__ymax = None

    def append(self, x, y):
        self.__x = np.append(self.__x, x)
        self.__y = np.append(self.__y, y)
        if len(self.__x) > 1:
            self.__xmin = min(self.__xmin, x)
            self.__xmax = max(self.__xmax, x)
            self.__ymin = min(self.__ymin, y)
            self.__ymax = max(self.__ymax, y)
        else:
            self.__xmin = x
            self.__xmax = x
            self.__ymin = y
            self.__ymax = y

    def replace(self, points):
        if len(points):
            points = zip(*points)
            self.__x = np.array(next(points))
            self.__y = np.array(next(points))
            self.__xmin = np.amin(self.__x)
            self.__xmax = np.amax(self.__x)
            self.__ymin = np.amin(self.__y)
            self.__ymax = np.amax(self.__y)
        else:
            self.clear()

    def first(self):
        return self.__x[0], self.__y[0]

    def last(self):
        return self.__x[-1], self.__y[-1]

    def at(self, index):
        return self.__x[index], self.__y[index]

    def xpos(self, value):
        """Returns nearest index for value on ordered series on x axis."""
        return np.abs(self.__x - value).argmin()

    def bounds(self):
        return (self.__xmin, self.__xmax), (self.__ymin, self.__ymax)

    def sample(self, begin, end, count):
        """Returns a sampling generator, up to `count` samples between `begin` and `end`.

        >>> series = DataSeries()
        >>> list(series.sample(100, 200, 25))
        [...]
        """
        assert begin <= end
        assert count > 0
        size = self.__x.size
        if size < 1:
            return iter([])
        begin_index = max(0, self.xpos(begin) - 1)
        end_index = min(size - 1, self.xpos(end) + 1)
        step = int(max(1, math.ceil((end_index - begin_index) / count)))
        for i in range(count):
            if begin_index >= end_index:
                yield self.at(end_index)
                break
            yield self.at(begin_index)
            begin_index += step

    def __len__(self):
        return self.__x.size

class DataSetMixin:
    """Mixin class to extend data series classes with a dataset attribute."""

    def fitHorizontal(self):
        for axis in self.attachedAxes():
            if axis.orientation() == QtCore.Qt.Horizontal:
                self.chart().updateAxis(axis, axis.min(), axis.max())
                break

    def data(self):
        try:
            return self.__data
        except AttributeError:
            self.setData(DataSeries())
            return self.__data

    def setData(self, data):
        if isinstance(data, (list, tuple)):
            data = DataSeries(data)
        self.__data = data

class ValueAxis(QtChart.QValueAxis):
    """Custon value axis."""

    pass

class LogValueAxis(QtChart.QLogValueAxis):
    """Custom log value axis."""

    pass

class DateTimeAxis(QtChart.QDateTimeAxis):
    """Custom date time axis."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default multi-line label with indented time
        indent = '&#160;' * 6
        self.setFormat('dd-MM-yyyy<br/>{}hh:mm'.format(indent))

class CategoryAxis(QtChart.QCategoryAxis):
    """Custom category axis."""

    pass

class LineSeries(QtChart.QLineSeries, DataSetMixin):
    """Custom line series."""

    pass

class SplineSeries(QtChart.QSplineSeries, DataSetMixin):
    """Custom spline series."""

    pass

class ScatterSeries(QtChart.QScatterSeries, DataSetMixin):
    """Custom scatter series."""

    pass

class MarkerGraphicsItem(QtWidgets.QGraphicsRectItem):
    """Marker graphics item for series data."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setValueFormat("G")
        self.setTextFormat("({x}, {y}) {name}")
        self.polygon = QtWidgets.QGraphicsPolygonItem(self)
        self.text = QtWidgets.QGraphicsTextItem(self)

    def valueFormat(self):
        return self.__valueFormat

    def setValueFormat(self, format):
        """Format for numeric values, default is `G`."""
        self.__valueFormat = format

    def textFormat(self):
        return self.__textFormat

    def setTextFormat(self, format):
        """Format can contain following placeholders `{x}`, `{y}` and `{name}`."""
        self.__textFormat = format

    def setSeriesText(self, series, point):
        point = [point.x(), point.y()]
        for i, axis in enumerate(series.attachedAxes()):
            if isinstance(axis, QtChart.QDateTimeAxis):
                point[i] = toDateTime(point[i] / milliseconds).toString(stripHtml(axis.format()))
            elif isinstance(axis, QtChart.QBarCategoryAxis):
                point[i] = format(point[i])
            else:
                point[i] = format(point[i], self.valueFormat())
        self.text.setPlainText(self.textFormat().format(x=point[0], y=point[1], name=series.name()))

    def setSeriesColor(self, color):
        # Set primary text and background color
        self.polygon.setBrush(QtGui.QBrush(color))
        # https://stackoverflow.com/questions/3942878/how-to-decide-font-color-in-white-or-black-depending-on-background-color
        if (color.red()*0.299 + color.green()*0.587 + color.blue()*0.114) > 186:
            penColor = QtGui.QColor(70, 70, 70)
        else:
            penColor = QtGui.QColor(255, 255, 255)
        self.text.setDefaultTextColor(penColor)
        self.polygon.setPen(penColor)

    def updateGeometry(self):
        rect = self.text.boundingRect()
        # Divide height by four to create left point
        quarter = rect.height() / 4
        self.text.setPos(rect.topLeft() + QtCore.QPointF(quarter, -rect.height() / 2))
        # Create pointed left label box
        polygon = QtGui.QPolygonF([
            rect.topLeft(),
            rect.topLeft() + QtCore.QPointF(0, quarter * 1),
            rect.topLeft() + QtCore.QPointF(-quarter, quarter * 2),
            rect.topLeft() + QtCore.QPointF(0, quarter * 3),
            rect.bottomLeft(),
            rect.bottomRight(),
            rect.topRight(),
        ])
        self.polygon.setPolygon(polygon)
        self.polygon.setPos(rect.topLeft().x() + quarter, rect.topLeft().y() - rect.height() / 2)

    def place(self, series, point):
        """Place marker for `series` at position of `point`."""
        visible = series.at(0).x() <= point.x() <= series.at(series.count()-1).x() and self.isVisible()
        self.setVisible(visible and series.chart().plotArea().contains(self.pos()))
        self.setPos(series.chart().mapToPosition(point))
        self.setSeriesText(series, point)
        self.setSeriesColor(series.pen().color())
        self.updateGeometry()

class ToolbarButton(QtWidgets.QPushButton):
    """Base class for toolbar buttons."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(24, 24)

class ViewAllButton(ToolbarButton):
    """View all toolbar button."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setIcon(self.createIcon())
        self.setToolTip(self.tr("View All"))

    def createIcon(self):
        """Creates icon for toolbar button."""
        pixmap = QtGui.QPixmap(64, 64)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 4))
        painter.drawLine(0, 0, 63, 63)
        painter.drawLine(63, 0, 0, 63)
        painter.drawLine(0, 0, 0, 15)
        painter.drawLine(0, 0, 15, 0)
        painter.drawLine(47, 0, 63, 0)
        painter.drawLine(63, 0, 63, 15)
        painter.drawLine(0, 47, 0, 63)
        painter.drawLine(0, 63, 15, 63)
        painter.drawLine(47, 63, 63, 63)
        painter.drawLine(63, 63, 63, 47)
        painter.end()
        return QtGui.QIcon(pixmap)

class FitHorizontalButton(ToolbarButton):
    """Fit horizontal toolbar button."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setIcon(self.createIcon())
        self.setToolTip(self.tr("Fit Horizontal"))

    def createIcon(self):
        """Creates icon for toolbar button."""
        pixmap = QtGui.QPixmap(64, 64)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 4))
        painter.drawLine(0, 31, 63, 31)
        painter.drawLine(15, 15, 0, 31)
        painter.drawLine(0, 31, 15, 47)
        painter.drawLine(47, 15, 63, 31)
        painter.drawLine(63, 31, 47, 47)
        painter.end()
        return QtGui.QIcon(pixmap)

class FitVerticalButton(ToolbarButton):
    """Fit horizontal toolbar button."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setIcon(self.createIcon())
        self.setToolTip(self.tr("Fit Vertical"))

    def createIcon(self):
        """Creates icon for toolbar button."""
        pixmap = QtGui.QPixmap(64, 64)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 4))
        painter.drawLine(31, 0, 31, 63)
        painter.drawLine(15, 15, 31, 0)
        painter.drawLine(31, 0, 47, 15)
        painter.drawLine(15, 47, 31, 63)
        painter.drawLine(31, 63, 47, 47)
        painter.end()
        return QtGui.QIcon(pixmap)

class ToggleMarkerButton(ToolbarButton):
    """Toggle marker toolbar button."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setIcon(self.createIcon())
        self.setCheckable(True)
        self.setToolTip(self.tr("Toggle Marker"))

    def createIcon(self):
        """Creates icon for toolbar button."""
        pixmap = QtGui.QPixmap(64, 64)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 4))
        painter.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        polygon = QtGui.QPolygon([
            QtCore.QPoint(0, 31),
            QtCore.QPoint(15, 15),
            QtCore.QPoint(63, 15),
            QtCore.QPoint(63, 47),
            QtCore.QPoint(15, 47)
        ])
        painter.drawPolygon(polygon)
        painter.end()
        return QtGui.QIcon(pixmap)

class Toolbar(QtWidgets.QWidget):

    viewAll = QtCore.pyqtSignal()
    fitHorizontal = QtCore.pyqtSignal()
    fitVertical = QtCore.pyqtSignal()
    toggleMarker = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(2, 2, 2, 2)
        self.layout().setSpacing(2)
        self.setStyleSheet('Toolbar {background-color: transparent;}')
        # View all button
        button = ViewAllButton()
        button.clicked.connect(self.viewAll.emit)
        self.layout().addWidget(button)
        # Fit horizontal button
        button = FitHorizontalButton()
        button.clicked.connect(self.fitHorizontal.emit)
        self.layout().addWidget(button)
        # Fit horizontal vertical
        button = FitVerticalButton()
        button.clicked.connect(self.fitVertical.emit)
        self.layout().addWidget(button)
        # Toggle marker button
        button = ToggleMarkerButton()
        button.toggled.connect(self.toggleMarker.emit)
        self.layout().addWidget(button)

class Chart(QtChart.QChart):
    """Custom chart class."""

    def __init__(self):
        super().__init__()
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setBackgroundRoundness(0)
        self.setResolution(800)

    def resolution(self):
        return self.__resolution

    def setResolution(self, count):
        self.__resolution = count

    def addValueAxis(self, align):
        return self.addAxis(ValueAxis(), align)

    def addLogValueAxis(self, align):
        return self.addAxis(LogValueAxis(), align)

    def addDateTimeAxis(self, align):
        return self.addAxis(DateTimeAxis(), align)

    def addCategoryAxis(self, align):
        return self.addAxis(CategoryAxis(), align)

    def addBarCategoryAxis(self, align):
        return self.addAxis(BarCategoryAxis(), align)

    def addAxis(self, axis, align):
        def updateAxis(minimum, maximum):
            self.updateAxis(axis, minimum, maximum)
        axis.rangeChanged.connect(updateAxis)
        super().addAxis(axis, align)
        return axis

    def addLineSeries(self, x, y, parent=None):
        return self.addSeries(LineSeries(parent), x, y)

    def addSplineSeries(self, x, y, parent=None):
        return self.addSeries(SplineSeries(parent), x, y)

    def addScatterSeries(self, x, y, parent=None):
        return self.addSeries(ScatterSeries(parent), x, y)

    def addSeries(self, series, x, y):
        super().addSeries(series)
        series.attachAxis(x)
        series.attachAxis(y)
        return series

    def bounds(self):
        """Returns bounding box of all series."""
        series = self.series()
        if len(series):
            minimumX = []
            maximumX = []
            minimumY = []
            maximumY = []
            for series in series:
                if len(series.data()):
                    if isinstance(series, DataSetMixin):
                        x, y = series.data().bounds()
                    minimumX.append(x[0])
                    maximumX.append(x[1])
                    minimumY.append(y[0])
                    maximumY.append(y[1])
            if len(minimumX):
                return (min(minimumX),  max(maximumX)), (min(minimumY),  max(maximumY))
        return ((0., 1.), (0., 1.)) # default bounds

    def fitHorizontal(self):
        bounds = self.bounds()
        for axis in self.axes(QtCore.Qt.Horizontal):
            if isinstance(axis, QtChart.QDateTimeAxis):
                axis.setRange(toDateTime(bounds[0][0]), toDateTime(bounds[0][1]))
            else:
                axis.setRange(bounds[0][0], bounds[0][1])

    def fitVertical(self):
        bounds = self.bounds()
        for axis in self.axes(QtCore.Qt.Vertical):
            if isinstance(axis, QtChart.QDateTimeAxis):
                axis.setRange(toDateTime(bounds[1][0]), toDateTime(bounds[1][1]))
            elif isinstance(axis, QtChart.QCategoryAxis):
                axis.setRange(axis.min(), axis.max())
            else:
                axis.setRange(bounds[1][0], bounds[1][1])

    def fit(self):
        self.zoomReset()
        self.fitHorizontal()
        self.fitVertical()

    @QtCore.pyqtSlot(object, float, float)
    def updateAxis(self, axis, minimum, maximum):
        if axis in self.axes(QtCore.Qt.Horizontal):
            if isinstance(axis, QtChart.QDateTimeAxis):
                minimum = toSecs(minimum)
                maximum = toSecs(maximum)
            for series in self.series():
                if axis in series.attachedAxes():
                    generator = series.data().sample(minimum, maximum, self.resolution())
                    if isinstance(axis, QtChart.QDateTimeAxis):
                        points = (QtCore.QPointF(toMSecs(x), y) for x, y in generator)
                    else:
                        points = (QtCore.QPointF(x, y) for x, y in generator)
                    series.replace(points) # assign a generator object

class ChartView(QtChart.QChartView):
    """Custom chart view class providing a toolbar and points marker and a
    default chart instance on creation.
    """

    MarkerRadius = 16

    def __init__(self, parent=None):
        super().__init__(Chart(), parent)
        self.__createToolbar()
        self.setMarkerEnabled(False)
        self.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.setMarker(MarkerGraphicsItem())
        # Store mouse pressed state
        self.__mousePressed = False

    def __createToolbar(self):
        # Create toolbar widget without parent, see below.
        self.__toolbar = Toolbar()
        self.__toolbar.viewAll.connect(lambda: self.chart().fit())
        self.__toolbar.fitHorizontal.connect(lambda: self.chart().fitHorizontal())
        self.__toolbar.fitVertical.connect(lambda: self.chart().fitVertical())
        self.__toolbar.toggleMarker.connect(self.setMarkerEnabled)
        proxyWidget = self.scene().addWidget(self.__toolbar)
        proxyWidget.setPos(0, 0)
        proxyWidget.setZValue(10000)
        # Set parent after adding widget to scene to trigger
        # widgets destruction on close of chart view.
        self.__toolbar.setParent(self)

    def toolbar(self):
        return self.__toolbar

    def marker(self):
        return self.__marker

    def setMarker(self, item):
        self.__marker = item
        item.setZValue(100)
        self.scene().addItem(item)

    def setMarkerEnabled(self, enabled):
        self.__setMarkerEnabled = enabled

    def isMarkerEnabled(self):
        return self.__setMarkerEnabled

    def isMousePressed(self):
        return self.__mousePressed

    def mousePressEvent(self, event):
        self.__mousePressed = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.__mousePressed = False
        super().mouseReleaseEvent(event)

    def nearestPoints(self, series, pos):
        items = []
        chart = self.chart()
        for point in series.pointsVector():
            distance = (pos - chart.mapToPosition(point)).manhattanLength()
            items.append((distance, series, point))
        items.sort(key=lambda item: item[0])
        return items

    def mouseMoveEvent(self, event):
        """Draws marker and symbols/labels."""
        chart = self.chart()
        # Position in data
        value = chart.mapToValue(event.pos())
        # Position in plot
        pos = chart.mapToScene(event.pos())
        # Hide if mouse pressed (else collides with rubber band)
        visible = chart.plotArea().contains(pos)
        visible = visible and self.isMarkerEnabled()
        visible = visible and not self.isMousePressed()
        self.marker().setVisible(visible)
        if self.isMarkerEnabled():
            items = []
            for series in chart.series():
                points = self.nearestPoints(series, pos)
                if len(points):
                    items.append(points[0])
            items.sort(key=lambda item: item[0])
            if len(items):
                distance, series, point = items[0]
                if distance < self.MarkerRadius:
                    self.marker().place(series, point)
                else:
                    self.marker().setVisible(False)
        super().mouseMoveEvent(event)
