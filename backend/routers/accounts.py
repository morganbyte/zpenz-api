from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.dependencies import get_current_user
from backend import models
from backend import schemas

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"]
)

@router.post("/", response_model=schemas.Account, status_code=status.HTTP_201_CREATED)
def create_account(
    account: schemas.AccountCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Crear una nueva cuenta bancaria/billetera para el usuario autenticado"""

    # Verificar que el tipo de cuenta sea válido.
    valid_types = ["banco", "efectivo", "tarjeta", "ahorro", "inversion"]
    if account.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de cuenta inválido. Tipos válidos: {valid_types}"
        )
    
    # Crear nueva cuenta.
    new_account = models.Account(
        name=account.name,
        type=account.type,
        balance=account.initial_balance,
        user_id=current_user.id
    )


    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account

@router.get("/", response_model=List[schemas.Account])
def get_accounts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener todas las cuentas asociadas al usuario autenticado"""
    accounts = db.query(models.Account).filter(models.Account.user_id == current_user.id).all()
    return accounts

@router.get("/{account_id}", response_model=schemas.Account)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obetener una cuenta específica"""
    account = db.query(models.Account).filter(
        models.Account.id == account_id,
        models.Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    
    return account

@router.put("/{account_id}", response_model=schemas.Account)
def update_account(
    account_id: int,
    account_update: schemas.AccountCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Actualizar información de una cuenta"""
    account = db.query(models.Account).filter(
        models.Account.id == account_id,
        models.Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )

    # Actualizar los campos de la cuenta.
    account.name = account_update.name
    account.type = account_update.type

    db.commit()
    db.refresh(account)

    return account

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Eliminar una cuenta"""
    account = db.query(models.Account).filter(
        models.Account.id == account_id,
        models.Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    
    # Verificar si tiene transacciones asociadas
    transaction_count = db.query(models.Transaction).filter(
        models.Transaction.account_id == account_id
    ).count()

    if transaction_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la cuenta porque tiene {transaction_count} transacciones asociadas"
        )
    
    db.delete(account)
    db.commit()

    return None

@router.get("/summary/total", response_model=dict)
def get_total_balance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtener el balance total de todas las cuentas del usuario"""
    accounts = db.query(models.Account).filter(
        models.Account.user_id == current_user.id
    ).all()

    total_balance = sum(account.balance for account in accounts)

    account_summary = [
        {
            "id": account.id,
            "name": account.name,
            "type": account.type,
            "balance": account.balance
        }
        for account in accounts
    ]

    return {
        "total_balance": total_balance,
        "account_count": len(accounts),
        "accounts": account_summary
    }