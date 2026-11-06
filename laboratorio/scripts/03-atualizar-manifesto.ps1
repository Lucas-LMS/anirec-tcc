# Inventario de arquivos locais. Nao instala nem executa modelos.
param([string]$LabRoot = 'C:/tcc-lab')
$ErrorActionPreference = 'Stop'
$OutputRoot = Split-Path $PSScriptRoot -Parent
$sources = @(
    @{ Name='text8.zip'; Path="$LabRoot/GloVe/data/text8.zip"; Url='https://mattmahoney.net/dc/text8.zip'; Role='Corpus do demo GloVe' },
    @{ Name='text8'; Path="$LabRoot/GloVe/text8"; Url='https://mattmahoney.net/dc/text8.zip'; Role='Corpus extraido' },
    @{ Name='enwik9.zip'; Path="$LabRoot/fastText/data/enwik9.zip"; Url='https://mattmahoney.net/dc/enwik9.zip'; Role='Corpus do exemplo fastText' },
    @{ Name='enwik9'; Path="$LabRoot/fastText/data/enwik9"; Url='https://mattmahoney.net/dc/enwik9.zip'; Role='Corpus extraido; requer wikifil.pl antes do treino' },
    @{ Name='fil9'; Path="$LabRoot/fastText/data/fil9"; Url='https://mattmahoney.net/dc/textdata.html'; Role='Derivado por perl wikifil.pl data/enwik9, script oficial fastText v0.9.2' },
    @{ Name='rw.zip'; Path="$LabRoot/fastText/data/rw.zip"; Url='https://nlp.stanford.edu/~lmthang/morphoNLM/rw.zip'; Role='Avaliacao Rare Words; download falhou na sessao inicial' },
    @{ Name='setup-x86_64.exe'; Path='C:/tcc-tools/downloads/setup-x86_64.exe'; Url='https://cygwin.com/setup-x86_64.exe'; Role='Instalador Cygwin baixado; apenas --help executado; instalacao bloqueada' }
)
$publishedMd5 = @{ text8='3bea1919949baf155f99411df5fada7e'; enwik9='e206c3450ac99950df65bf70ef61a12d'; fil9='2754e1cfcc34288745cd23272d976384' }
$items = foreach ($source in $sources) {
    $exists = Test-Path -LiteralPath $source.Path -PathType Leaf
    $size = $null
    $hash = $null
    $md5 = $null
    $expected = $publishedMd5[$source.Name]
    if ($exists) {
        $size = (Get-Item -LiteralPath $source.Path).Length
        $hash = (Get-FileHash -LiteralPath $source.Path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($expected) {
            $md5 = (Get-FileHash -LiteralPath $source.Path -Algorithm MD5).Hash.ToLowerInvariant()
            if ($md5 -ne $expected) { throw "Checksum publicado diverge: $($source.Name)" }
        }
    }
    [ordered]@{name=$source.Name; path=$source.Path; source=$source.Url; role=$source.Role; exists=$exists; bytes=$size; sha256=$hash; published_md5=$expected; observed_md5=$md5; checksum_source= $(if ($expected) { 'https://mattmahoney.net/dc/textdata.html' } else { $null }); checksum_verified_against_publisher= [bool]($exists -and $expected -and ($md5 -eq $expected))}
}
$repositories = foreach ($name in @('GloVe','fastText')) {
    $repoPath = Join-Path $LabRoot $name
    $revision = & git -C $repoPath rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw "Falha ao consultar $repoPath" }
    $remote = & git -C $repoPath remote get-url origin
    if ($LASTEXITCODE -ne 0) { throw "Falha ao consultar origem $repoPath" }
    $tracked = @(& git -C $repoPath status --porcelain --untracked-files=no)
    if ($LASTEXITCODE -ne 0) { throw "Falha ao consultar estado $repoPath" }
    [ordered]@{name=$name; path=$repoPath; remote=$remote; revision=$revision; tracked_changes=$tracked; compiled=$false; trained=$false; evaluated=$false}
}
[ordered]@{
    recorded_at=[DateTimeOffset]::Now.ToString('o')
    note='Estado desta sessao: preparacao; compilacao, treinamento e avaliacao nao executados. Atualizar os estados manualmente com evidencias apos execucoes futuras.'
    artifacts=@($items)
    repositories=@($repositories)
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$OutputRoot/manifests/artefatos.json" -Encoding utf8
Write-Output 'Manifesto atualizado; MD5 publicados comparados quando disponiveis. SHA-256 locais nao equivalem a assinaturas do publicador.'
