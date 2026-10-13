' Document Studio Pro — Silent Windowless Launcher
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath

pyExe = "pythonw.exe"
If fso.FileExists(strPath & "\runtime\pythonw.exe") Then
    pyExe = """" & strPath & "\runtime\pythonw.exe"""
ElseIf fso.FileExists(strPath & "\runtime\python.exe") Then
    pyExe = """" & strPath & "\runtime\python.exe"""
ElseIf fso.FileExists(strPath & "\runtime\Scripts\pythonw.exe") Then
    pyExe = """" & strPath & "\runtime\Scripts\pythonw.exe"""
End If

WshShell.Run pyExe & " """ & strPath & "\splitter.py""", 0, False
