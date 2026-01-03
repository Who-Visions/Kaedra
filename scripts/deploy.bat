@echo off
setlocal enabledelayedexpansion

REM ====================================================
REM  KAEDRA v0.0.6 - Cloud Run Deploy Script
REM ====================================================

REM --- CONFIGURATION ---
set "PROJECT_ID=gen-lang-client-0939852539"
set "SERVICE_NAME=kaedra-shadow-tactician"
set "REGION=us-central1"
set "IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%"

echo.
echo ====================================================
echo  Deploying KAEDRA to Cloud Run
echo ====================================================
echo  Project: %PROJECT_ID%
echo  Service: %SERVICE_NAME%
echo  Region:  %REGION%
echo ====================================================
echo.

REM 1. Set Project
echo [*] Setting active project...
call gcloud config set project %PROJECT_ID%
if %errorlevel% neq 0 (
    echo [!] Failed to set project.
    exit /b %errorlevel%
)

REM 2. Enable APIs (Run once, skipping if already valid usually fine but good to be safe)
echo [*] Ensuring services are enabled...
call gcloud services enable cloudbuild.googleapis.com run.googleapis.com
if %errorlevel% neq 0 (
    echo [!] Failed to enable services.
    exit /b %errorlevel%
)

REM 3. Submit Build
echo [*] Building and submitting container image...
call gcloud builds submit --tag %IMAGE_NAME% .
if %errorlevel% neq 0 (
    echo [!] Build failed.
    exit /b %errorlevel%
)

REM 4. Deploy
echo [*] Deploying to Cloud Run...
call gcloud run deploy %SERVICE_NAME% ^
    --image %IMAGE_NAME% ^
    --platform managed ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --memory 2Gi ^
    --cpu 2 ^
    --set-env-vars "GOOGLE_CLOUD_PROJECT=%PROJECT_ID%,KAEDRA_LOCATION=%REGION%,KAEDRA_AGENT_RESOURCE=projects/69017097813/locations/us-central1/reasoningEngines/kaedra-shadow-tactician"

if %errorlevel% neq 0 (
    echo [!] Deployment failed.
    exit /b %errorlevel%
)

echo.
echo ====================================================
echo  [SUCCESS] Kaedra Deployed Successfully!
echo ====================================================
echo.
pause
