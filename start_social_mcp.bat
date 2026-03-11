@echo off
cd /d "%~dp0"
echo Starting Social Media MCP Server...
echo ==================================================
echo This server allows you to post to Facebook & Instagram
echo ==================================================
echo.
python scripts/mcp/social_mcp.py
pause
