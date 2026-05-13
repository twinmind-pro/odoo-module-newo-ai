import logging
import re
import secrets
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

SAAS_HOST_PATTERN = re.compile(r"\.odoo\.com(?:[/:]|$)")

_logger = logging.getLogger(__name__)

INTEGRATION_USER_LOGIN = "newo-integration"
INTEGRATION_USER_NAME = "Newo AI Integration"
API_KEY_NAME = "Newo AI Receptionist"

# Newo SaaS-side destinations.
# VibeCreator is the agent provisioning UI for first-time setup.
# Portal is for managing existing agents and integrations afterwards.
# Deep-link with prefilled credentials is not yet specified; for now both
# links go to the standalone landing pages and the user pastes the values
# from the credentials wizard.
AGENT_CREATOR_URL = "https://vibecreator.newo.ai/"
NEWO_PORTAL_URL = "https://portal.newo.ai/"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    newo_data_consent = fields.Boolean(
        string="Share data with Newo",
        config_parameter="newo_ai_receptionist.data_consent",
        help=(
            "Required before any data is exchanged with Newo. The integration "
            "may read and write contacts, calendar events, and leads using the "
            "credentials generated below."
        ),
    )
    newo_database_name = fields.Char(
        string="Database",
        compute="_compute_newo_runtime",
        readonly=True,
    )
    newo_base_url = fields.Char(
        string="Base URL",
        compute="_compute_newo_runtime",
        readonly=True,
    )
    newo_integration_user_login = fields.Char(
        string="Integration User",
        compute="_compute_newo_runtime",
        readonly=True,
    )
    newo_integration_state = fields.Selection(
        selection=[
            ("not_provisioned", "Not provisioned"),
            ("active", "Active"),
            ("archived", "Archived"),
        ],
        compute="_compute_newo_runtime",
        readonly=True,
        string="Integration State",
    )
    newo_last_provisioned_at = fields.Datetime(
        string="Last Provisioned",
        compute="_compute_newo_runtime",
        readonly=True,
    )
    newo_is_saas = fields.Boolean(
        string="Odoo Online (SaaS)",
        compute="_compute_newo_runtime",
        readonly=True,
    )
    newo_company_tz = fields.Char(
        string="Business Timezone",
        compute="_compute_newo_runtime",
        readonly=True,
    )

    @api.depends_context("uid")
    def _compute_newo_runtime(self):
        params = self.env["ir.config_parameter"].sudo()
        base_url = params.get_param("web.base.url", "")
        last_provisioned = params.get_param("newo_ai_receptionist.last_provisioned_at")
        user = self._get_integration_user()
        if not user:
            state = "not_provisioned"
        elif user.active:
            state = "active"
        else:
            state = "archived"
        is_saas = bool(SAAS_HOST_PATTERN.search(base_url or ""))
        company_tz = self._get_company_tz()
        for record in self:
            record.newo_database_name = self.env.cr.dbname
            record.newo_base_url = base_url
            record.newo_integration_user_login = user.login if user else False
            record.newo_integration_state = state
            record.newo_last_provisioned_at = last_provisioned or False
            record.newo_is_saas = is_saas
            record.newo_company_tz = company_tz

    def _get_company_tz(self):
        calendar = self.env.company.resource_calendar_id
        return (calendar.tz if calendar else None) or "UTC"

    def _get_integration_user(self):
        return (
            self.env["res.users"]
            .sudo()
            .with_context(active_test=False)
            .search([("login", "=", INTEGRATION_USER_LOGIN)], limit=1)
        )

    def _ensure_integration_user(self):
        user = self._get_integration_user()
        group = self.env.ref("newo_ai_receptionist.group_newo_integration")
        if user:
            if not user.active:
                user.action_unarchive()
            user.sudo().write({"group_ids": [(4, group.id)]})
            return user
        return self.env["res.users"].sudo().create({
            "name": INTEGRATION_USER_NAME,
            "login": INTEGRATION_USER_LOGIN,
            "group_ids": [(6, 0, [group.id])],
        })

    def action_provision_integration(self):
        self.ensure_one()
        if not self.newo_data_consent:
            raise UserError(_("Enable the data sharing consent first."))
        user = self._ensure_integration_user()
        ApiKeys = self.env["res.users.apikeys"].sudo()
        ApiKeys.search([
            ("user_id", "=", user.id),
            ("name", "=", API_KEY_NAME),
        ]).unlink()
        expiration = fields.Datetime.now() + timedelta(days=365)
        plaintext_key = ApiKeys.with_user(user)._generate("rpc", API_KEY_NAME, expiration)
        webhook_secret = secrets.token_urlsafe(32)
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("newo_ai_receptionist.integration_user_id", str(user.id))
        params.set_param("newo_ai_receptionist.webhook_secret", webhook_secret)
        params.set_param(
            "newo_ai_receptionist.last_provisioned_at",
            fields.Datetime.now().isoformat(sep=" "),
        )
        base_url = params.get_param("web.base.url", "")
        wizard = self.env["newo.credentials.wizard"].create({
            "api_key": plaintext_key,
            "webhook_secret": webhook_secret,
            "user_login": user.login,
            "database_name": self.env.cr.dbname,
            "base_url": base_url,
            "company_tz": self._get_company_tz(),
            "is_saas": bool(SAAS_HOST_PATTERN.search(base_url or "")),
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Newo Integration Credentials"),
            "res_model": "newo.credentials.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_revoke_integration(self):
        self.ensure_one()
        user = self._get_integration_user()
        if not user:
            raise UserError(_("No integration user to revoke."))
        self.env["res.users.apikeys"].sudo().search([("user_id", "=", user.id)]).unlink()
        user.action_archive()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Integration revoked"),
                "message": _("API keys deleted and the integration user was archived."),
                "type": "warning",
                "sticky": False,
            },
        }

    def action_open_agent_creator(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": AGENT_CREATOR_URL,
            "target": "new",
        }

    def action_open_newo_portal(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": NEWO_PORTAL_URL,
            "target": "new",
        }
