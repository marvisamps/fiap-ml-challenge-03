# ========================================
# CHECKLIST PRÉ-APRESENTAÇÃO - FASE 3
# Execute este script antes de gravar o vídeo
# ========================================

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  CHECKLIST PRÉ-APRESENTAÇÃO - PRATO DO DIA (FASE 3)          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$ErrorCount = 0

# ========================================
# 1. VERIFICAR AMBIENTE
# ========================================
Write-Host "1️⃣  VERIFICANDO AMBIENTE..." -ForegroundColor Yellow

# Python
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "3\.1[1-9]") {
        Write-Host "   ✅ Python: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Python: $pythonVersion (recomendado 3.11+)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Python não encontrado!" -ForegroundColor Red
    $ErrorCount++
}

# Virtual Environment
if (Test-Path ".venv") {
    Write-Host "   ✅ Virtual environment (.venv) existe" -ForegroundColor Green
} else {
    Write-Host "   ❌ Virtual environment não encontrado! Execute: python -m venv .venv" -ForegroundColor Red
    $ErrorCount++
}

# .env
if (Test-Path ".env") {
    Write-Host "   ✅ Arquivo .env existe" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Arquivo .env não encontrado (copie de env.example)" -ForegroundColor Yellow
}

# ========================================
# 2. VERIFICAR DADOS
# ========================================
Write-Host "`n2️⃣  VERIFICANDO DADOS..." -ForegroundColor Yellow

# events.jsonl
if (Test-Path "data/events.jsonl") {
    $eventCount = (Get-Content "data/events.jsonl" | Measure-Object -Line).Lines
    Write-Host "   ✅ data/events.jsonl: $eventCount eventos" -ForegroundColor Green
    if ($eventCount -lt 100) {
        Write-Host "      ⚠️  Poucos eventos! Execute: python data/firestore_direct.py" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ data/events.jsonl não encontrado!" -ForegroundColor Red
    $ErrorCount++
}

# Features
if ((Test-Path "data/feat_train.parquet") -and (Test-Path "data/feat_val.parquet")) {
    Write-Host "   ✅ Features geradas (train + val)" -ForegroundColor Green
} else {
    Write-Host "   ❌ Features não encontradas! Execute: python pipelines/features.py" -ForegroundColor Red
    $ErrorCount++
}

# Modelo
if (Test-Path "artifacts/model.txt") {
    $modelDate = (Get-Item "artifacts/model.txt").LastWriteTime
    Write-Host "   ✅ Modelo treinado: $($modelDate.ToString('dd/MM/yyyy HH:mm'))" -ForegroundColor Green
} else {
    Write-Host "   ❌ Modelo não encontrado! Execute: python models/train.py" -ForegroundColor Red
    $ErrorCount++
}

# ========================================
# 3. VERIFICAR DEPENDÊNCIAS
# ========================================
Write-Host "`n3️⃣  VERIFICANDO DEPENDÊNCIAS..." -ForegroundColor Yellow

$requiredPackages = @("fastapi", "uvicorn", "lightgbm", "streamlit", "firebase-admin", "plotly", "pandas")
$missingPackages = @()

foreach ($pkg in $requiredPackages) {
    $installed = pip list 2>&1 | Select-String -Pattern $pkg -Quiet
    if ($installed) {
        Write-Host "   ✅ $pkg instalado" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $pkg NÃO instalado" -ForegroundColor Red
        $missingPackages += $pkg
        $ErrorCount++
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "`n   💡 Execute: pip install -r requirements.txt" -ForegroundColor Yellow
}

# ========================================
# 4. VERIFICAR DOCUMENTAÇÃO
# ========================================
Write-Host "`n4️⃣  VERIFICANDO DOCUMENTAÇÃO..." -ForegroundColor Yellow

$docs = @(
    "README.md",
    "docs/MODEL_EVALUATION.md",
    "docs/PRESENTATION_GUIDE.md",
    "entrega.txt"
)

foreach ($doc in $docs) {
    if (Test-Path $doc) {
        Write-Host "   ✅ $doc" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $doc não encontrado!" -ForegroundColor Red
        $ErrorCount++
    }
}

# ========================================
# 5. TESTAR API
# ========================================
Write-Host "`n5️⃣  TESTANDO API..." -ForegroundColor Yellow

# Verificar se porta 8000 está em uso
$apiRunning = netstat -ano | Select-String ":8000" | Measure-Object | Select-Object -ExpandProperty Count

if ($apiRunning -gt 0) {
    Write-Host "   ✅ API rodando na porta 8000" -ForegroundColor Green
    
    # Testar endpoint /health
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -ErrorAction Stop
        if ($response.status -eq "healthy") {
            Write-Host "   ✅ GET /health → status: healthy" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  GET /health → status: $($response.status)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️  Não foi possível testar /health" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  API não está rodando" -ForegroundColor Yellow
    Write-Host "      💡 Execute em outro terminal: uvicorn api.main:app --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
}

# ========================================
# 6. TESTAR DASHBOARD
# ========================================
Write-Host "`n6️⃣  TESTANDO DASHBOARD..." -ForegroundColor Yellow

$dashRunning = netstat -ano | Select-String ":8501" | Measure-Object | Select-Object -ExpandProperty Count

if ($dashRunning -gt 0) {
    Write-Host "   ✅ Dashboard rodando na porta 8501" -ForegroundColor Green
    Write-Host "      💡 Acesse: http://localhost:8501" -ForegroundColor Cyan
} else {
    Write-Host "   ⚠️  Dashboard não está rodando" -ForegroundColor Yellow
    Write-Host "      💡 Execute em outro terminal: streamlit run dash/app.py" -ForegroundColor Cyan
}

# ========================================
# 7. MÉTRICAS PRINCIPAIS
# ========================================
Write-Host "`n7️⃣  MÉTRICAS PRINCIPAIS..." -ForegroundColor Yellow

if (Test-Path "data/events.jsonl") {
    try {
        $events = Get-Content "data/events.jsonl" | ConvertFrom-Json
        $totalEvents = $events.Count
        $uniqueUsers = ($events | Select-Object -ExpandProperty user_id -Unique).Count
        $generated = ($events | Where-Object { $_.event_name -eq "recipe_generate" }).Count
        $favorited = ($events | Where-Object { $_.event_name -eq "save_recipe" }).Count
        
        Write-Host "   📊 Total de eventos: $totalEvents" -ForegroundColor Cyan
        Write-Host "   👥 Usuários únicos: $uniqueUsers" -ForegroundColor Cyan
        Write-Host "   ✨ Receitas geradas: $generated" -ForegroundColor Cyan
        Write-Host "   ⭐ Receitas favoritadas: $favorited" -ForegroundColor Cyan
    } catch {
        Write-Host "   ⚠️  Não foi possível calcular métricas" -ForegroundColor Yellow
    }
}

# ========================================
# RESUMO FINAL
# ========================================
Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESUMO FINAL                                                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($ErrorCount -eq 0) {
    Write-Host "🎉 TUDO PRONTO PARA GRAVAR! 🎬" -ForegroundColor Green
    Write-Host "`nPróximos passos:" -ForegroundColor Yellow
    Write-Host "1. Abrir Firebase Console (https://console.firebase.google.com)" -ForegroundColor White
    Write-Host "2. Abrir API Docs (http://localhost:8000/docs)" -ForegroundColor White
    Write-Host "3. Abrir Dashboard (http://localhost:8501)" -ForegroundColor White
    Write-Host "4. Abrir VS Code com estrutura de pastas visível" -ForegroundColor White
    Write-Host "5. Revisar docs/PRESENTATION_GUIDE.md" -ForegroundColor White
    Write-Host "6. Gravar vídeo de 5 minutos! 🎥`n" -ForegroundColor White
} else {
    Write-Host "❌ ENCONTRADOS $ErrorCount PROBLEMAS!" -ForegroundColor Red
    Write-Host "`nResolva os problemas acima antes de gravar.`n" -ForegroundColor Yellow
}

# ========================================
# COMANDOS ÚTEIS
# ========================================
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  COMANDOS ÚTEIS                                               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "Ativar ambiente:" -ForegroundColor Yellow
Write-Host "  .venv\Scripts\Activate.ps1`n" -ForegroundColor White

Write-Host "Sincronizar Firebase:" -ForegroundColor Yellow
Write-Host "  python data/firestore_direct.py`n" -ForegroundColor White

Write-Host "Gerar features:" -ForegroundColor Yellow
Write-Host "  python pipelines/features.py`n" -ForegroundColor White

Write-Host "Treinar modelo:" -ForegroundColor Yellow
Write-Host "  python models/train.py`n" -ForegroundColor White

Write-Host "Executar API:" -ForegroundColor Yellow
Write-Host "  uvicorn api.main:app --host 0.0.0.0 --port 8000`n" -ForegroundColor White

Write-Host "Executar Dashboard:" -ForegroundColor Yellow
Write-Host "  streamlit run dash/app.py`n" -ForegroundColor White

Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

