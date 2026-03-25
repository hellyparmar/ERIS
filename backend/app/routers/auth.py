from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.multitenant_models import User, Organization, UserRole, Store
from app.schemas.auth import UserRegister, UserLogin, UserResponse, Token
from app.services.auth_service import auth_service
from app.middleware.auth import get_current_user, oauth2_scheme
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve the profile of the currently authenticated user.
    
    Returns:
    - **User details** including email, full name, role, and organization.
    """
    return current_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user and create a corresponding retail organization.
    
    - **user_in**: Registration details.
    - **Organization**: Created automatically based on `organization_name`.
    - **Store**: A default "Main Store" is created for the new organization.
    """
    # Check if user already exists
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Create Organization if it's a new one
    organization = db.query(Organization).filter(Organization.name == user_in.organization_name).first()
    if not organization:
        organization = Organization(name=user_in.organization_name)
        db.add(organization)
        db.commit()
        db.refresh(organization)
        
        # Create Default Store for new organization
        default_store = Store(
            name="Main Store",
            code="MAIN",
            organization_id=organization.id,
            store_type="retail"
        )
        db.add(default_store)
        db.commit()
    
    # Create User
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=auth_service.get_password_hash(user_in.password),
        role=user_in.role,
        organization_id=organization.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and issue JWT access/refresh tokens.
    
    - **email**: User's registered email.
    - **password**: Plaintext password for verification.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not auth_service.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = auth_service.create_access_token(
        subject=user.email
    )
    refresh_token = auth_service.create_refresh_token(
        subject=user.email
    )
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Refresh an expired access token using a valid refresh token.
    """
    payload = auth_service.decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    access_token = auth_service.create_access_token(subject=user.email)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    """
    Invalidate the current access token.
    
    Note: Token is added to a server-side blacklist until expiry.
    """
    from app.utils.security import blacklist_token
    blacklist_token(token)
    return {"message": "Successfully logged out"}
