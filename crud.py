from sqlalchemy.orm import Session

try:
    from .models import Expense
    from .schemas import ExpenseCreate
except ImportError:  # pragma: no cover - supports running the file directly
    from models import Expense
    from schemas import ExpenseCreate


def create_expense(db: Session, expense: ExpenseCreate, user_id: int | None = None) -> Expense:
    db_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        user_id=user_id,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_expenses(db: Session, user_id: int | None = None) -> list[Expense]:
    query = db.query(Expense)
    if user_id is not None:
        query = query.filter(Expense.user_id == user_id)
    return query.all()


def get_expense(db: Session, expense_id: int, user_id: int | None = None) -> Expense | None:
    query = db.query(Expense).filter(Expense.id == expense_id)
    if user_id is not None:
        query = query.filter(Expense.user_id == user_id)
    return query.first()


def update_expense(db: Session, expense_id: int, updated: ExpenseCreate, user_id: int | None = None) -> Expense | None:
    db_expense = get_expense(db, expense_id, user_id=user_id)
    if not db_expense:
        return None

    db_expense.title = updated.title
    db_expense.amount = updated.amount
    db_expense.category = updated.category

    db.commit()
    db.refresh(db_expense)
    return db_expense


def delete_expense(db: Session, expense_id: int, user_id: int | None = None) -> bool:
    db_expense = get_expense(db, expense_id, user_id=user_id)
    if not db_expense:
        return False

    db.delete(db_expense)
    db.commit()
    return True
