@echo off
chcp 65001 > nul
echo ========================================
echo  セットアップを開始します...
echo ========================================
echo.

echo [1/2] ライブラリをインストール中...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo エラーが発生しました。Pythonが正しくインストールされているか確認してください。
    pause
    exit /b 1
)

echo.
echo [2/2] ブラウザをインストール中...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo エラーが発生しました。
    pause
    exit /b 1
)

echo.
echo ========================================
echo  セットアップ完了！
echo  次に login.bat をダブルクリックしてください。
echo ========================================
pause
