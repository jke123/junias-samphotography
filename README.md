# 📷 Portfolio Photographe — Déploiement Vercel + Cloudinary

## 🗂️ Structure

```
portfolio/
├── app.py
├── models.py
├── config.py
├── vercel.json
├── requirements.txt
├── .env.example
├── static/{css,js,uploads/}
└── templates/{public,admin}/
```

---

## ☁️ Configuration Cloudinary

### 1. Créer un compte
**[cloudinary.com](https://cloudinary.com)** → Sign up gratuit (25 Go gratuits)

### 2. Récupérer les identifiants
Sur le **Dashboard** Cloudinary, en haut, tu trouveras :
- **Cloud name**
- **API Key**
- **API Secret** (cliquer "reveal")

### 3. Créer un "Upload Preset" non signé
Nécessaire pour permettre l'upload direct depuis le navigateur de l'admin (galerie photos) sans exposer ta clé secrète.

1. Dashboard Cloudinary → **Settings** (roue dentée) → **Upload**
2. Descend jusqu'à **Upload presets** → **Add upload preset**
3. **Signing Mode** → choisir **Unsigned**
4. Donne-lui un nom (ex: `portfolio_unsigned`) → **Save**
5. Note ce nom, c'est ton `CLOUDINARY_UPLOAD_PRESET`

---

## 🚀 Variables d'environnement sur Vercel

**Project Settings → Environment Variables** :

| Variable | Valeur | Secret ? |
|---|---|---|
| `SECRET_KEY` | chaîne aléatoire longue | oui |
| `DATABASE_URL` | connection string PostgreSQL (Neon.tech recommandé) | oui |
| `CLOUDINARY_URL` | `cloudinary://API_KEY:API_SECRET@CLOUD_NAME` | oui |
| `CLOUDINARY_CLOUD_NAME` | ton cloud name | non |
| `CLOUDINARY_UPLOAD_PRESET` | nom du preset créé ci-dessus | non |
| `ADMIN_USERNAME` | admin | non |
| `ADMIN_PASSWORD` | ton mot de passe | oui |

Redéploie après ajout des variables.

---

## 🔐 Connexion admin

`https://ton-site.vercel.app/admin/login`

---

## ✨ Fonctionnement des uploads

- **Galerie (photos multiples)** : upload direct navigateur → Cloudinary (upload non signé), contourne la limite de taille Vercel
- **Photo de profil / couverture de projet** : upload signé depuis le serveur (via `CLOUDINARY_URL`)

## 📱 Galerie

Style téléphone natif : swipe avec momentum, pinch-to-zoom, double-tap, thumbnails, navigation clavier.
