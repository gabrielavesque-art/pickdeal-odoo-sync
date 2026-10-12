# Pick&Deal — Sync Odoo Pipeline

Synchronise automatiquement le pipeline CRM Odoo vers `data/pipeline.json`, toutes les heures via GitHub Actions.

## Mise en place (une seule fois)

1. Crée un **repo privé** sur GitHub (ex: `pickdeal-odoo-sync`)
2. Va dans **Settings → Secrets and variables → Actions → New repository secret**, ajoute ces 4 secrets :
   - `ODOO_URL` → ex: `https://pickdeal1.odoo.com`
   - `ODOO_DB` → le nom de ta base (souvent `pickdeal1`)
   - `ODOO_USER` → l'email de connexion à Odoo
   - `ODOO_API_KEY` → la clé API générée dans Odoo (Sécurité → Clés API)
3. Upload tous les fichiers de ce dossier dans le repo (drag & drop via l'interface web GitHub, pas besoin de ligne de commande)
4. Va dans l'onglet **Actions** du repo → le workflow "Sync Odoo Pipeline" doit apparaître → clique "Run workflow" pour tester une première fois manuellement
5. Si ça marche, un fichier `data/pipeline.json` apparaît dans le repo avec ton pipeline à jour

Ensuite, ça tourne tout seul chaque heure, sans que tu touches à rien.
