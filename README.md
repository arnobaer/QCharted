# QCharted

Plotting large data series using [PyQtChart](https://www.riverbankcomputing.com/software/pyqtchart/intro).

Currently supports `LineSeries`, `SplineSeries` and `ScatterSeries`.

## Quick start

Install using pip.

```bash
pip install git+https://github.com/arnobaer/QCharted.git@1.1.1
```

Create a plot widget, assign two axes and some line series.

```python
import sys
from PyQt5 import QtCore, QtWidgets
from QCharted import Chart, ChartView

app = QtWidgets.QApplication(sys.argv)

# Create chart
chart = Chart()

# Create multiple axis
x = chart.addDateTimeAxis(QtCore.Qt.AlignBottom)
x.setTitleText("Time")
y1 = chart.addValueAxis(QtCore.Qt.AlignLeft)
y1.setTitleText("Temp")
y2 = chart.addValueAxis(QtCore.Qt.AlignRight)
y2.setTitleText("Humid")

# Create multiple series
temp = chart.addLineSeries(x, y)
temp.setPen(QtCore.Qt.red)
humid = chart.addLineSeries(x, y)
humid.setPen(QtCore.Qt.blue)

# Replace data, note the `data()` method
temp.data().replace([(0, 21.8), (1, 22.3)])
humid.data().replace([(0, 50.3), (1, 51.1)])

# Append data, note the `data()` method
temp.data().append(2, 22.1)
humid.data().append(2, 51.0)

# Create chart view
view = ChartView()
view.setChart(chart)
view.show()

# Fit to extent
chart.fit()

app.exec_()
```

## Custom series classes

Actual data is stored in a `data` property using `numpy`.

```python
# Instead of QLineSeries()
series = LineSeries()
# Replace data
series.data().replace([...])
# Append to data
series.data().append(2, 3)
# Clear data
series.data().clear()
```


## Example application

The supplied example application renders 16 x 250k data samples fluently even while
zooming. The QtChart line series only contain a sampled subset of the actual data. See
[examples/main.py](/examples/main.py) for the example source.

Make sure to first install additional dependencies provided in `requirements.txt`.

```bash
python -m venv env
. env/bin/activate
(env) pip install -r requirements.txt
(env) python setup.py develop
(env) python examples/main.py
```

Run the application with different options to see live plotting in action.

```bash
(env) python examples/main.py -c 8 -s 100
```

## License

QCharted is licensed under the [GNU General Public License Version 3](/LICENSE).
