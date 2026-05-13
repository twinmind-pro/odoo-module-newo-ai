import hashlib
import hmac
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class NewoWebhookController(http.Controller):
    @http.route(
        "/newo/webhook/conversation",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def conversation_webhook(self, **_kwargs):
        raw_body = request.httprequest.get_data()
        signature = request.httprequest.headers.get("X-Newo-Signature", "")
        secret = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("newo_ai_receptionist.webhook_secret", "")
        )
        if not secret or not self._verify_signature(raw_body, signature, secret):
            _logger.warning("Newo webhook rejected — invalid HMAC signature")
            return request.make_response("invalid signature", status=401)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return request.make_response("invalid payload", status=400)
        request.env["newo.conversation"].sudo().ingest_payload(payload)
        return request.make_response("ok", status=200)

    @staticmethod
    def _verify_signature(body: bytes, provided: str, secret: str) -> bool:
        expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, provided)
