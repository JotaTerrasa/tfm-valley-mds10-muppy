#!/bin/bash
# Sincroniza tu rama Dev con la rama Dev del repo de Sergio (upstream).
set -e
echo "→ Fetching upstream (Sergio)..."
git fetch upstream
echo "→ Merging upstream/Dev into Dev..."
git checkout Dev
git merge upstream/Dev
echo "→ Pushing to origin (tu repo)..."
git push origin Dev
echo "✓ Listo. Tu Dev está sincronizada con la Dev de Sergio."
