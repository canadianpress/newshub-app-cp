import logging
from datetime import datetime, timedelta
from os import environ

import google.oauth2.id_token
from firebase_admin import auth
from firebase_admin import initialize_app as initialize_firebase_app
from firebase_admin.credentials import Certificate as FirebaseCertificate
from firebase_admin.exceptions import FirebaseError
from flask import Blueprint, make_response
from google.auth.transport import requests
from newsroom.auth.utils import (
    get_current_request,
    is_valid_session,
    sign_user_by_email,
)
from newsroom.auth.views import (
    blueprint as auth_blueprint,
)
from newsroom.auth.views import (
    firebase_auth_token as core_firebase_auth_token,
)
from newsroom.celery_app import celery
from newsroom.flask import flash
from newsroom.types import AuthProviderType
from quart_babel import gettext
from superdesk.core import get_app_config, get_current_app, get_current_async_app
from superdesk.core.types import Request
from superdesk.core.web import EndpointGroup
from superdesk.flask import redirect, session, url_for
from werkzeug.http import parse_cookie

blueprint = EndpointGroup("cp_auth", __name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
firebase_app = initialize_firebase_app(
    credential=FirebaseCertificate(environ.get("FIREBASE_CONFIG")), name="cp_auth"
)


@blueprint.endpoint("/firebase_auth_token", auth=False)
async def firebase_auth_token(args, params, request: Request):
    token = request.get_url_arg("token")
    if token:
        try:
            claims = auth.verify_id_token(
                token,
                firebase_app,
            )
        except ValueError as err:
            logger.error(err)
            await flash(gettext("User token is not valid"), "danger")
            return request.redirect(url_for("auth.login", token_error=1))

        email = claims["email"]
        response = make_response(
            await sign_user_by_email(
                email, auth_type=AuthProviderType.FIREBASE, validate_login_attempt=True
            )
        )

        try:
            expires_in = timedelta(days=14)
            expires = datetime.now() + expires_in
            session_cookie = auth.create_session_cookie(token, expires_in, firebase_app)
            response.set_cookie(
                "cp_session",
                session_cookie,
                expires=expires,
                httponly=True,
                secure=request.url.startswith("https"),
                path="/",
            )
            return response
        except Exception as e:
            logger.info(f"Failed to create session cookie: {e}")
            await flash(gettext("User token is not valid"), "danger")
            return request.redirect(url_for("auth.login", token_error=1))

    return request.redirect(url_for("auth.login"))


@blueprint.endpoint("/firebase_credentials", auth=False)
async def get_id_token_from_session(args, params, request: Request):
    cookie_header = request.get_header("Cookie")
    cookies = parse_cookie(cookie_header)
    session_cookie = cookies.get("cp_session")
    if not session_cookie:
        return {"error": "No session found"}, 401

    try:
        decoded_claims = auth.verify_session_cookie(
            session_cookie, check_revoked=True, app=firebase_app
        )
        uid = decoded_claims["uid"]
        email = decoded_claims["email"]
        custom_token = auth.create_custom_token(uid, app=firebase_app)
        return {"email": email, "token": custom_token.decode("utf-8")}, 200
    except Exception as e:
        logger.error(f"Failed to verify session or create custom token: {e}")
        return {"error": "Invalid session"}, 401


def init_app(app):
    get_current_async_app().wsgi.register_endpoint(blueprint)
