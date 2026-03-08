@echo off
echo ============================================================
echo Email MCP - Manual Test Workflow
echo ============================================================
echo.

:: Step 1: Create approval request
echo [Step 1] Creating email approval request...
python -c "from scripts.mcp.email_mcp import EmailMCPServer; s = EmailMCPServer(); s.authenticate(); result = s.send_email(to='hk202504@gmail.com', subject='Manual Test', body='Testing HITL workflow manually', skip_approval=False); print('Approval file:', result.get('approval_file', 'ERROR'))"
echo.

:: Step 2: Wait for user
echo [Step 2] Check Pending_Approval folder
dir Pending_Approval\EMAIL_SEND_*.md /b
echo.
set /p "confirm=Press ENTER to approve (move to Approved)..."

:: Step 3: Approve
echo [Step 3] Approving email...
for /f "tokens=*" %%f in ('dir Pending_Approval\EMAIL_SEND_*.md /b') do (
    move Pending_Approval\%%f Approved\%%f
    echo Approved: %%f
)
echo.

:: Step 4: Wait for orchestrator
echo [Step 4] Waiting 15 seconds for Orchestrator to process...
timeout /t 15 /nobreak
echo.

:: Step 5: Check result
echo [Step 5] Checking result...
dir Done\EMAIL_SEND_*.md /b
echo.

:: Step 6: Show logs
echo [Step 6] Recent logs:
type Logs\2026-03-08.md | findstr /C:"email_sent"
echo.

echo ============================================================
echo Test Complete! Check your Gmail: hk202504@gmail.com
echo ============================================================
pause
