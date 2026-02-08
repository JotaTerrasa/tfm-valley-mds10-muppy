# Traer el repo a tu GitHub (privado) y sincronizar con la base

---

## Sincronización automática con el repo de Sergio

En este repo hay un **GitHub Action** (archivo `.github/workflows/sync-upstream.yml`) que:

- **Cada hora** copia todas las ramas de `ssillerom/tfm-valley-mds10-muppy` a tu repo.
- También puedes lanzarlo **a mano**: en GitHub → pestaña **Actions** → "Sync from Sergio (upstream)" → **Run workflow**.

Así, cuando Sergio suba algo, en menos de una hora (o al instante si lo ejecutas tú) las ramas de tu repo estarán actualizadas.

---

## Sincronizar a mano (rama Dev de Sergio)

Cuando quieras traer a tu máquina los últimos cambios de la rama **Dev** de Sergio:

```bash
git fetch upstream
git checkout Dev
git merge upstream/Dev
git push origin Dev
```

O ejecuta el script desde la raíz del proyecto: `./scripts/git/sync-con-sergio.sh`

---

## Paso 1 – Crear el repo en tu GitHub (tú, en el navegador)

1. Entra en **https://github.com/new**
2. **Repository name:** `tfm-valley-mds10-muppy` (o el que quieras)
3. **Private**
4. **No** marques "Add a README", "Add .gitignore" ni "Choose a license" (dejar vacío)
5. **Create repository**

## Paso 2 – Añadir tu repo como remote y subir el código

En la terminal, desde la raíz del proyecto (donde está este README):

```bash
# Usuario típico: jotaterrasa (minúsculas). Si tu repo tiene otro nombre, cambia la URL.
git remote add jota https://github.com/jotaterrasa/tfm-valley-mds10-muppy.git

# Subir la rama Dev (y main) a tu repo
git push jota Dev
git push jota main
```

## Paso 3 – Dejar tu repo como origin y la base como upstream

```bash
git remote remove origin
git remote rename jota origin
```

Desde ahora:
- **origin** = tu repo (JotaTerrasa/tfm-valley-mds10-muppy), privado
- **upstream** = repo base (ssillerom/tfm-valley-mds10-muppy)

## Sincronizar con la base (cuando Sergio suba cambios)

```bash
git fetch upstream
git checkout Dev
git merge upstream/Dev
git push origin Dev
```

(O si prefieres rebase: `git rebase upstream/Dev` y luego `git push origin Dev`.)

## Resumen de remotos después del setup

| Remote   | Repo                                      |
|----------|-------------------------------------------|
| origin   | Tu repo (JotaTerrasa), privado             |
| upstream | Repo base (ssillerom), para traer cambios  |
