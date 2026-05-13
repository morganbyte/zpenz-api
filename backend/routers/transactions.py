from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import List, Optional
from datetime import datetime, timedelta
from backend.database import get_db
from backend.dependencies import get_current_user
from backend import models
from backend import schemas

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Registrar una nueva transacción (ingreso o gasto)"""
    # Validar el tipo de transacción.
    if transaction.type not in ["income", "expense"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tipo debe ser 'ingreso' o 'gasto'"
        )
    
    # Verificar que la cuenta existe y pertenece al usuario.
    account = db.query(models.Account).filter(
        models.Account.id == transaction.account_id,
        models.Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    
    # Verificar que la categoría existe y pertenece al usuario.
    category = db.query(models.Category).filter(
        models.Category.id == transaction.category_id,
        models.Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    # Verificar que el tipo de transacción coincide con el tipo de categoría.
    if transaction.type != category.type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La categoría '{category.name}' es de tipo '{category.type}', pero la transacción es de tipo '{transaction.type}'"
        )
    
    # Validar monto positivo.
    if transaction.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto debe ser mayor a 0"
        )

    transaction_type = models.TransactionType.INCOME if transaction.type == "income" else models.TransactionType.EXPENSE
    
    # Crear la transacción.
    new_transaction = models.Transaction(
        amount=transaction.amount,
        description=transaction.description,
        type=transaction_type,
        account_id=transaction.account_id,
        category_id=transaction.category_id,
        user_id=current_user.id
    )

    # Actualizar balance de la cuenta.
    if transaction.type == "income":
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction      

@router.get("/", response_model=List[schemas.Transaction])
def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener las transacciones del usuario con filtros opcionales"""
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )

    # Aplicar filtros
    if account_id:
        query = query.filter(models.Transaction.account_id == account_id)

    if category_id:
        query = query.filter(models.Transaction.category_id == category_id)

    if type:
        if type not in ["income", "expense"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tipo debe ser 'ingreso' o 'gasto'"
            )
        transaction_type = models.TransactionType.INCOME if type == "income" else models.TransactionType.EXPENSE
        query = query.filter(models.Transaction.type == transaction_type)

    # Ordenar por fecha descendente (más reciente primero)
    transactions = query.order_by(models.Transaction.date.desc()).offset(skip).limit(limit).all()

    return transactions

@router.get("/recent", response_model=List[schemas.Transaction])
def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener las transacciones más recientes del usuario"""

    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).order_by(models.Transaction.date.desc()).limit(limit).all()

    return transactions

@router.get("/summary", response_model=dict)
def get_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener resumen financiero total"""

    # Total de ingresos
    total_income = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.type == models.TransactionType.INCOME
    ).scalar() or 0.0

    # Total de gastos
    total_expenses = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.type == models.TransactionType.EXPENSE
    ).scalar() or 0.0

    # Balance 
    balance = total_income - total_expenses

    # Contar transacciones 
    transaction_count = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).count()

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
        "transaction_count": transaction_count
    }

@router.get("/by-category", response_model=List[dict])
def get_by_category(
    type: str = Query(..., description="Ingreso o gasto"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener transacciones agrupadas por categoría"""
    
    if type not in ["income", "expense"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tipo debe ser 'ingreso' o 'gasto'"
        )
    
    transaction_type = models.TransactionType.INCOME if type == "income" else models.TransactionType.EXPENSE
    
    results = db.query(
        models.Category.name,
        models.Category.id,
        func.sum(models.Transaction.amount).label('total'),
        func.count(models.Transaction.id).label('count')
    ).join(
        models.Transaction, models.Transaction.category_id == models.Category.id
    ).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.type == transaction_type
    ).group_by(
        models.Category.id, models.Category.name
    ).all()

    return [
        {
            "category_id": r.id,
            "category_name": r.name,
            "total": r.total,
            "transaction_count": r.count
        }
        for r in results
    ]

@router.get("/monthly_summary", response_model=dict)
def get_monthly_summary(
    year: int = Query(datetime.now().year),
    month: int = Query(datetime.now().month, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener resumen del mes específico"""

    # Total de ingresos del mes
    total_income = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.type == models.TransactionType.INCOME,
        extract('year', models.Transaction.date) == year,
        extract('month', models.Transaction.date) == month
    ).scalar() or 0.0

    # Total de gastos del mes
    total_expenses = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.type == models.TransactionType.EXPENSE,
        extract('year', models.Transaction.date) == year,
        extract('month', models.Transaction.date) == month
    ).scalar() or 0.0

    # Balance del mes
    balance = total_income - total_expenses

    return {
        "year": year,
        "month": month,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance
    }

@router.get("/{transaction_id}", response_model=schemas.Transaction)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener una transacción específica"""

    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transacción no encontrada"
        )

    return transaction

@router.put("/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(
    transaction_id: int,
    transaction_update: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Actualizar una transacción"""

    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transacción no encontrada"
        )
    
    # Obtener una cuenta anterior
    old_account = db.query(models.Account).filter(
        models.Account.id == transaction.account_id
    ).first()

    # Revertir el cambio anterior en el balance
    if transaction.type == models.TransactionType.INCOME:
        old_account.balance -= transaction.amount
    else:
        old_account.balance += transaction.amount

    # Verificar nueva cuenta
    new_account = db.query(models.Account).filter(
        models.Account.id == transaction_update.account_id,
        models.Account.user_id == current_user.id
    ).first()

    if not new_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )

    # Verificar categoría
    category = db.query(models.Category).filter(
        models.Category.id == transaction_update.category_id,
        models.Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    transaction_type = models.TransactionType.INCOME if transaction_update.type == "income" else models.TransactionType.EXPENSE

    # Actualizar transacción
    transaction.amount = transaction_update.amount
    transaction.description = transaction_update.description
    transaction.type = transaction_type
    transaction.account_id = transaction_update.account_id
    transaction.category_id = transaction_update.category_id

    # Aplicar nuevo cambio en el balance
    if transaction_update.type == "income":
        new_account.balance += transaction_update.amount
    else:
        new_account.balance -= transaction_update.amount

    db.commit()
    db.refresh(transaction)

    return transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Eliminar una transacción"""
    
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transacción no encontrada"
        )
    
    # Obtener cuenta
    account = db.query(models.Account).filter(
        models.Account.id == transaction.account_id
    ).first()
    
    # Revertir el cambio en el balance
    if transaction.type == models.TransactionType.INCOME:
        account.balance -= transaction.amount
    else:
        account.balance += transaction.amount
    
    db.delete(transaction)
    db.commit()
    
    return None
