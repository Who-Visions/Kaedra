@echo off
echo ================================================================
echo  DAV1D GMAIL AUTHENTICATION SETUP
echo ================================================================
echo.
echo  To allow Dav1d to read your Gmail, we need to update your
echo  Application Default Credentials (ADC) with the correct permissions.
echo.
echo  Please run the following command in your terminal:
echo.
echo  gcloud auth application-default login --scopes=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/cloud-platform
echo.
echo  1. A browser window will open.
echo  2. Sign in with your Google account.
echo  3. Allow the requested permissions.
echo.
echo  After that, Dav1d will be able to check your email!
echo.
echo ================================================================
pause
