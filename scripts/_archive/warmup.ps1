<#
.SYNOPSIS
    Executa consultas repetidas ao endpoint /ask para aquecer o cache do Araquem (M4).
.DESCRIPTION
    Mede o tempo total, cache hits/misses e gera estatísticas rápidas no console.
    Usa perguntas reais da entidade fiis_cadastro (ex.: CNPJ de VINO11, KNRI11, HGLG11, etc.)
#>

# --- Configurações ---
$ApiUrl = "http://localhost:8000/ask"
$Nickname = "@leleo"
$ClientId = "66140994691"
$ConversationPrefix = "warmup"
$Questions = @(
    "Qual o CNPJ do VINO11?",
    "Qual o CNPJ do HGLG11?",
    "Qual o CNPJ do KNRI11?",
    "Quem é o administrador do VINO11?",
    "Quem é o administrador do HGLG11?"
)

Write-Host "🔹 Iniciando warmup para $($Questions.Count) perguntas..." -ForegroundColor Cyan
$results = @()
$swTotal = [System.Diagnostics.Stopwatch]::StartNew()

foreach ($q in $Questions) {
    $body = @{
        question = $q
        conversation_id = "$ConversationPrefix-$([guid]::NewGuid())"
        nickname = $Nickname
        client_id = $ClientId
    } | ConvertTo-Json -Depth 4

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-RestMethod -Uri $ApiUrl -Method POST -ContentType "application/json" -Body $body
        $elapsed = $sw.ElapsedMilliseconds

        $entity = $resp.meta.planner_entity
        $hit = $resp.meta.cache.hit
        $rows = $resp.meta.rows_total
        $score = $resp.meta.planner_score

        $results += [pscustomobject]@{
            Pergunta = $q
            Entidade = $entity
            Score    = $score
            Rows     = $rows
            CacheHit = if ($hit) { "✅ HIT" } else { "❌ MISS" }
            TempoMs  = $elapsed
        }

        Write-Host ("{0,-50} {1,6} {2,8}ms" -f $q, $results[-1].CacheHit, $elapsed)
    }
    catch {
        Write-Host "⚠️ Erro ao consultar '$q' → $($_.Exception.Message)" -ForegroundColor Red
    }
}

$swTotal.Stop()
Write-Host "`n⏱️ Total: $($swTotal.ElapsedMilliseconds) ms" -ForegroundColor Cyan

# --- Estatísticas ---
$hits = ($results | Where-Object { $_.CacheHit -eq "✅ HIT" }).Count
$misses = ($results | Where-Object { $_.CacheHit -eq "❌ MISS" }).Count
$total = $results.Count
$hitRatio = if ($total -gt 0) { [math]::Round(($hits / $total) * 100, 1) } else { 0 }

Write-Host "`n📊 Estatísticas"
Write-Host "   Total perguntas : $total"
Write-Host "   Hits            : $hits"
Write-Host "   Misses          : $misses"
Write-Host "   Hit Ratio       : $hitRatio%"

# --- Export opcional ---
$outFile = "warmup_results_$(Get-Date -Format yyyyMMdd_HHmmss).csv"
$results | Export-Csv -Path $outFile -NoTypeInformation -Encoding UTF8
Write-Host "`n📁 Resultados exportados em: $outFile" -ForegroundColor Green
