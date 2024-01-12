SETLOCAL 
CALL conda config --set report_errors false
CALL conda activate dev_pandss
CALL conda build . --output-folder .\dist > .\dist\record_conda.txt 2>&1
ENDLOCAL
PAUSE