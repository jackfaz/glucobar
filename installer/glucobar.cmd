@echo off
rem Comando "glucobar" da terminale: richiama glucobar-cli.exe nella cartella sopra
"%~dp0..\glucobar-cli.exe" %*
exit /b %errorlevel%
