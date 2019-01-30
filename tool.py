from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5 import QtGui


class Pen:
    def handleObject(self, mapSurface, position, selectedObject, button):
        if button != Qt.LeftButton:
            return
        if not selectedObject:
            objectPreview = mapSurface.editor.ui.objectPreviewFrame
            mapSurface.addObject(objectPreview.createObject(position))
    def handleTile(self, mapSurface, position, selectedObject, button):
        if button != Qt.LeftButton:
            return
        tilePreview = mapSurface.editor.ui.tilePreviewFrame
        tile = tilePreview.createTile(position)
        if not selectedObject and tile:
            mapSurface.addTile(tile)


class Brush:
    pass


class ToolHandler:
    def __init__(self, ui):
        group = QActionGroup(ui.toolBar)
        group.addAction(ui.actionPen)
        group.addAction(ui.actionBrush)
        self.group = group
        self.actionBrush = ui.actionBrush
        self.actionPen = ui.actionPen
        group.triggered.connect(self.triggered)
        self.tool = Pen()
    def triggered(self):
        if self.group.checkedAction() == self.actionBrush:
            self.selectBrush()
        else:
            self.selectPen()
    def selectBrush(self):
        print('brush')
        self.tool = Brush()
    def selectPen(self):
        print('pen')
        self.tool = Pen()
    def handleMapSurfaceClick(self, mapSurface, position, selectedObject, button):
        if mapSurface.tileResizeHover:
            return
        if mapSurface.window().ui.tabWidget.currentIndex() == 0:
            # object
            objectPreview = mapSurface.editor.ui.objectPreviewFrame
            if objectPreview.type:
                self.tool.handleObject(mapSurface, position, selectedObject, button)
        elif mapSurface.window().ui.tabWidget.currentIndex() == 1:
            # tile
            tilePreview = mapSurface.editor.ui.tilePreviewFrame
            if not tilePreview.image.isNull() and not tilePreview.selection.isNull():
                self.tool.handleTile(mapSurface, position, selectedObject, button)
