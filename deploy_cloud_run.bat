@echo off
REM ====================================================
REM  Kaedra - Deploy to Google Cloud Run
REM  Project: WhoBanana (gen-lang-client-0939852539)
REM  Region: us-central1
REM ====================================================

setlocal enabledelayedexpansion

set "PROJECT_ID=gen-lang-client-0939852539"
set "SERVICE_NAME=kaedra-shadow-tactician"
set "REGION=us-central1"
set "IMAGE=gcr.io/%PROJECT_ID%/%SERVICE_NAME%:latest"

echo.
echo ====================================================
echo  Deploying KAEDRA to Cloud Run
echo ====================================================
echo  Project: %PROJECT_ID%
echo  Service: %SERVICE_NAME%
echo  Region:  %REGION%
echo  Image:   %IMAGE%
echo ====================================================
echo.

REM 1. Set active project
echo [1/5] Setting active project...
call gcloud config set project %PROJECT_ID%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to set project
    pause
    exit /b 1
)

REM 2. Enable required APIs
echo [2/5] Enabling required APIs...
call gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com
if %errorlevel% neq 0 (
    echo [ERROR] Failed to enable APIs
    pause
    exit /b 1
)

REM 3. Build container image
echo [3/5] Building container image...
call gcloud builds submit --tag %IMAGE% .
if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

REM 4. Deploy to Cloud Run
echo [4/5] Deploying to Cloud Run...
call gcloud run deploy %SERVICE_NAME% ^
    --image %IMAGE% ^
    --platform managed ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --memory 2Gi ^
    --cpu 2 ^
    --timeout 300 ^
    --set-env-vars "GOOGLE_CLOUD_PROJECT=%PROJECT_ID%,KAEDRA_LOCATION=%REGION%"

if %errorlevel% neq 0 (
    echo [ERROR] Deployment failed
    pause
    exit /b 1
)

REM 5. Get service URL
echo [5/5] Getting service URL...
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format="value(status.url)"') do set SERVICE_URL=%%i

echo.
echo ====================================================
echo  SUCCESS! Kaedra deployed to Cloud Run
echo ====================================================
echo  URL: %SERVICE_URL%
echo  Endpoints:
echo    - Health: %SERVICE_URL%/
echo    - A2A Card: %SERVICE_URL%/a2a
echo    - Chat API: %SERVICE_URL%/v1/chat
echo ====================================================
echo.

echo Test with:
echo   curl %SERVICE_URL%/a2a
echo.

pause
