@echo off
chcp 65001 >nul
title QClaw ADB APK 项目工具

echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║     QClaw ADB工具箱 - Android版 v1.0         ║
echo  ╚═══════════════════════════════════════════════╝
echo.

:menu
echo  请选择操作:
echo.
echo  [1] 在Windows上预览应用 (需要安装Python和Flet)
echo  [2] 查看项目文件
echo  [3] 查看构建指南
echo  [4] 安装Flet依赖
echo  [5] 退出
echo.
set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" goto preview
if "%choice%"=="2" goto files
if "%choice%"=="3" goto guide
if "%choice%"=="4" goto install
if "%choice%"=="5" goto end

:preview
echo.
echo  正在启动应用预览...
echo  (这会在Windows上模拟运行,实际APK在Android上运行)
echo.
python main.py
pause
goto menu

:files
echo.
echo  项目文件列表:
echo.
dir /B
echo.
pause
goto menu

:guide
echo.
type 构建指南.md
echo.
pause
goto menu

:install
echo.
echo  正在安装Flet...
echo.
pip install flet
if %errorlevel% equ 0 (
    echo.
    echo  ✓ 安装成功!
) else (
    echo.
    echo  ✗ 安装失败,请检查Python和pip是否正确安装
)
echo.
pause
goto menu

:end
echo.
echo  感谢使用!
echo.
timeout /t 2 >nul
exit
