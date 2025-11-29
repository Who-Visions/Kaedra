@echo off
echo ================================================================
echo  AUTHENTICATING WITH SPECIFIC CLIENT ID
echo ================================================================
echo.
echo  This uses your project's specific Client ID to bypass the
echo  "App Blocked" error.
echo.
echo  Please sign in as: whoentertains@gmail.com
echo.
call gcloud auth application-default login --client-id-file=client_secret.json --scopes=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/cloud-platform
echo.
echo ================================================================
echo  Setup complete! You can now run dav1d.bat
pause
