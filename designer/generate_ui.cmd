pyrcc5 -o ../icons_rc.py icons.qrc
pyrcc5 -o ../editor_rc.py editor.qrc
call pyuic5 -o ../uiEditor.py editor.ui
call pyuic5 -o ../uiCodeEditor.py codeEditor.ui
call pyuic5 -o ../uiSolidDirections.py solidDirections.ui