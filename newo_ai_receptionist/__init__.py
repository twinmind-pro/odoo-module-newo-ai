from . import controllers, models


def uninstall_hook(env):
    """Cleanup integration user, API keys, and config parameters on uninstall."""
    params = env["ir.config_parameter"].sudo()
    for key in (
        "newo_ai_receptionist.integration_user_id",
        "newo_ai_receptionist.last_provisioned_at",
        "newo_ai_receptionist.data_consent",
        "newo_ai_receptionist.agent_external_id",
        "newo_ai_receptionist.webhook_secret",
    ):
        params.search([("key", "=", key)]).unlink()

    user = env["res.users"].sudo().search([("login", "=", "newo-integration")], limit=1)
    if user:
        env["res.users.apikeys"].sudo().search([("user_id", "=", user.id)]).unlink()
        user.action_archive()
