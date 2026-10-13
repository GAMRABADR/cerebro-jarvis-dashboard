@echo off
title JARVIS CLOUDFLARE PERMANENT TUNNEL (jarvis.badrexpress.com)
rem Il token non sta piu' in questo file: era letterale e committato nel repo
rem GitHub pubblico. Lo prende da .env (slot CF_TUNNEL_TOKEN). Fail-closed:
rem senza slot il tunnel non parte e viene detto perche', invece di schiattare
rem al primo handshake con l'output chiuso.
setlocal
set "CF_TOKEN="
for /f "usebackq tokens=1,* delims==" %%A in ("%~dp0.env") do if /i "%%A"=="CF_TUNNEL_TOKEN" set "CF_TOKEN=%%B"
if not defined CF_TOKEN (
  echo [JARVIS] ERRORE: slot CF_TUNNEL_TOKEN vuoto o assente in %~dp0.env - nessun avvio.
  exit /b 1
)
rem TUNNEL_TOKEN nell'ambiente, non in argv: da argv e' leggibile da tasklist.
set "TUNNEL_TOKEN=%CF_TOKEN%"
echo [JARVIS] Avvio Cloudflare Named Tunnel su jarvis.badrexpress.com...
cloudflared.exe tunnel run
pause
