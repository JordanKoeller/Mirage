from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow


class Window(QMainWindow):
  """Generic wndow object for loading views into. A very minimalist object with a "File" menu item to save, load, and quit."""
  windowQML = "mainwindow.ui"

  def __init__(self):
    QMainWindow.__init__(self)
    from os import environ, sep
    prefix = None
    if "MIRAGE_HOME" in environ:
      prefix = environ['MIRAGE_HOME'] + sep + "mirage" + sep + "views" + sep + "qml" + sep
    else:
      prefix = ""
    uic.loadUi(prefix + self.windowQML, self)
    self._save_action = lambda: print("Dummy")
    self._open_action = lambda: print("Dummy")
    self.actionOpen.triggered.connect(lambda: self._open_action())
    self.actionSave.triggered.connect(lambda: self._save_action())

  def bind_widget(self, widget):
    box = self.layoutBox
    box.addWidget(widget)
    self._widget = widget
    self._save_action, self._open_action = widget.actionTriggers()

  def get_object(self, *args, **kwargs):
    return self._widget.get_object(*args, **kwargs)

  def set_object(self, *args, **kwargs):
    return self._widget.set_object(*args, **kwargs)

  @property
  def widget(self):
    return self._widget
