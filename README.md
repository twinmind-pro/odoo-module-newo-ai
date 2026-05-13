# Newo AI Receptionist — Odoo Marketplace App

Free Odoo connector that links Odoo to the Newo AI Receptionist SaaS platform.

## Status

**Bootstrap.** Empty module skeleton. Installs on Odoo 19 without errors. No business logic yet.

## Targets

- **Odoo version:** 19.0 (initial listing)
- **License:** LGPL-3
- **Price:** free (`price=0`)
- **Funnel:** paid Newo SaaS subscription at https://newo.ai
- **Marketplace:** https://apps.odoo.com

## Layout

```
marketplaces/odoo/
├── newo_ai_receptionist/    # the Odoo module (this is what gets zipped for submission)
│   ├── __manifest__.py
│   ├── __init__.py
│   ├── models/              # Python models (empty)
│   ├── views/               # XML views (empty)
│   ├── controllers/         # webhook receivers from Newo (empty)
│   ├── data/                # automation rules, seed records (empty)
│   ├── security/            # access rights (empty)
│   ├── doc/index.rst        # marketplace documentation
│   └── static/description/  # icon + listing landing page
├── docker-compose.yml       # local Odoo 19 + Postgres for development
├── tests/                   # Python tests
├── scripts/                 # build / package / lint helpers
├── submission/              # marketplace assets (not bundled in zip)
└── .gitignore
```

## Local development

```bash
cd marketplaces/odoo/
docker compose up

# Open http://localhost:8069
# Create a database and install "Newo AI Receptionist" from Apps menu
```

The module is mounted read-only into the Odoo container at `/mnt/extra-addons/`. Edit files in this repo, restart the container, reinstall.

## Marketplace constraints (must follow)

- **No activation key at install.** Module must install cleanly on an empty database; the Newo subscription gate triggers only when the user invokes Newo features.
- **No vendor lock-in.** No remote code download, no license keys, no calls home before user opt-in.
- **HMAC-sign all inbound webhooks** from Newo (Odoo `base_automation` ships unsigned by default).
- **GDPR disclosure.** Settings page must enumerate every data field sent to Newo and require explicit opt-in.
- **Uninstall hook.** Drop API key, automation rules, integration user, and crons; notify Newo.
- **External CTA links** in the listing description page are stripped — `newo.ai` CTA must live inside the installed module's settings page.

## Submission

See `submission/` for listing description, screenshots, and the submission checklist. Submission flow:

1. Run `scripts/package.sh` → produces a clean zip from `newo_ai_receptionist/`.
2. Upload at https://apps.odoo.com/apps/upload, version `19.0`, license `LGPL-3`.
3. Provide a public Git repo URL (read-only access for Odoo reviewers).
4. Wait for review (no published SLA, typical: days to ~2 weeks).
