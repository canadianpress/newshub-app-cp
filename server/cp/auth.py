from datetime import datetime, timedelta
from logging import INFO, getLogger
from os import environ
from uuid import uuid4

from firebase_admin import auth
from firebase_admin import initialize_app as initialize_firebase_app
from firebase_admin.credentials import Certificate as FirebaseCertificate
from flask import Response, make_response
from newsroom.auth.utils import get_current_request, sign_user_by_email
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
SESSION_EXPIRY = timedelta(days=5)
REFRESH_THRESHOLD = timedelta(minutes=5)

blueprint = EndpointGroup("cp_auth", __name__)
logger = getLogger(__name__)
logger.setLevel(INFO)
firebase_app = initialize_firebase_app(
    credential=FirebaseCertificate(environ.get("FIREBASE_CONFIG"))
)


@blueprint.endpoint("/firebase_auth_token", auth=False)
async def firebase_auth_token(args, params, request: Request):
    token = request.get_url_arg("token")
    if not token:
        await flash(gettext("User token is not valid"), "danger")
        return request.redirect(url_for("auth.login", token_error=1))

    try:
        claims = auth.verify_id_token(
            token,
            firebase_app,
        )
    except Exception as e:
        logger.error(f"Failed to verify token: {e}")
        await flash(gettext("User token is not valid"), "danger")
        return request.redirect(url_for("auth.login", token_error=1))

    email = claims["email"]
    uid = claims["uid"]
    response = make_response(
        await sign_user_by_email(
            email, auth_type=AuthProviderType.FIREBASE, validate_login_attempt=True
        )
    )
    session_id = _get_cp_session_cookie(request) or str(uuid4())

    _update_cp_session(
        session_id, {"created_at": str(datetime.now().timestamp()), "uid": uid}
    )
    _set_cp_cookie(response, request, session_id)
    return response


@blueprint.endpoint("/firebase_credentials")
def get_id_token_from_session(args, params, request: Request):
    session_id = _get_cp_session_cookie(request)
    if not session_id:
        return {"error": "No session found"}, 401

    session_data = _get_session_data_from_redis(session_id)
    if not session_data:
        return {"error": "Invalid Session"}, 401

    try:
        token = auth.create_custom_token(session_data["uid"], app=firebase_app)
    except Exception as e:
        logger.error(f"Failed to create token: {e}")
        return {"error": "Invalid session"}, 401

    return {"token": token.decode("utf-8")}, 200


def _get_cp_session_cookie(request: Request):
    return parse_cookie(request.get_header("Cookie")).get(CP_SESSION_COOKIE_NAME)


def _update_cp_session(session_id: str, data: dict[str, str] | None = None) -> None:
    key = _get_redis_key(session_id)
    _get_redis().pipeline().hset(
        key, mapping={**(data or {}), "updated_at": str(datetime.now().timestamp())}
    ).expire(key, int(SESSION_EXPIRY.total_seconds())).execute()


def _set_cp_cookie(response: Response, request: Request, session_id: str) -> None:
    response.set_cookie(
        CP_SESSION_COOKIE_NAME,
        session_id,
        expires=datetime.now() + SESSION_EXPIRY,
        httponly=True,
        secure=request.url.startswith("https"),
        samesite="Lax",
        path="/",
    )


def _get_redis() -> Redis:
    return get_current_async_app().wsgi.redis


def _get_redis_key(session_id: str) -> str:
    return f"{CP_SESSION_COOKIE_NAME}:{session_id}"


def _get_session_data_from_redis(session_id: str) -> dict[str, str]:
    value = _get_redis().hgetall(_get_redis_key(session_id))
    return {k.decode("utf-8"): v.decode("utf-8") for k, v in value.items()}


def init_refresh_session_hook(app):
    @app.after_request
    async def refresh_cp_session(response):
        request = get_current_request()
        session_id = _get_cp_session_cookie(request)
        if not session_id:
            return response

        session_data = _get_session_data_from_redis(session_id)
        last_updated = datetime.now().timestamp() - float(session_data["updated_at"])
        if last_updated > REFRESH_THRESHOLD.total_seconds():
            _update_cp_session(session_id)
            _set_cp_cookie(response, request, session_id)

        return response


def init_app(app):
    init_refresh_session_hook(app)
    get_current_async_app().wsgi.register_endpoint(blueprint)
