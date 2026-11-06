param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('llama','deepseek','qwen')][string]$Model,
    [int]$Port = 8088
)
$ErrorActionPreference = 'Stop'
$labTcc = 'C:/tcc-lab/LLMs'
$filesTcc = @{
    llama = 'Llama-3.2-1B-Instruct-Q4_K_M.gguf'
    deepseek = 'DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf'
    qwen = 'Qwen3-0.6B-Q8_0.gguf'
}
$weightTcc = Join-Path "$labTcc/models" $filesTcc[$Model]
if (!(Test-Path -LiteralPath $weightTcc)) { throw "Modelo ausente: $weightTcc" }
$thinkingTcc = if ($Model -eq 'llama') { 'off' } else { 'on' }
$samplingTcc = if ($Model -eq 'qwen') { @('--temp','0.6','--top-p','0.95','--top-k','20','--min-p','0','--presence-penalty','1.5') } else { @() }
# API exclusivamente local. Este comando ocupa o terminal até Ctrl+C.
& "$labTcc/runtime-b12110/llama-server.exe" -m $weightTcc -c 2048 -t 4 -tb 4 -ngl 0 -np 1 -n 512 --host 127.0.0.1 --port $Port --reasoning $thinkingTcc @samplingTcc
