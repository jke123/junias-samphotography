# 📷 Portfolio Photographe — Déploiement Vercel

## 🗂️ Structure

```
portfolio/
├── app.py                 ← Application Flask
├── models.py               ← Modèles base de données
├── config.py                ← Configuration (psycopg3 + NullPool pour serverless)
├── vercel.json               ← Config déploiement Vercel
├── requirements.txt
├── .env.example
├── static/{css,js,uploads/}
└── templates/{public,admin}/
```

---

## ⚠️ Pourquoi Vercel est différent de Render

Vercel fonctionne en **serverless** — chaque requête peut être traitée par une nouvelle instance.
Conséquences gérées dans ce projet :

- **Base de données** : NullPool activé (pas de connexions persistantes) — fonctionne avec n'importe quelle base PostgreSQL externe (Neon, Supabase, Render, ElephantSQL...)
- **Upload photos** : se fait **directement depuis le navigateur vers ImgBB** (upload client-side), pas via le serveur — évite les limites de taille de requête Vercel (4.5 Mo)
- **Fichiers statiques uploadés** : aucun stockage local possible sur Vercel — tout passe par ImgBB

---

## 🚀 Déploiement pas à pas

### 1. Créer une base de données PostgreSQL gratuite

Recommandé : **[Neon.tech](https://neon.tech)** (gratuit, ne expire jamais contrairement à Render)

- Crée un compte → New Project
- Copie la **Connection String** (commence par `postgresql://`)

### 2. Créer un compte ImgBB (si pas déjà fait)

- **[imgbb.com](https://imgbb.com)** → Sign up
- **[api.imgbb.com](https://api.imgbb.com)** → Get API key

### 3. Déployer sur Vercel

**Option A — via GitHub (recommandé) :**
1. Pousse ce dossier sur un repo GitHub
2. Va sur **[vercel.com](https://vercel.com)** → New Project → Import ton repo
3. Vercel détecte automatiquement `vercel.json`

**Option B — via CLI :**
```bash
npm i -g vercel
cd portfolio
vercel
```

### 4. Variables d'environnement sur Vercel

Dans **Project Settings → Environment Variables**, ajoute :

| Variable | Valeur |
|---|---|
| `SECRET_KEY` | une chaîne aléatoire longue |
| `DATABASE_URL` | ta connection string Neon/PostgreSQL |
| `IMGBB_API_KEY` | ta clé ImgBB |
| `ADMIN_USERNAME` | admin |
| `ADMIN_PASSWORD` | ton mot de passe choisi |

### 5. Redéployer

Après ajout des variables → **Deployments → Redeploy**

---

## 🔐 Connexion admin

`https://ton-site.vercel.app/admin/login`

---

## ✨ Nouveautés de cette version

- **Galerie style téléphone natif** : swipe fluide avec momentum, pinch-to-zoom, double-tap zoom, thumbnails, navigation clavier
- **Upload direct navigateur → ImgBB** : plus rapide, pas de limite serveur
- **Page 404 personnalisée**
- **Année de copyright automatique**
- **Bouton WhatsApp flottant** (si configuré)
- **Bouton retour en haut**
