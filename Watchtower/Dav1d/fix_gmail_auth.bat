@echo off
echo ================================================================
echo  FIXING GMAIL AUTHENTICATION
echo ================================================================
echo.
echo  1. Setting active account to: whoentertains@gmail.com
call gcloud config set account whoentertains@gmail.com
echo.
echo  2. Requesting correct permissions (Gmail Read + Cloud Platform)
echo     Please sign in as: whoentertains@gmail.com
echo.
call gcloud auth application-default login --scopes=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/cloud-platform
echo.
echo ================================================================
echo  Setup complete! You can now run dav1d.bat
pause
