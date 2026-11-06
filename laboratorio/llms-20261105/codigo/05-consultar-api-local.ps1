param(
    [Parameter(Mandatory=$true)][string]$Text,
    [int]$Port = 8088
)
$ErrorActionPreference = 'Stop'
if ($Port -lt 1 -or $Port -gt 65535) { throw 'Porta inválida.' }
$bodyTcc = @{
    messages = @(@{role='user';content=$Text})
    max_tokens = 512
    temperature = 0.6
    top_p = 0.95
    stream = $false
} | ConvertTo-Json -Depth 5
# Endereço fixo no próprio computador; não acessa API paga nem aceita URL externa.
$replyTcc = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/v1/chat/completions" -Method Post -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($bodyTcc)) -TimeoutSec 180
$replyTcc | ConvertTo-Json -Depth 12
