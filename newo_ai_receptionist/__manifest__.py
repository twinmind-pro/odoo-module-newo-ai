{
    "name": "Newo AI Receptionist",
    "version": "19.0.1.0.0",
    "summary": "Connect Odoo to Newo AI Receptionist — answers calls, books appointments, captures leads",
    "description": """
Newo AI Receptionist Connector
==============================

Provisions a dedicated integration user and API key in Odoo so that the Newo
AI Receptionist platform can read and write your Odoo data:

- Create bookings as ``calendar.event``
- Capture leads as ``crm.lead`` with transcripts and recordings
- Deduplicate contacts against ``res.partner``

After installation, open **Settings → Newo AI Receptionist**, click *Generate
Integration Credentials*, and copy the displayed API key into your Newo
dashboard. A paid Newo subscription is required to run conversations; the
module itself is free.
""",
    "category": "Sales/CRM",
    "author": "TwinMind / Newo.ai",
    "maintainer": "TwinMind",
    "website": "https://newo.ai",
    "support": "support@newo.ai",
    "license": "LGPL-3",
    "price": 0.0,
    "currency": "EUR",
    "depends": [
        "base",
        "calendar",
        "crm",
        "contacts",
    ],
    "data": [
        "security/newo_security.xml",
        "security/ir.model.access.csv",
        "views/newo_credentials_wizard_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "uninstall_hook": "uninstall_hook",
}
