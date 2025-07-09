@echo off
title Verificador de IP do computador
echo Verificando o seu endereco IPV4...
echo.

REM --- Bloco para capturar o IP em uma variavel ---
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "IP_ADDRESS=%%a"
    goto :found
)

:found
REM Remove os espacos em branco do inicio da variavel
set "IP_ADDRESS=%IP_ADDRESS: =%"

echo Endereco IP encontrado: %IP_ADDRESS%
echo.
echo Copie e use: %IP_ADDRESS%:5000
echo.
echo Pressione qualquer tecla para sair.
pause > nul