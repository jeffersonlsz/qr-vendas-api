param(
    [string]$ListaArquivos = "arquivos.txt",
    [string]$Saida = "conteudo_arquivos.txt"
)

if (!(Test-Path $ListaArquivos)) {
    Write-Host "Arquivo de lista não encontrado: $ListaArquivos"
    exit 1
}

# limpa ou cria arquivo de saída
"" | Set-Content $Saida -Encoding UTF8

Get-Content $ListaArquivos | ForEach-Object {
    $caminho = $_.Trim()

    if ($caminho -eq "") {
        return
    }

    Add-Content $Saida "=================================================="
    Add-Content $Saida "ARQUIVO: $caminho"
    Add-Content $Saida "=================================================="

    if (Test-Path $caminho) {
        Get-Content $caminho | Add-Content $Saida
    }
    else {
        Add-Content $Saida "[ERRO] Arquivo não encontrado: $caminho"
    }

    Add-Content $Saida ""
    Add-Content $Saida ""
}

Write-Host "Arquivo gerado: $Saida"