# ☁️ Cloud Functions - Sincronização Automática

## 📋 Visão Geral

Este diretório contém as Cloud Functions do Firebase para sincronização automática de dados.

## 🚀 Funções Disponíveis

### 1. `onRecipeGenerated`
**Trigger**: Quando documento é criado em `recipes_generated`  
**Ação**: Envia automaticamente para `/firebase/recipe-generated`

### 2. `onRecipeFavorited`
**Trigger**: Quando documento é criado em `users/{userId}/favoriteLists/{listId}/items/{recipeId}`  
**Ação**: Envia automaticamente para `/firebase/recipe-favorited`  
**⚠️ Estrutura aninhada** - requer collection group queries

### 3. `syncManual`
**Tipo**: HTTP Function  
**Ação**: Sincronização manual em lote  
**URL**: `https://your-region-your-project.cloudfunctions.net/syncManual`

### 4. `syncScheduled`
**Tipo**: Scheduled Function  
**Frequência**: A cada 5 minutos  
**Ação**: Marca documentos como sincronizados

## 📦 Instalação

```bash
cd cloud_functions/functions
npm install
```

## 🔧 Configuração

### 1. Configurar Projeto Firebase

```bash
# Na pasta cloud_functions/
firebase login
firebase use --add
# Selecione seu projeto
```

### 2. Configurar URL da API

```bash
firebase functions:config:set api.url="https://your-api.com"
```

### 3. Visualizar Configuração

```bash
firebase functions:config:get
```

## 🧪 Testar Localmente

```bash
cd cloud_functions/functions
npm run serve
```

Isso inicia o emulador local. Teste criando documentos no Firestore.

## 🚀 Deploy

```bash
cd cloud_functions
firebase deploy --only functions
```

### Deploy de Função Específica

```bash
firebase deploy --only functions:onRecipeGenerated
firebase deploy --only functions:onRecipeFavorited
```

## 📊 Monitoramento

### Ver Logs

```bash
firebase functions:log
```

### Ver Logs de Função Específica

```bash
firebase functions:log --only onRecipeGenerated
```

### Ver Logs em Tempo Real

```bash
firebase functions:log --follow
```

## 🔐 Permissões Necessárias

- Cloud Functions Admin
- Firestore Read/Write
- Cloud Scheduler Admin (para funções agendadas)

## 📝 Estrutura de Dados Esperada

⚠️ **IMPORTANTE:** Favoritos usam estrutura aninhada!

### Collection: `recipes_generated` (flat)

**Path:** `recipes_generated/{recipeId}`

```javascript
{
  recipeName: string,
  query: string,
  fullRecipe: string,
  userId: string,
  createdAt: Timestamp,
  calories: number | null,
  imageUrl: string | null,
  synced: boolean,  // adicionado automaticamente
  syncedAt: Timestamp | null
}
```

### Nested Structure: Favoritos

**Path:** `users/{userId}/favoriteLists/{listId}/items/{recipeId}`

**Exemplo:** `users/user_xyz/favoriteLists/hash_abc/items/recipe_123`

```javascript
{
  name: string,
  response: string,
  addedAt: Timestamp,
  query: string,
  imageUrl: string | null,
  synced: boolean,  // adicionado automaticamente
  syncedAt: Timestamp | null,
  listId: string    // adicionado automaticamente
}
```

**⚠️ Observações:**
- O `userId` é extraído do path, não está no documento
- Mesma receita pode estar em múltiplas listas do mesmo usuário
- Requer **collection group queries** para buscar todos os favoritos

📖 **Ver detalhes completos em:** [FIRESTORE_STRUCTURE.md](../FIRESTORE_STRUCTURE.md)

## 🔄 Fluxo de Sincronização

```
┌─────────────────┐
│ App cria doc    │
│ no Firestore    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cloud Function  │
│ é disparada     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Envia para API  │
│ POST /firebase/ │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Marca como      │
│ synced=true     │
└─────────────────┘
```

## 📋 Índices Necessários

⚠️ **CRÍTICO:** Collection group queries requerem índices!

### Criar Índices

**Opção 1: Automático (recomendado)**
1. Fazer deploy das functions
2. Esperar erro na primeira execução
3. Clicar no link do erro
4. Confirmar criação do índice

**Opção 2: Manual**

No Firebase Console → Firestore Database → Indexes:

1. **items** (collection group) - synced
   - Collection ID: `items`
   - Fields: `synced` (Ascending), `__name__` (Ascending)
   - Query scope: **Collection group**

2. **items** (collection group) - addedAt
   - Collection ID: `items`
   - Fields: `addedAt` (Descending), `__name__` (Ascending)
   - Query scope: **Collection group**

3. **recipes_generated** - synced
   - Collection ID: `recipes_generated`
   - Fields: `synced` (Ascending), `createdAt` (Descending)
   - Query scope: Collection

📖 **Detalhes:** [FIRESTORE_STRUCTURE.md](../FIRESTORE_STRUCTURE.md) - seção "Índices Necessários"

## 💰 Custos

Cloud Functions possui tier gratuito:
- 2 milhões de invocações/mês
- 400.000 GB-segundos
- 200.000 CPU-segundos

**Estimativa para 1000 receitas/dia**: ~$0/mês (dentro do free tier)

## 🐛 Troubleshooting

### Função não dispara

1. Verificar índices criados:
   ```bash
   firebase firestore:indexes
   ```

2. Verificar logs:
   ```bash
   firebase functions:log --only onRecipeGenerated
   ```

3. Se erro "The query requires an index":
   - Clicar no link fornecido no log
   - Confirmar criação automática
   - Aguardar build (1-5 min)

### Erro 403 Forbidden

Verificar permissões do Service Account:
```bash
gcloud projects get-iam-policy seu-projeto-id
```

### Timeout

Aumentar tempo limite (padrão: 60s):
```javascript
exports.onRecipeGenerated = functions
  .runWith({ timeoutSeconds: 120 })
  .firestore.document('recipes_generated/{docId}')
  .onCreate(...)
```

## 📚 Recursos

- [Firebase Functions Docs](https://firebase.google.com/docs/functions)
- [Cloud Functions Triggers](https://firebase.google.com/docs/functions/firestore-events)
- [Pricing Calculator](https://cloud.google.com/functions/pricing)

