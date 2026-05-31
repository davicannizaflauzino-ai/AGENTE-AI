@echo off
echo Teste funcionou! > "%TEMP%\jarvis_test.txt"
echo Caminho: %~dp0 >> "%TEMP%\jarvis_test.txt"
echo PATH: %PATH% >> "%TEMP%\jarvis_test.txt"
echo LOCALAPPDATA: %LOCALAPPDATA% >> "%TEMP%\jarvis_test.txt"
echo Python check: >> "%TEMP%\jarvis_test.txt"
where python >> "%TEMP%\jarvis_test.txt" 2>&1
echo Fim do teste >> "%TEMP%\jarvis_test.txt"
echo Teste concluido. Pressione qualquer tecla.
pause