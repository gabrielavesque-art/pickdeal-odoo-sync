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

LEAD_FIELDS = [
    "name", "partner_name", "contact_name",
    "email_from", "phone",
    "stage_id", "probability", "expected_revenue",
    "description",
    "tag_ids", "user_id",
    "create_date", "write_date",
]

leads = models.execute_kw(
    DB, uid, API_KEY,
    "crm.lead", "search_read",
    [[]],
    {"fields": LEAD_FIELDS, "limit": 500}
)

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
            "body": m["body"],
        })

# Activités planifiées (rdv, appels...) avec échéance exacte
activities_by_lead = {lid: [] for lid in lead_ids}

if lead_ids:
    activities = models.execute_kw(
        DB, uid, API_KEY,
        "mail.activity", "search_read",
        [[["res_model", "=", "crm.lead"], ["res_id", "in", lead_ids]]],
        {
            "fields": [
                "res_id", "summary", "note",
                "activity_type_id", "date_deadline",
                "create_date", "user_id",
            ],
            "order": "date_deadline asc",
            "limit": 500,
        }
    )
    for a in activities:
        activities_by_lead.setdefault(a["res_id"], []).append({
            "summary": a.get("summary"),
            "note": a.get("note"),
            "type": a["activity_type_id"][1] if a.get("activity_type_id") else None,
            "date_deadline": a.get("date_deadline"),
            "created": a.get("create_date"),
            "assigned_to": a["user_id"][1] if a.get("user_id") else None,
        })

for lead in leads:
    lead["chatter"] = chatter_by_lead.get(lead["id"], [])
    lead["activities"] = activities_by_lead.get(lead["id"], [])

snapshot = {
    "synced_at": datetime.now(timezone.utc).isoformat(),
    "count": len(leads),
    "leads": leads,
}

os.makedirs("data", exist_ok=True)
with open("data/pipeline.json", "w", encoding="utf-8") as f:
    json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)

print(f"Synced {len(leads)} leads (with chatter + activities) at {snapshot['synced_at']}")
