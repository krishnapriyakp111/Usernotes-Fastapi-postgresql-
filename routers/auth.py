from datetime import timedelta, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Form, status, Request, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import models
from database import SessionLocal, engine
from supporting_functions import get_flashed_messages, flash, redirect_to_login


from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
    responses={400: {'success': 'created'}}
)

SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


def authenticate_user(email: str, password: str, db):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not bcrypt_context.verify(password, user.password):
        return None
    return user


def create_access_token(email: str, user_id: int, f_name: str, expires_delta: timedelta):
    encode = {'sub': email, 'id': user_id, 'name': f_name}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_name: str = payload.get('name')
        if email is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user.')
        return {'email': email, 'user_id': user_id, 'user_name': user_name}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')


models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory='templates')
templates.env.globals['get_flashed_messages'] = get_flashed_messages


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def login_for_access_token(email, id, f_name):
    token = create_access_token(email, id, f_name, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}


user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get('/sign-up')
def home(request: Request):
    return templates.TemplateResponse('sign_up.html', {'request': request})


@router.post('/sign-up')
def homes(request: Request, db: Session = Depends(get_db), email: str = Form(...), firstName: str = Form(...),
          password1: str = Form(...), password2: str = Form(...)):
    user = db.query(models.User).filter(models.User.f_name == firstName).first()
    if user:
        flash(request, "username taken", "error")
        return RedirectResponse(url='/auth/sign-up', status_code=303)
    if password1 != password2:
        flash(request, "password not matching", "error")
        return RedirectResponse(url='/auth/sign-up', status_code=303)
    new_user = models.User(email=email, f_name=firstName, password=bcrypt_context.hash(password1))
    db.add(new_user)
    db.commit()
    flash(request, "success", "success")
    return RedirectResponse(url='/auth', status_code=303)


@router.get('/')
def login(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/')
def logins(request: Request, db: Session = Depends(get_db), email: str = Form('email'),
           password: str = Form('password')):
    user = authenticate_user(email, password, db)
    if user:
        token = login_for_access_token(user.email, user.id, user.f_name)
        redirect_response = RedirectResponse(url='/views/main', status_code=status.HTTP_302_FOUND)
        redirect_response.set_cookie(key="access_token", value=token['access_token'])
        return redirect_response
    flash(request, "user does not exist", "error")
    return RedirectResponse(url='/auth', status_code=303)


@router.get('/logout')
def login():
    return redirect_to_login()
