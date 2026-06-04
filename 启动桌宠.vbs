Set WshShell = CreateObject("WScript.Shell")
scriptDir = WshShell.CurrentDirectory
WshShell.Run "pythonw """ & scriptDir & "\desktop-pet.py""", 0, False
