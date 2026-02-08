#!/bin/bash
# Sincroniza la rama Dev con la rama Dev del repo de Sergio (upstream).
# Ejecutar desde la raíz del proyecto: ./scripts/git/sync-con-sergio.sh
# Ver: docs/SETUP_MI_REPO.md
set -e
echo "→ Fetching upstream (Sergio)..."
git fetch upstream
echo "→ Merging upstream/Dev into Dev..."
git checkout Dev
git merge upstream/Dev
echo "→ Pushing to origin (tu repo)..."
git push origin Dev
echo "✓ Listo. Tu Dev está sincronizada con la Dev de Sergio."
