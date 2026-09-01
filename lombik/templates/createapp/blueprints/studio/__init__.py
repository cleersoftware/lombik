from flask import Blueprint, g, redirect, url_for

from lombik.flash import Flash


studio_bp = Blueprint(
    "studio_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@studio_bp.before_request
def _require_superuser():
    user = getattr(g, "user", None)

    if not user:
        Flash.error("You must log in to visit Studio.")
        return redirect(url_for("auth_bp.login"))

    if user.role != "superuser":
        Flash.error("Studio is only available to superusers.")
        return redirect(url_for("core_bp.home"))
