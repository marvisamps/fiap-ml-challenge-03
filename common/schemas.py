from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

# Schema genérico para eventos simulados
class Event(BaseModel):
    event_time: datetime
    user_id: str
    event_name: str  # recipe_view | save_recipe | like | recipe_generate | reco_impression | reco_click
    recipe_id: Optional[str] = None
    diet_selected: Optional[str] = None
    platform: Optional[str] = None
    app_version: Optional[str] = None
    source: Optional[str] = None
    session_id: Optional[str] = None
    extras: Optional[Dict] = None

# Schemas para eventos reais do Firebase/App
class RecipeGenerated(BaseModel):
    """Evento quando usuário gera uma nova receita"""
    recipe_name: str = Field(..., alias="recipeName")
    query: str
    full_recipe: str = Field(..., alias="fullRecipe")
    user_id: str = Field(..., alias="userId")
    created_at: datetime = Field(..., alias="createdAt")
    calories: Optional[int] = None
    image_url: Optional[str] = Field(None, alias="imageUrl")
    preparation_time: Optional[int] = Field(None, alias="preparationTime")
    servings: Optional[int] = None
    
    class Config:
        populate_by_name = True

class RecipeFavorited(BaseModel):
    """Evento quando usuário favorita uma receita"""
    name: str
    response: str
    added_at: datetime = Field(..., alias="addedAt")
    user_id: str = Field(..., alias="userId")
    query: Optional[str] = ""
    image_url: Optional[str] = Field(None, alias="imageUrl")
    
    class Config:
        populate_by_name = True

class FirebaseEvent(BaseModel):
    """Wrapper para eventos do Firebase"""
    event_type: str  # "recipe_generate" | "save_recipe"
    user_id: str
    timestamp: datetime
    data: Dict  # dados específicos do evento

# Schemas de resposta da API
class RecItem(BaseModel):
    recipe_id: str
    score: float
    reason: str = "model"
    recipe_name: Optional[str] = None
    query: Optional[str] = None

class RecResponse(BaseModel):
    user_id: str
    items: List[RecItem]

