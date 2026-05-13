import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class NewoConversation(models.Model):
    _name = "newo.conversation"
    _description = "Newo Conversation"
    _order = "started_at desc"
    _rec_name = "external_id"

    external_id = fields.Char(
        string="Newo Conversation ID",
        required=True,
        index=True,
        copy=False,
    )
    started_at = fields.Datetime(string="Started At", required=True)
    ended_at = fields.Datetime(string="Ended At")
    channel = fields.Selection(
        selection=[
            ("phone", "Phone"),
            ("sms", "SMS"),
            ("whatsapp", "WhatsApp"),
            ("telegram", "Telegram"),
            ("chat", "Web Chat"),
        ],
        string="Channel",
    )
    intent = fields.Selection(
        selection=[
            ("lead", "Lead Capture"),
            ("booking", "Booking"),
            ("info", "Information Request"),
            ("other", "Other"),
        ],
        string="Detected Intent",
    )
    partner_id = fields.Many2one("res.partner", string="Contact", index=True)
    lead_id = fields.Many2one("crm.lead", string="Lead", index=True)
    transcript = fields.Text(string="Transcript")
    recording_url = fields.Char(string="Recording URL")
    summary = fields.Text(string="Summary")

    _external_id_unique = models.Constraint(
        "unique(external_id)",
        "A conversation with this Newo ID already exists.",
    )

    @api.model
    def ingest_payload(self, payload):
        """Idempotently upsert a conversation from a Newo webhook payload."""
        external_id = payload.get("conversation_id")
        if not external_id:
            _logger.warning("Newo webhook payload missing conversation_id")
            return self.browse()
        partner = self._find_or_create_partner(payload.get("contact") or {})
        vals = {
            "external_id": external_id,
            "started_at": payload.get("started_at"),
            "ended_at": payload.get("ended_at"),
            "channel": payload.get("channel"),
            "intent": payload.get("intent"),
            "transcript": payload.get("transcript"),
            "recording_url": payload.get("recording_url"),
            "summary": payload.get("summary"),
            "partner_id": partner.id if partner else False,
        }
        existing = self.search([("external_id", "=", external_id)], limit=1)
        if existing:
            existing.write(vals)
            conversation = existing
        else:
            conversation = self.create(vals)
        if payload.get("intent") == "lead" and not conversation.lead_id:
            conversation.lead_id = conversation._create_lead(payload).id
        return conversation

    @api.model
    def _find_or_create_partner(self, contact):
        phone = contact.get("phone")
        email = contact.get("email")
        if not phone and not email:
            return self.env["res.partner"].browse()
        domain = []
        if phone and email:
            domain = ["|", ("phone", "=", phone), ("email", "=", email)]
        elif phone:
            domain = [("phone", "=", phone)]
        else:
            domain = [("email", "=", email)]
        partner = self.env["res.partner"].search(domain, limit=1)
        if partner:
            return partner
        return self.env["res.partner"].create({
            "name": contact.get("name") or phone or email,
            "phone": phone,
            "email": email,
        })

    def _create_lead(self, payload):
        contact = payload.get("contact") or {}
        return self.env["crm.lead"].create({
            "name": payload.get("summary") or f"Newo lead — {payload.get('conversation_id')}",
            "description": payload.get("transcript"),
            "partner_id": self.partner_id.id or False,
            "phone": contact.get("phone"),
            "email_from": contact.get("email"),
            "type": "lead",
        })
