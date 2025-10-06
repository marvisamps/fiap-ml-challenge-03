# ========================================
# SCRIPT DE COMMIT E PUSH - FASE 3
# Execute para enviar tudo ao GitHub
# ========================================

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PREPARANDO COMMIT E PUSH PARA GITHUB                         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Verificar se estamos no diretório correto
if (-not (Test-Path "README.md")) {
    Write-Host "❌ Execute este script da raiz do projeto!" -ForegroundColor Red
    exit 1
}

# Verificar se git está inicializado
if (-not (Test-Path ".git")) {
    Write-Host "⚠️  Git não inicializado. Inicializando..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git inicializado" -ForegroundColor Green
}

# Verificar remote
$remote = git remote get-url origin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Remote 'origin' não configurado. Adicionando..." -ForegroundColor Yellow
    git remote add origin git@github.com:marvisamps/fiap-ml-challenge-03.git
    Write-Host "✅ Remote adicionado: git@github.com:marvisamps/fiap-ml-challenge-03.git" -ForegroundColor Green
} else {
    Write-Host "✅ Remote configurado: $remote" -ForegroundColor Green
}

# Status atual
Write-Host "`n📊 Status atual do repositório:" -ForegroundColor Yellow
git status --short

# Listar arquivos principais
Write-Host "`n📁 Arquivos principais a serem commitados:" -ForegroundColor Yellow
$mainFiles = @(
    "README.md",
    "entrega.txt",
    "requirements.txt",
    "Dockerfile",
    ".gitignore",
    "api/main.py",
    "models/train.py",
    "pipelines/features.py",
    "dash/app.py",
    "data/firestore_direct.py",
    "docs/MODEL_EVALUATION.md",
    "docs/PRESENTATION_GUIDE.md",
    "common/config.py",
    "common/schemas.py"
)

foreach ($file in $mainFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $file (não encontrado)" -ForegroundColor Yellow
    }
}

# Confirmar antes de continuar
Write-Host "`n⚠️  ATENÇÃO: Este script irá:" -ForegroundColor Yellow
Write-Host "   1. Adicionar todos os arquivos (git add .)" -ForegroundColor White
Write-Host "   2. Criar commit com mensagem padrão" -ForegroundColor White
Write-Host "   3. Fazer push para origin main" -ForegroundColor White
Write-Host ""
$confirm = Read-Host "Deseja continuar? (S/N)"

if ($confirm -ne "S" -and $confirm -ne "s") {
    Write-Host "`n❌ Operação cancelada pelo usuário." -ForegroundColor Red
    exit 0
}

# Git add
Write-Host "`n📦 Adicionando arquivos..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Arquivos adicionados" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao adicionar arquivos" -ForegroundColor Red
    exit 1
}

# Git commit
Write-Host "`n💾 Criando commit..." -ForegroundColor Yellow
$commitMessage = @"
feat: Fase 3 - Sistema de Recomendação completo

- ✅ API FastAPI com 4 endpoints Firebase
- ✅ Modelo LightGBM LambdaMART (NDCG@10: 0.583)
- ✅ Dashboard Streamlit (3 abas: Executiva, Técnica, Receitas)
- ✅ Integração Firebase (501 eventos, 161 usuários)
- ✅ Documentação completa (8 docs)
- ✅ Pipeline ML (feature engineering + treinamento)
- ✅ Cloud Functions para sincronização tempo real
- ✅ Docker + .env para produção

Aluno: Mário Vieira Sampaio Filho
RM: RM362712
Turma: Pós em Machine Learning Engineering
"@

git commit -m $commitMessage
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Commit criado com sucesso" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao criar commit" -ForegroundColor Red
    Write-Host "   Tente: git commit -m 'feat: Fase 3 completa'" -ForegroundColor Yellow
    exit 1
}

# Git push
Write-Host "`n🚀 Enviando para GitHub..." -ForegroundColor Yellow
Write-Host "   Remote: git@github.com:marvisamps/fiap-ml-challenge-03.git" -ForegroundColor Cyan
Write-Host "   Branch: main" -ForegroundColor Cyan
Write-Host ""

# Verificar se branch main existe
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "⚠️  Branch atual: $currentBranch. Renomeando para main..." -ForegroundColor Yellow
    git branch -M main
}

# Push
git push -u origin main
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 PUSH REALIZADO COM SUCESSO! 🎉" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Repositório atualizado em:" -ForegroundColor Green
    Write-Host "   https://github.com/marvisamps/fiap-ml-challenge-03" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
    Write-Host "   1. Verificar repositório no GitHub (link acima)" -ForegroundColor White
    Write-Host "   2. Gravar vídeo de apresentação (5 min)" -ForegroundColor White
    Write-Host "   3. Upload vídeo no YouTube" -ForegroundColor White
    Write-Host "   4. Adicionar link do vídeo em entrega.txt" -ForegroundColor White
    Write-Host "   5. Fazer commit + push novamente" -ForegroundColor White
    Write-Host "   6. Enviar entrega.txt na plataforma FIAP" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "`n❌ ERRO NO PUSH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possíveis causas:" -ForegroundColor Yellow
    Write-Host "   1. SSH key não configurada" -ForegroundColor White
    Write-Host "   2. Sem permissão no repositório" -ForegroundColor White
    Write-Host "   3. Branch protegida" -ForegroundColor White
    Write-Host ""
    Write-Host "Soluções:" -ForegroundColor Yellow
    Write-Host "   # Verificar SSH" -ForegroundColor Cyan
    Write-Host "   ssh -T git@github.com" -ForegroundColor White
    Write-Host ""
    Write-Host "   # Ou usar HTTPS" -ForegroundColor Cyan
    Write-Host "   git remote set-url origin https://github.com/marvisamps/fiap-ml-challenge-03.git" -ForegroundColor White
    Write-Host "   git push -u origin main" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

