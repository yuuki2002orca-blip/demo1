@echo off
chcp 65001 > nul
echo ========================================
echo  AI記事生成ツール
echo ========================================
echo.
set /p topic="トピックを入力してください（例: AI最新動向）: "
echo.
echo 記事を生成してXとnoteに投稿します...
echo.
python main.py generate "%topic%" --post
pause
