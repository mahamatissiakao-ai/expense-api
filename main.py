from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

try:
    from .crud import create_expense, delete_expense, get_expense, get_expenses, update_expense
    from .database import get_db, init_db
    from .models import User
    from .schemas import ExpenseCreate, ExpenseResponse, TokenResponse, UserCreate, UserLogin
    from .security import create_access_token, get_current_user, get_password_hash, verify_password
except ImportError:  # pragma: no cover - supports running the file directly
    from crud import create_expense, delete_expense, get_expense, get_expenses, update_expense
    from database import get_db, init_db
    from models import User
    from schemas import ExpenseCreate, ExpenseResponse, TokenResponse, UserCreate, UserLogin
    from security import create_access_token, get_current_user, get_password_hash, verify_password


app = FastAPI()
init_db()


@app.post("/register", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == str(user.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    db_user = User(
        name=user.name,
        email=str(user.email),
        password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = create_access_token({"sub": db_user.email})
    return TokenResponse(access_token=token)


@app.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == str(user.email)).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email})
    return TokenResponse(access_token=token)


@app.post("/expenses", response_model=ExpenseResponse)
def create_expense_endpoint(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_expense(db, expense, user_id=current_user.id)


@app.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_expenses(db, user_id=current_user.id)


@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def read_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = get_expense(db, expense_id, user_id=current_user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense_endpoint(
    expense_id: int,
    updated: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = update_expense(db, expense_id, updated, user_id=current_user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.delete("/expenses/{expense_id}")
def delete_expense_endpoint(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = delete_expense(db, expense_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted"}