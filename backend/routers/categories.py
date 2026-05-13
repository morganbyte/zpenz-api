from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.dependencies import get_current_user
from backend import models
from backend import schemas

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.post("/", response_model=schemas.Category, status_code=status.HTTP_201_CREATED)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Crear nueva categoría personalizada"""
    
    # Validar tipo
    if category.type not in ["income", "expense"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tipo debe ser 'income' o 'expense'"
        )
    
    # Verificar que no exista una categoría con el mismo nombre para este usuario
    existing = db.query(models.Category).filter(
        models.Category.name == category.name,
        models.Category.user_id == current_user.id,
        models.Category.type == category.type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una categoría '{category.name}' de tipo '{category.type}'"
        )
    
    # Crear categoría
    new_category = models.Category(
        name=category.name,
        type=category.type,
        user_id=current_user.id
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category

@router.get("/", response_model=List[schemas.Category])
def get_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener todas las categorías del usuario"""
    
    categories = db.query(models.Category).filter(
        models.Category.user_id == current_user.id
    ).all()
    
    return categories

@router.get("/income", response_model=List[schemas.Category])
def get_income_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener solo categorías de ingresos"""
    
    categories = db.query(models.Category).filter(
        models.Category.user_id == current_user.id,
        models.Category.type == "income"
    ).all()
    
    return categories

@router.get("/expense", response_model=List[schemas.Category])
def get_expense_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener solo categorías de gastos"""
    
    categories = db.query(models.Category).filter(
        models.Category.user_id == current_user.id,
        models.Category.type == "expense"
    ).all()
    
    return categories

@router.put("/{category_id}", response_model=schemas.Category)
def update_category(
    category_id: int,
    category_update: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Actualizar una categoría"""
    
    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    # Actualizar campos
    category.name = category_update.name
    category.type = category_update.type
    
    db.commit()
    db.refresh(category)
    
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Eliminar una categoría"""
    
    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    # Verificar si tiene transacciones asociadas
    transaction_count = db.query(models.Transaction).filter(
        models.Transaction.category_id == category_id
    ).count()
    
    if transaction_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la categoría porque tiene {transaction_count} transacciones asociadas"
        )
    
    db.delete(category)
    db.commit()
    
    return None

@router.post("/defaults", status_code=status.HTTP_201_CREATED)
def create_default_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Crear categorías por defecto para el usuario"""
    
    # Verificar si ya tiene categorías
    existing_count = db.query(models.Category).filter(
        models.Category.user_id == current_user.id
    ).count()
    
    if existing_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene categorías creadas"
        )
    
    # Categorías por defecto
    default_categories = [
        # Ingresos
        {"name": "Salario", "type": "income"},
        {"name": "Freelance", "type": "income"},
        {"name": "Inversiones", "type": "income"},
        {"name": "Otros ingresos", "type": "income"},
        
        # Gastos
        {"name": "Alimentación", "type": "expense"},
        {"name": "Transporte", "type": "expense"},
        {"name": "Vivienda", "type": "expense"},
        {"name": "Entretenimiento", "type": "expense"},
        {"name": "Salud", "type": "expense"},
        {"name": "Educación", "type": "expense"},
        {"name": "Servicios", "type": "expense"},
        {"name": "Compras", "type": "expense"},
        {"name": "Otros gastos", "type": "expense"},
    ]
    
    created_categories = []
    for cat_data in default_categories:
        category = models.Category(
            name=cat_data["name"],
            type=cat_data["type"],
            user_id=current_user.id
        )
        db.add(category)
        created_categories.append(cat_data["name"])
    
    db.commit()
    
    return {
        "message": "Categorías por defecto creadas exitosamente",
        "categories_created": len(created_categories),
        "categories": created_categories
    }
