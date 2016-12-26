# -*- coding: utf-8 -*-
import copy
import pickle
import sys

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QFileDialog)
from ui_editor import Ui_EditorWindow

class EditorException(Exception):
	pass

class EditStateContainer:
	'''pseudo-container used by EditState to track changes'''
	def __init__(self, container_type, callback = None):
		self.container = container_type()
	def __getattr__(self, key):
		print('notify parent here!')
		# FIXME: not attributes that make no edits
		return getattr(self.container, key)
	def __getitem__(self, key):
		return self.container[key]
	def __setitem__(self, key, val):
		print('notify parent here!')
		self.container[key] = val
	def setCallback(self, fn):
		self.cb = fn

l = EditStateContainer(list)
l.append(5)
print(l[0])
d = EditStateContainer(dict)
d['a'] = 10
print(d['a'])

class EditState:
	'''stores map data and detects changes to them'''
	_stateAttributes = ("height", "width", "objects",)
	_observe = False
	def __init__(self, editor, **kwargs):
		self._editor = editor
		self._pickleRequest = False
		# set defaults
		#self._data = dict()
		self.height = 100
		self.width = 100
		self.objects = []
		# set keyword values
		for k,v in kwargs.items():
			setattr(self, k, v)
		# inform editor of changes
		self._observe = True
	def __deepcopy__(self, memo):
		# only deep-copy map state (i.e. not the editor)
		new = EditState(self._editor)
		new._observe = False
		for a in self._stateAttributes:
			setattr(new, a, copy.deepcopy(getattr(self, a), memo))
		new._observe = True
		return new
	def equals(self, otherState):
		# compares two EditStates (by value, if necessary)
		if self == otherState: return True
		return pickle.dumps(self) == pickle.dumps(otherState)
	'''
	def __getattr__(self, name):
		attr = super(EditState, self).__getattr__(name)
		if type(attr) in (list, dict):
			print(1)
			attr = EditStateContainer(attr)
		return attr
	'''
	def __setattr__(self, name, val):
		if name[0] != '_':
			if name not in self._stateAttributes:
				raise EditorException("EditState: no such attribute: %s" % name)
			if self._observe:
				self._editor.stateBeforeChange(self, name, val)
		#	self._data[name] = val
		#else:
		#	super(EditState, self).__setattr__(name, val)
		super(EditState, self).__setattr__(name, val)

class Editor(QMainWindow):
	def __init__(self):
		# set up UI window
		super(Editor, self).__init__()
		self.ui = Ui_EditorWindow()
		self.ui.setupUi(self)
		
		self.ui.objectTree.expandAll()
		self.ui.tilesetTree.expandAll()
		
		self.ui.actionOpen.triggered.connect(self.openFile)
		self.ui.actionSaveAs.triggered.connect(self.saveAs)

		# s
		self.editStates = [EditState(self)] # list of edit states
		# an edit state contains options that can be undone (Ctrl-Z)

		self.currentState = self.editStates[0]
		self.lastSavedState = self.editStates[0]
	def openFile(self):
		path = QFileDialog.getOpenFileName(caption = "Open map", filter = "game1 maps (*.map)")
		if path:
			pass
	def saveAs(self):
		file = QFileDialog.getSaveFileName(caption = "Save map", filter = "game1 maps (*.map)")
		print(file)
	def isModified(self):
		return not self.currentState.equals(self.lastSavedState)
	#def canRedo(self):
	#	return self.editStates[-1] != self.currentState
	def stateBeforeChange(self, editState, name, val):
		print("recorded change (EditState):", name, '=', val)
		if editState != self.currentState:
			raise EditorException("trying to edit a non-current state")
		# keep a copy of the current state
		copy.deepcopy(editState)

# create Qt application
if __name__ == '__main__':
	app = QApplication(sys.argv)
	editor = Editor()

	state = EditState(editor, objects = [{'type':'player', 'x':10, 'y':10}])
	state2 = copy.deepcopy(state)
	print('state == state2?', state.equals(state2))
	state2.objects[0]['x'] = 20 # FIXME: change not detected
	print('state == state2?', state.equals(state2))

	# EditState: could instead have 'onChange(self, fn)'
	# Editor: state = EditState()
	#	state.onChange(self.stateChange)

	editor.show()
	sys.exit(app.exec_())