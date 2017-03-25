pyrcc5 -o ../icons_rc.py icons.qrc
pyrcc5 -o ../editor_rc.py editor.qrc
pyuic5 -o ../uiEditor.py editor.ui

pyuic5 -o ../uiCodeEditor.py codeEditor.ui