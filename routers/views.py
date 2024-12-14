import json
from typing import Annotated
from routers.auth import get_current_user

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from supporting_functions import get_flashed_messages, flash, redirect_to_login

import models
from database import SessionLocal, engine

router = APIRouter(
    prefix='/views',
    tags=['views'],
    responses={400: {'success': 'created'}}
)


models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory='templates')
templates.env.globals['get_flashed_messages'] = get_flashed_messages


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get('/main')
def homee(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request.cookies.get('access_token'))
    if user is None:
        return redirect_to_login()
    notes = db.query(models.Note).filter(models.Note.user_id == user['user_id']).all()
    return templates.TemplateResponse('home.html', {'request': request, 'user': user, 'notes': notes})


@router.post('/main')
def homei(request: Request, db: Session = Depends(get_db), note: str = Form('note')):
    user = get_current_user(request.cookies.get('access_token'))
    if user is None:
        return redirect_to_login()
    if len(note) < 2:
        flash(request, "note is too short", "error")
        return RedirectResponse(url='/views/main', status_code=303)
    note = models.Note(content=note, user_id=user['user_id'])
    db.add(note)
    db.commit()
    flash(request, "note added successfully", "success")
    return RedirectResponse(url='/views/main', status_code=303)


@router.delete('/delete-note')
async def delete_note(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request.cookies.get('access_token'))
    inter = await request.body()
    note = json.loads(inter)  # this function expects a JSON from the INDEX.js file
    noteId = note['noteId']
    note = db.query(models.Note).filter(models.Note.id == noteId).first()
    if note:
        if note.user_id == user['user_id']:
            db.delete(note)
            db.commit()
    return RedirectResponse(url='/views/main', status_code=303)
