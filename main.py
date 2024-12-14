import typing

from fastapi import FastAPI, Request
import uvicorn

from starlette import status
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from starlette.authentication import (
    AuthCredentials, AuthenticationBackend, AuthenticationError, SimpleUser
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
import base64
import binascii

from routers import auth, views

app = FastAPI()

app.mount('/static', StaticFiles(directory="static"), name="static")


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        if "Authorization" not in conn.headers:
            return

        auth = conn.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != 'basic':
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError('Invalid basic auth credentials')

        username, _, password = decoded.partition(":")
        # TODO: You'd want to verify the username and password here.
        return AuthCredentials(["authenticated"]), SimpleUser(username)


app.add_middleware(AuthenticationMiddleware, backend=BasicAuthBackend())
app.add_middleware(SessionMiddleware, secret_key='super-secret')


app.include_router(auth.router)
app.include_router(views.router)


@app.get('/')
def root():
    return RedirectResponse(url='/auth', status_code=status.HTTP_200_OK)


def main():
    uvicorn.run("main:app", port=3000, reload=True)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
