"""Auth: register, login, and OAuth/OIDC login."""
from urllib.parse import urlencode
import secrets

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import (
    APP_BASE_URL,
    OAUTH_BACKEND_BASE_URL,
    OAUTH_FRONTEND_BASE_URL,
    GOOGLE_OIDC_DISCOVERY_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
)
from app.database import get_db
from app.models import User
from app.services.auth import hash_password, verify_password, create_token, decode_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth = OAuth()


def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Require valid Bearer token. Raises 401 if missing or invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login required")
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


class AuthBody(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


def _provider_settings() -> dict[str, str]:
    return {
        "name": "google",
        "server_metadata_url": GOOGLE_OIDC_DISCOVERY_URL,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "scope": "openid email profile",
    }


def _ensure_provider_enabled() -> dict[str, str]:
    cfg = _provider_settings()
    missing = []
    if not cfg["server_metadata_url"]:
        missing.append("server metadata URL")
    if not cfg["client_id"]:
        missing.append("client ID")
    if not cfg["client_secret"]:
        missing.append("client secret")
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Google OAuth is not configured (missing: {', '.join(missing)}).",
        )
    return cfg


def _get_oauth_client():
    cfg = _ensure_provider_enabled()
    client = oauth.create_client("google")
    if client:
        return client
    oauth.register(
        name=cfg["name"],
        server_metadata_url=cfg["server_metadata_url"],
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        client_kwargs={"scope": cfg["scope"]},
    )
    return oauth.create_client("google")


def _backend_base_url(request: Request) -> str:
    if OAUTH_BACKEND_BASE_URL:
        return OAUTH_BACKEND_BASE_URL.rstrip("/")
    return str(request.base_url).rstrip("/")


def _frontend_base_url(request: Request) -> str:
    if OAUTH_FRONTEND_BASE_URL:
        return OAUTH_FRONTEND_BASE_URL.rstrip("/")
    host = (request.url.hostname or "").lower()
    if host in {"localhost", "127.0.0.1"}:
        return "http://localhost:8080"
    if APP_BASE_URL and "your-username.github.io" not in APP_BASE_URL:
        return APP_BASE_URL.rstrip("/")
    return str(request.base_url).rstrip("/")


def _oauth_redirect_uri(request: Request) -> str:
    return f"{_backend_base_url(request)}/api/auth/oauth/google/callback"


def _extract_email(userinfo: dict) -> str:
    email = (userinfo.get("email") or "").strip().lower()
    if not email:
        preferred_username = (userinfo.get("preferred_username") or "").strip().lower()
        if "@" in preferred_username:
            email = preferred_username
    if not email:
        upn = (userinfo.get("upn") or "").strip().lower()
        if upn:
            email = upn
    return email


def _build_frontend_redirect(request: Request, *, token: str | None = None, email: str | None = None, error: str | None = None):
    params: dict[str, str] = {}
    if token and email:
        params["token"] = token
        params["email"] = email
    if error:
        params["oauth_error"] = error
    query = urlencode(params)
    base = _frontend_base_url(request)
    target = f"{base}/"
    if query:
        target = f"{target}?{query}"
    return RedirectResponse(url=target)


@router.post("/register")
def api_register(body: AuthBody, db: Session = Depends(get_db)):
    """Register new user."""
    if db.query(User).filter(User.email == body.email.lower().strip()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = User(email=body.email.lower().strip(), password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.email)
    return {"token": token, "email": user.email, "user_id": user.id}


@router.post("/login")
def api_login(body: AuthBody, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user.id, user.email)
    return {"token": token, "email": user.email, "user_id": user.id}


@router.get("/me")
def get_me(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    """Get current user from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        return {"logged_in": False}
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        return {"logged_in": False}
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"logged_in": False}
    return {"logged_in": True, "email": user.email, "user_id": user.id}


@router.get("/oauth/google/start")
async def oauth_google_start(request: Request):
    """Start Google OAuth login flow."""
    client = _get_oauth_client()
    redirect_uri = _oauth_redirect_uri(request)
    nonce = secrets.token_urlsafe(16)
    return await client.authorize_redirect(request, redirect_uri, nonce=nonce)


@router.get("/oauth/google/callback")
async def oauth_google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback, create/find user, issue app token, and redirect to frontend."""
    client = _get_oauth_client()
    try:
        token = await client.authorize_access_token(request)
    except OAuthError as exc:
        return _build_frontend_redirect(request, error=f"Google login failed: {exc.error}")
    except Exception:
        return _build_frontend_redirect(request, error="Google login failed during token exchange.")

    userinfo: dict = token.get("userinfo") or {}
    if not userinfo:
        try:
            parsed = await client.parse_id_token(request, token)
            userinfo = dict(parsed) if parsed else {}
        except Exception:
            userinfo = {}
    if not userinfo:
        return _build_frontend_redirect(request, error="Google login failed: no user profile returned.")

    email = _extract_email(userinfo)
    if not email:
        return _build_frontend_redirect(request, error="Google login failed: email not provided.")

    if userinfo.get("email_verified") is False:
        return _build_frontend_redirect(request, error="Google login failed: email is not verified.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create OAuth users with a random internal password hash.
        user = User(email=email, password_hash=hash_password(secrets.token_urlsafe(32)))
        db.add(user)
        db.commit()
        db.refresh(user)

    app_token = create_token(user.id, user.email)
    return _build_frontend_redirect(request, token=app_token, email=user.email)
