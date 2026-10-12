import xmlrpc.client
import json
import os
from datetime import datetime, timezone

URL = os.environ["ODOO_URL"]
DB = os.environ["ODOO_DB"]
USERNAME = os.environ["ODOO_USER"]
API_KEY = os.environ["ODOO_API_KEY"]

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, API_KEY, {})
if not uid:
    raise SystemExit("Authentification échouée — vérifie ODOO_DB, ODOO_USER, ODOO_API_KEY")

models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

# Tous les champs utiles d'une fiche prospect/opportunité
LEAD_FIELDS = [
    "name", "partner_name", "contact_name",
    "email_from", "phone", "mobile",
    "stage_id", "probability", "expected_revenue",
    "description",            # le champ "Notes" visible sur la fiche
    "tag_ids", "user_id",      # vendeur assigné
    "create_date", "write_date",
]

leads = models.execute_kw(
    DB, uid, API_KEY,
    "crm.lead", "search_read",
    [[]],
    {"fields": LEAD_FIELDS, "limit": 500}
)

# Pour chaque fiche, on va chercher son chatter (mail.message)
# Le chatter Odoo = tous les messages/notes liés à ce lead précis
lead_ids = [l["id"] for l in leads]

chatter_by_lead = {lid: [] for lid in lead_ids}

if lead_ids:
    messages = models.execute_kw(
        DB, uid, API_KEY,
        "mail.message", "search_read",
        [[["model", "=", "crm.lead"], ["res_id", "in", lead_ids]]],
        {
            "fields": ["res_id", "body", "author_id", "date", "message_type", "subtype_id"],
            "order": "date asc",
            "limit": 2000,
        }
    )
    for m in messages:
        chatter_by_lead.setdefault(m["res_id"], []).append({
            "date": m["date"],
            "author": m["author_id"][1] if m["author_id"] else None,
            "type": m["message_type"],
            # body est en HTML brut Odoo, on le garde tel quel (du texte simple la plupart du temps)
            "body": m["body"],
        })

for lead in leads:
    lead["chatter"] = chatter_by_lead.get(lead["id"], [])

snapshot = {
    "synced_at": datetime.now(timezone.utc).isoformat(),
    "count": len(leads),
    "leads": leads,
}

os.makedirs("data", exist_ok=True)
with open("data/pipeline.json", "w", encoding="utf-8") as f:
    json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)

print(f"Synced {len(leads)} leads (with chatter) at {snapshot['synced_at']}")
