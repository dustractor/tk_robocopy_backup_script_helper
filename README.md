# tk_robocopy_backup_script_helper
A small tkinter utility to assist with creating a robocopy script for automating backups

ROBOCOPY is the Microsoft's **RO**bust **CO**py utility that can be used to automate backups.  This python script assists with writing the script to run ROBOCOPY.  It generates a batch file which you right-click and choose "Run as Administrator" to perform the backup.

It keeps it's settings in a sqlite3 database and provides an interface that allows you to:

* add and remove sources and targets (Sources can have multiple targets.)
* choose the name and location of the batch file and the logfile
