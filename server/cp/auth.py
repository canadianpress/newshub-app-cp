from datetime import datetime, timedelta
from logging import INFO, getLogger
from os import environ
from uuid import uuid4

from firebase_admin import auth
from firebase_admin import initialize_app as initialize_firebase_app
from firebase_admin.credentials import Certificate as FirebaseCertificate
from flask import Response, make_response
from newsroom.auth.utils import sign_user_by_email
from newsroom.flask import flash
from newsroom.types import AuthProviderType
from quart_babel import gettext
from redis import Redis
from superdesk.core import get_current_async_app
from superdesk.core.types import Request
from superdesk.core.web import EndpointGroup
from superdesk.flask import url_for
from werkzeug.http import parse_cookie

CP_SESSION_COOKIE_NAME = "cp_session"
SESSION_EXPIRY = timedelta(days=14)

blueprint = EndpointGroup("cp_auth", __name__)
logger = getLogger(__name__)
logger.setLevel(INFO)
firebase_app = initialize_firebase_app(
    credential=FirebaseCertificate(environ.get("FIREBASE_CONFIG"))
)


@blueprint.endpoint("/firebase_auth_token", auth=False)
async def firebase_auth_token(args, params, request: Request):
    session_cookie = _get_cp_session_cookie(request)
    token = request.get_url_arg("token")
    if not token:
        await flash(gettext("User token is not valid"), "danger")
        response = make_response(request.redirect(url_for("auth.login")))
        if not session_cookie:
            response = _start_cp_session(response, request)
        return response

    try:
        claims = auth.verify_id_token(
            token,
            firebase_app,
        )
    except Exception as e:
        logger.error(f"Failed to verify token: {e}")
        await flash(gettext("User token is not valid"), "danger")
        response = make_response(request.redirect(url_for("auth.login", token_error=1)))
        if not session_cookie:
            response = _start_cp_session(response, request)
        return response

    email = claims["email"]
    uid = claims["uid"]
    response = make_response(
        await sign_user_by_email(
            email, auth_type=AuthProviderType.FIREBASE, validate_login_attempt=True
        )
    )
    if not session_cookie:
        session_id = str(uuid4())
        response = _start_cp_session(response, request, session_id)
    else:
        session_id = session_cookie

    response = _update_cp_session(
        response,
        request,
        session_id,
        {"email": email, "uid": uid},
    )
    return response


@blueprint.endpoint("/firebase_credentials")
def get_id_token_from_session(args, params, request: Request):
    session_cookie = _get_cp_session_cookie(request)
    if not session_cookie:
        return {"error": "No session found"}, 401

    session_data = _get_session_data_from_redis(session_cookie)
    if not session_data:
        return {"error": "Invalid Session"}, 401

    uid = session_data["uid"]
    try:
        token = auth.create_custom_token(uid, app=firebase_app)
    except Exception as e:
        logger.error(f"Failed to create token: {e}")
        return {"error": "Invalid session"}, 401

    response = make_response({"token": token.decode("utf-8")})
    response = _update_cp_session(response, request, session_cookie)
    return response


def _get_redis() -> Redis:
    return get_current_async_app().wsgi.redis


def _get_cp_session_cookie(request: Request):
    cookie_header = request.get_header("Cookie")
    cookies = parse_cookie(cookie_header)
    return cookies.get(CP_SESSION_COOKIE_NAME)


def _start_cp_session(response: Response, request: Request, session_id: str = None):
    if session_id is None:
        session_id = str(uuid4())
    redis = _get_redis()
    key = _get_redis_key(session_id)
    redis.hset(key, mapping={"created_at": str(datetime.now().timestamp())})
    redis.expire(key, int(SESSION_EXPIRY.total_seconds()))
    _set_cp_cookie(response, request, session_id)
    return response


def _update_cp_session(
    response: Response, request: Request, session_id: str, data: dict = None
):
    redis = _get_redis()
    key = _get_redis_key(session_id)
    redis.hset(
        key,
        mapping={
            **(data if data else {}),
            "updated_at": str(datetime.now().timestamp()),
        },
    )
    redis.expire(key, int(SESSION_EXPIRY.total_seconds()))
    _set_cp_cookie(response, request, session_id)
    return response


def _get_session_data_from_redis(session_id: str):
    redis = _get_redis()
    key = _get_redis_key(session_id)
    value = redis.hgetall(key)
    return {k.decode("utf-8"): v.decode("utf-8") for k, v in value.items()}


def _get_redis_key(session_id: str):
    return f"cp_session:{session_id}"


def _set_cp_cookie(response: Response, request: Request, session_id: str):
    response.set_cookie(
        CP_SESSION_COOKIE_NAME,
        session_id,
        expires=datetime.now() + SESSION_EXPIRY,
        httponly=True,
        secure=request.url.startswith("https"),
        samesite="Lax",
        path="/",
    )


def init_app(app):
    get_current_async_app().wsgi.register_endpoint(blueprint)
