param (
    [Parameter(Mandatory=$true)]
    [Alias('f')]
    [string]$FilePath
)

# Extrai o diretório do caminho do arquivo
$Directory = Split-Path -Parent $FilePath

# Verifica se o diretório existe e, se não, cria-o
if (-not (Test-Path -Path $Directory)) {
    Write-Host "O diretório '$Directory' não existe. Criando..."
    try {
        New-Item -ItemType Directory -Force -Path $Directory -ErrorAction Stop | Out-Null
        Write-Host "Diretório '$Directory' criado com sucesso."
    } catch {
        Write-Error "Falha ao criar o diretório '$Directory'. Erro: $_"
        exit 1
    }
}

# Verifica se o arquivo já existe
if (Test-Path -Path $FilePath) {
    Write-Host "O arquivo '$FilePath' já existe. Nenhuma ação será tomada."
} else {
    # Cria o novo arquivo
    try {
        New-Item -ItemType File -Path $FilePath -ErrorAction Stop | Out-Null
        Write-Host "Arquivo '$FilePath' criado com sucesso."
    } catch {
        Write-Error "Falha ao criar o arquivo '$FilePath'. Erro: $_"
        exit 1
    }
}
