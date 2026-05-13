from odoo import fields, models


class NewoCredentialsWizard(models.TransientModel):
    """One-time display of newly generated integration credentials.

    The API key is shown to the admin once and never persisted in plaintext.
    """

    _name = "newo.credentials.wizard"
    _description = "Newo Integration Credentials"

    user_login = fields.Char(string="Username (login)", readonly=True)
    api_key = fields.Char(string="API Key", readonly=True)
    database_name = fields.Char(string="Database", readonly=True)
    base_url = fields.Char(string="Base URL", readonly=True)
    company_tz = fields.Char(string="Business Timezone", readonly=True)
    is_saas = fields.Boolean(string="Odoo Online (SaaS)", readonly=True)
