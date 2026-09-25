from typing import Self
from abc import ABC, abstractmethod

from matplotlib.backends.qt_compat import QtWidgets


class Builder(ABC):
  @abstractmethod
  def build(self, parent: QtWidgets.QWidget | None = None) -> QtWidgets.QWidget:
    pass


class ButtonBuilder(Builder):
  __button_types_map = {
    "checkbox": QtWidgets.QCheckBox,
    "push": QtWidgets.QPushButton,
  }

  def __init__(self, button_type: str) -> None:
    if button_type not in ButtonBuilder.__button_types_map:
      raise ValueError(
        f"Unrecognized button type {button_type}. Options:\n{', '.join(ButtonBuilder.__button_types_map.keys())}"
      )
    self.button_type = button_type
    self.title = None
    self.callback = None
    self.active = True

  def set_label(self, label: str) -> Self:
    self.title = label
    return self

  def set_active(self, active: bool) -> Self:
    self.active = active
    return self

  def set_callback(self, func: callable) -> Self:
    self.callback = func
    return self

  def build(self, parent: QtWidgets.QWidget = None) -> QtWidgets.QToolButton:
    button = ButtonBuilder.__button_types_map[self.button_type](self.title, parent)
    if hasattr(button, "setChecked"):
      button.setChecked(self.active)
    if self.callback:
      button.clicked.connect(self.callback)
    return button


class PanelBuilder(Builder):
  def __init__(self, title: str = None) -> None:
    self.title = title
    self.checkbox_callback = None
    self.rows = []

  def set_checkbox_callback(self, callback: callable | None) -> Self:
    self.checkbox_callback = callback
    return self

  def set_title(self, title: str) -> Self:
    self.title = title
    return self

  def add_row(self, *widgets: list[QtWidgets.QWidget | Builder]) -> Self:
    self.rows.append(widgets)
    return self

  def build(self, parent: QtWidgets.QWidget = None) -> QtWidgets.QGroupBox:
    panel = QtWidgets.QGroupBox(self.title, parent)
    gridbox = QtWidgets.QGridLayout(panel)
    for ri, row in enumerate(self.rows):
      for ci, widget in enumerate(row):
        if isinstance(widget, Builder):
          widget = widget.build()
        gridbox.addWidget(widget, ri, ci)
    if self.checkbox_callback:
      panel.setCheckable(True)
      panel.toggled.connect(self.checkbox_callback)
    return panel
