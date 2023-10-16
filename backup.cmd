
@echo off
set PATH=%HOMEDRIVE%%HOMEPATH%\ANACON~1;%PATH%
set PYTHONHOME=%HOMEDRIVE%%HOMEPATH%\anaconda3
call conda activate
%PYTHONHOME%\pythonw.exe .\tk_robocopy_backup_script_helper.py
