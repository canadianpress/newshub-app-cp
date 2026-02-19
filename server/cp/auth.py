from urllib.parse import urlencode

from flask import Blueprint, redirect, request

blueprint = Blueprint("cp_auth", __name__)


@blueprint.route("/sso-redirect", methods=["GET", "POST"])
def callback():
    code = request.args.get("code")
    tenant_id = request.args.get("tenant_id")
    partner_sso_url = request.args.get("partner_sso_url")

    if code and tenant_id and partner_sso_url:
        params = {"tenant_id": tenant_id, "code": code}

        query_string = urlencode(params)
        target_url = f"{partner_sso_url}?{query_string}"

        return redirect(target_url)


def init_app(app):
    app.register_blueprint(blueprint)
