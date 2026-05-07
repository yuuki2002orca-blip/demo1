@echo off
chcp 65001 > nul
echo ========================================
echo  ログインを開始します
echo  ブラウザが3回開きます。
echo  それぞれログイン後にこの画面でEnterを押してください。
echo ========================================
echo.
python main.py login
pause
