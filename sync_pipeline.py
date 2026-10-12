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

# Récupère les opportunités/projets du pipeline CRM (crm.lead)
fields = ["name", "partner_name", "stage_id", "expected_revenue", "probability",
          "activity_summary", "activity_date_deadline", "write_date", "tag_ids"]

leads = models.execute_kw(
    DB, uid, API_KEY,
    "crm.lead", "search_read",
    [[]],
    {"fields": fields, "limit": 500}
)

snapshot = {
    "synced_at": datetime.now(timezone.utc).isoformat(),
    "count": len(leads),
    "leads": leads,
}

os.makedirs("data", exist_ok=True)
with open("data/pipeline.json", "w", encoding="utf-8") as f:
    json.dump(snapshot, f, ensure_ascii=False, indent=2)

print(f"Synced {len(leads)} leads at {snapshot['synced_at']}")
