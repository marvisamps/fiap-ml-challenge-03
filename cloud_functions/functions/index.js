/**
 * Firebase Cloud Functions para Sincronização Automática
 * Dispara automaticamente quando dados são escritos no Firestore
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const fetch = require('node-fetch');

admin.initializeApp();

// URL da sua API (configurar no Firebase Console)
const API_URL = functions.config().api.url || 'https://your-api.com';

/**
 * Trigger quando uma receita é gerada
 * Dispara em: firestore.document('recipes_generated/{docId}').onCreate()
 */
exports.onRecipeGenerated = functions.firestore
  .document('recipes_generated/{docId}')
  .onCreate(async (snap, context) => {
    const recipe = snap.data();
    const docId = context.params.docId;
    
    console.log(`📝 Nova receita gerada: ${recipe.recipeName}`);
    
    // Preparar payload para a API
    const payload = {
      recipeName: recipe.recipeName,
      query: recipe.query || '',
      fullRecipe: recipe.fullRecipe || '',
      userId: recipe.userId,
      createdAt: recipe.createdAt ? recipe.createdAt.toDate().toISOString() : new Date().toISOString(),
      calories: recipe.calories || null,
      imageUrl: recipe.imageUrl || null,
      preparationTime: recipe.preparationTime || null,
      servings: recipe.servings || null
    };
    
    try {
      // Enviar para a API
      const response = await fetch(`${API_URL}/firebase/recipe-generated`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`API retornou ${response.status}`);
      }
      
      const result = await response.json();
      console.log(`✅ Receita enviada para API: ${result.recipe_id}`);
      
      // Opcional: marcar como sincronizado no Firestore
      await snap.ref.update({
        synced: true,
        syncedAt: admin.firestore.FieldValue.serverTimestamp(),
        recipeId: result.recipe_id
      });
      
      return result;
      
    } catch (error) {
      console.error(`❌ Erro ao enviar para API: ${error.message}`);
      
      // Opcional: marcar erro no Firestore
      await snap.ref.update({
        synced: false,
        syncError: error.message,
        lastSyncAttempt: admin.firestore.FieldValue.serverTimestamp()
      });
      
      throw error;
    }
  });


/**
 * Trigger quando uma receita é favoritada
 * Dispara em: users/{userId}/favoriteLists/{listId}/items/{recipeId}
 * Estrutura aninhada de favoritos
 */
exports.onRecipeFavorited = functions.firestore
  .document('users/{userId}/favoriteLists/{listId}/items/{recipeId}')
  .onCreate(async (snap, context) => {
    const recipe = snap.data();
    const userId = context.params.userId;
    const listId = context.params.listId;
    const recipeId = context.params.recipeId;
    
    console.log(`⭐ Receita favoritada por ${userId}: ${recipe.name || recipeId}`);
    
    // Preparar payload para a API
    const payload = {
      name: recipe.name || recipe.recipeName || 'Receita Favorita',
      response: recipe.response || recipe.fullRecipe || '',
      addedAt: recipe.addedAt ? recipe.addedAt.toDate().toISOString() : new Date().toISOString(),
      userId: userId,
      query: recipe.query || '',
      imageUrl: recipe.imageUrl || null
    };
    
    try {
      // Enviar para a API
      const response = await fetch(`${API_URL}/firebase/recipe-favorited`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`API retornou ${response.status}`);
      }
      
      const result = await response.json();
      console.log(`✅ Favorito enviado para API: ${result.recipe_id}`);
      
      // Opcional: marcar como sincronizado
      await snap.ref.update({
        synced: true,
        syncedAt: admin.firestore.FieldValue.serverTimestamp(),
        recipeId: result.recipe_id,
        listId: listId
      });
      
      return result;
      
    } catch (error) {
      console.error(`❌ Erro ao enviar para API: ${error.message}`);
      
      await snap.ref.update({
        synced: false,
        syncError: error.message,
        lastSyncAttempt: admin.firestore.FieldValue.serverTimestamp()
      });
      
      throw error;
    }
  });


/**
 * Função HTTP para sincronização manual em lote
 * Chame via: POST https://your-region-your-project.cloudfunctions.net/syncManual
 */
exports.syncManual = functions.https.onRequest(async (req, res) => {
  if (req.method !== 'POST') {
    res.status(405).send('Method Not Allowed');
    return;
  }
  
  console.log('🔄 Iniciando sincronização manual...');
  
  try {
    const db = admin.firestore();
    
    // Buscar documentos não sincronizados
    const generatedSnapshot = await db.collection('recipes_generated')
      .where('synced', '==', false)
      .limit(100)
      .get();
    
    const events = [];
    
    // Processar receitas geradas
    generatedSnapshot.forEach(doc => {
      const data = doc.data();
      events.push({
        event_type: 'recipe_generate',
        user_id: data.userId,
        timestamp: data.createdAt ? data.createdAt.toDate().toISOString() : new Date().toISOString(),
        data: {
          recipeName: data.recipeName,
          query: data.query,
          fullRecipe: data.fullRecipe
        }
      });
    });
    
    // Buscar receitas favoritadas (collection group query)
    // Busca em todas as coleções "items" independente da estrutura
    const favoritedSnapshot = await db.collectionGroup('items')
      .where('synced', '==', false)
      .limit(100)
      .get();
    
    // Processar receitas favoritadas
    favoritedSnapshot.forEach(doc => {
      const data = doc.data();
      // Extrair userId do path: users/{userId}/favoriteLists/{hash}/items/{recipeId}
      const pathParts = doc.ref.path.split('/');
      const userId = pathParts.length >= 2 && pathParts[0] === 'users' ? pathParts[1] : 'unknown';
      
      events.push({
        event_type: 'save_recipe',
        user_id: userId,
        timestamp: data.addedAt ? data.addedAt.toDate().toISOString() : new Date().toISOString(),
        data: {
          name: data.name || data.recipeName,
          response: data.response || data.fullRecipe
        }
      });
    });
    
    if (events.length === 0) {
      res.json({ message: 'Nenhum evento para sincronizar', count: 0 });
      return;
    }
    
    // Enviar em lote para a API
    const response = await fetch(`${API_URL}/firebase/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(events)
    });
    
    if (!response.ok) {
      throw new Error(`API retornou ${response.status}`);
    }
    
    const result = await response.json();
    
    console.log(`✅ Sincronizados ${result.processed} eventos`);
    
    res.json({
      message: 'Sincronização completa',
      processed: result.processed,
      total: events.length
    });
    
  } catch (error) {
    console.error(`❌ Erro na sincronização: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});


/**
 * Função agendada que roda periodicamente
 * Configure no Firebase Console: schedule.every('5 minutes')
 */
exports.syncScheduled = functions.pubsub
  .schedule('every 5 minutes')
  .onRun(async (context) => {
    console.log('⏰ Executando sincronização agendada...');
    
  try {
    const db = admin.firestore();
    
    // Buscar documentos não sincronizados
    const generatedSnapshot = await db.collection('recipes_generated')
      .where('synced', '!=', true)
      .limit(50)
      .get();
    
    // Buscar favoritos não sincronizados (collection group)
    const favoritedSnapshot = await db.collectionGroup('items')
      .where('synced', '!=', true)
      .limit(50)
      .get();
    
    let syncCount = 0;
    
    // Processar e marcar como sincronizados
    const batch = db.batch();
    
    generatedSnapshot.forEach(doc => {
      batch.update(doc.ref, { synced: true, syncedAt: admin.firestore.FieldValue.serverTimestamp() });
      syncCount++;
    });
    
    favoritedSnapshot.forEach(doc => {
      batch.update(doc.ref, { synced: true, syncedAt: admin.firestore.FieldValue.serverTimestamp() });
      syncCount++;
    });
    
    await batch.commit();
      
      console.log(`✅ Marcados ${syncCount} documentos como sincronizados`);
      
      return null;
      
    } catch (error) {
      console.error(`❌ Erro na sincronização agendada: ${error.message}`);
      throw error;
    }
  });

