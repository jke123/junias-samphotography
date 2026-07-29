import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Admin, SiteConfig, Experience, Formation, Project, Photo, ContactInfo, Message
import cloudinary
import cloudinary.uploader

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"
login_manager.login_message = "Veuillez vous connecter."
login_manager.login_message_category = "warning"

# ── Cloudinary ──
# CLOUDINARY_URL (secret, format cloudinary://key:secret@cloud_name) sert aux
# uploads signés faits depuis le serveur (profil, couverture de projet).
# CLOUDINARY_CLOUD_NAME + CLOUDINARY_UPLOAD_PRESET (non secrets) servent aux
# uploads directs depuis le navigateur (galerie) pour contourner la limite
# de taille de requête de Vercel.
CLOUDINARY_URL           = os.getenv("CLOUDINARY_URL", "")
CLOUDINARY_CLOUD_NAME    = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET", "")

if CLOUDINARY_URL:
    cloudinary.config(cloudinary_url=CLOUDINARY_URL, secure=True)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def upload_to_cloudinary(file_bytes, name="photo"):
    """Upload signé (côté serveur) vers Cloudinary, retourne l'URL ou None."""
    if not CLOUDINARY_URL:
        return None
    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            folder="portfolio",
            public_id=f"{name}_{uuid.uuid4().hex[:8]}",
            resource_type="image",
        )
        return result.get("secure_url")
    except Exception as e:
        app.logger.error(f"Cloudinary error: {e}")
        return None


def save_image(file, folder=None, name="photo"):
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    file.seek(0)
    img_bytes = file.read()
    url = upload_to_cloudinary(img_bytes, name)
    if url:
        return url
    # Fallback local (utile seulement en développement, pas persistant sur Vercel)
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, filename), "wb") as f:
        f.write(img_bytes)
    return filename


def get_config(key, default=""):
    row = SiteConfig.query.filter_by(key=key).first()
    return row.value if row else default


def set_config(key, value):
    row = SiteConfig.query.filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.session.add(SiteConfig(key=key, value=value))
    db.session.commit()


def get_all_config():
    return {r.key: r.value for r in SiteConfig.query.all()}


def unread_count():
    return Message.query.filter_by(is_read=False).count()


# ─────────────────────────────────────────────
#  PUBLIC ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    cfg      = get_all_config()
    projects = Project.query.filter_by(visible=True).order_by(Project.order).limit(6).all()
    experiences = Experience.query.filter_by(visible=True).order_by(Experience.order).all()
    formations  = Formation.query.filter_by(visible=True).order_by(Formation.order).all()
    contacts    = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order).all()
    return render_template("public/index.html", cfg=cfg, projects=projects,
                           experiences=experiences, formations=formations, contacts=contacts)


@app.route("/gallery")
def gallery():
    cfg      = get_all_config()
    category = request.args.get("cat", "all")
    q = Photo.query.filter_by(visible=True)
    if category != "all":
        q = q.filter_by(category=category)
    photos = q.order_by(Photo.order, Photo.created_at.desc()).all()
    cats   = [c[0] for c in db.session.query(Photo.category).filter_by(visible=True).distinct().all()]
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order).all()
    return render_template("public/gallery.html", cfg=cfg, photos=photos,
                           categories=cats, current_cat=category, contacts=contacts)


@app.route("/projects")
def projects():
    cfg      = get_all_config()
    all_proj = Project.query.filter_by(visible=True).order_by(Project.order).all()
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order).all()
    return render_template("public/projects.html", cfg=cfg, projects=all_proj, contacts=contacts)


@app.route("/project/<int:pid>")
def project_detail(pid):
    cfg     = get_all_config()
    project = Project.query.get_or_404(pid)
    if not project.visible:
        return redirect(url_for("projects"))
    photos  = Photo.query.filter_by(project_id=pid, visible=True).order_by(Photo.order).all()
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order).all()
    return render_template("public/project_detail.html", cfg=cfg, project=project,
                           photos=photos, contacts=contacts)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    cfg      = get_all_config()
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order).all()
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        phone   = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip()
        body    = request.form.get("body", "").strip()
        if not name or not body:
            flash("Le nom et le message sont obligatoires.", "danger")
        else:
            db.session.add(Message(name=name, email=email, phone=phone,
                                   subject=subject, body=body))
            db.session.commit()
            flash("Message envoyé avec succès. Merci !", "success")
            return redirect(url_for("contact"))
    return render_template("public/contact.html", cfg=cfg, contacts=contacts)


# ─────────────────────────────────────────────
#  ADMIN AUTH
# ─────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        admin = Admin.query.filter_by(username=request.form.get("username","").strip()).first()
        if admin and admin.check_password(request.form.get("password","")):
            login_user(admin)
            return redirect(url_for("admin_dashboard"))
        flash("Identifiants incorrects.", "danger")
    return render_template("admin/login.html")


@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("admin_login"))


# ─────────────────────────────────────────────
#  ADMIN DASHBOARD
# ─────────────────────────────────────────────

@app.route("/admin/")
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    stats = {
        "photos": Photo.query.count(),
        "projects": Project.query.count(),
        "messages": Message.query.count(),
        "unread": unread_count(),
        "experiences": Experience.query.count(),
        "formations": Formation.query.count(),
    }
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats,
                           recent_messages=recent_messages, unread=unread_count())


# ─────────────────────────────────────────────
#  API — Config Cloudinary pour upload direct navigateur
# ─────────────────────────────────────────────

@app.route("/api/upload-key")
@login_required
def get_upload_key():
    """Retourne le cloud_name + upload_preset (non secrets) pour permettre
    à l'admin d'uploader des photos directement depuis le navigateur vers
    Cloudinary (upload non signé), sans passer par notre serveur — ce qui
    contourne la limite de taille de requête de Vercel."""
    if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_UPLOAD_PRESET:
        return jsonify({"error": "Cloudinary non configuré (CLOUDINARY_CLOUD_NAME / CLOUDINARY_UPLOAD_PRESET manquants)"}), 500
    return jsonify({
        "cloud_name": CLOUDINARY_CLOUD_NAME,
        "upload_preset": CLOUDINARY_UPLOAD_PRESET,
    })



@app.route("/admin/gallery/save-urls", methods=["POST"])
@login_required
def admin_photo_save_urls():
    """Reçoit les URLs ImgBB uploadées côté client et les sauvegarde en base."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400
    urls        = data.get("urls", [])
    category    = data.get("category", "autre")
    title       = data.get("title", "")
    description = data.get("description", "")
    project_id  = data.get("project_id") or None
    count = 0
    for url in urls:
        if url and url.startswith("http"):
            db.session.add(Photo(filename=url, title=title,
                                 description=description, category=category,
                                 project_id=project_id))
            count += 1
    if count:
        db.session.commit()
    return jsonify({"success": True, "count": count})


# ─────────────────────────────────────────────
#  ADMIN — PROFIL
# ─────────────────────────────────────────────

@app.route("/admin/profile", methods=["GET", "POST"])
@login_required
def admin_profile():
    if request.method == "POST":
        for f in ["photographer_name","structure_name","years_experience",
                  "about_short","about_full","specialties"]:
            set_config(f, request.form.get(f, ""))
        pf = request.files.get("profile_photo")
        if pf and pf.filename:
            url = save_image(pf, app.config["PROFILE_FOLDER"], "profil")
            if url:
                set_config("profile_photo", url)
        flash("Profil mis à jour.", "success")
        return redirect(url_for("admin_profile"))
    return render_template("admin/profile.html", cfg=get_all_config(), unread=unread_count())


# ─────────────────────────────────────────────
#  ADMIN — EXPERIENCES
# ─────────────────────────────────────────────

@app.route("/admin/experiences")
@login_required
def admin_experiences():
    return render_template("admin/experiences.html",
                           experiences=Experience.query.order_by(Experience.order).all(),
                           unread=unread_count())


@app.route("/admin/experiences/add", methods=["POST"])
@login_required
def admin_exp_add():
    db.session.add(Experience(
        title=request.form.get("title",""),
        company=request.form.get("company",""),
        description=request.form.get("description",""),
        year_start=request.form.get("year_start",""),
        year_end=request.form.get("year_end",""),
        order=int(request.form.get("order",0)),
        visible=bool(request.form.get("visible"))
    ))
    db.session.commit()
    flash("Expérience ajoutée.", "success")
    return redirect(url_for("admin_experiences"))


@app.route("/admin/experiences/edit/<int:eid>", methods=["POST"])
@login_required
def admin_exp_edit(eid):
    exp = Experience.query.get_or_404(eid)
    exp.title=request.form.get("title",exp.title)
    exp.company=request.form.get("company",exp.company)
    exp.description=request.form.get("description",exp.description)
    exp.year_start=request.form.get("year_start",exp.year_start)
    exp.year_end=request.form.get("year_end",exp.year_end)
    exp.order=int(request.form.get("order",exp.order))
    exp.visible=bool(request.form.get("visible"))
    db.session.commit()
    flash("Expérience mise à jour.", "success")
    return redirect(url_for("admin_experiences"))


@app.route("/admin/experiences/delete/<int:eid>")
@login_required
def admin_exp_delete(eid):
    db.session.delete(Experience.query.get_or_404(eid))
    db.session.commit()
    flash("Supprimé.", "success")
    return redirect(url_for("admin_experiences"))


# ─────────────────────────────────────────────
#  ADMIN — FORMATIONS
# ─────────────────────────────────────────────

@app.route("/admin/formations")
@login_required
def admin_formations():
    return render_template("admin/formations.html",
                           formations=Formation.query.order_by(Formation.order).all(),
                           unread=unread_count())


@app.route("/admin/formations/add", methods=["POST"])
@login_required
def admin_form_add():
    db.session.add(Formation(
        title=request.form.get("title",""),
        institution=request.form.get("institution",""),
        year=request.form.get("year",""),
        description=request.form.get("description",""),
        order=int(request.form.get("order",0)),
        visible=bool(request.form.get("visible"))
    ))
    db.session.commit()
    flash("Formation ajoutée.", "success")
    return redirect(url_for("admin_formations"))


@app.route("/admin/formations/edit/<int:fid>", methods=["POST"])
@login_required
def admin_form_edit(fid):
    f = Formation.query.get_or_404(fid)
    f.title=request.form.get("title",f.title)
    f.institution=request.form.get("institution",f.institution)
    f.year=request.form.get("year",f.year)
    f.description=request.form.get("description",f.description)
    f.order=int(request.form.get("order",f.order))
    f.visible=bool(request.form.get("visible"))
    db.session.commit()
    flash("Mise à jour.", "success")
    return redirect(url_for("admin_formations"))


@app.route("/admin/formations/delete/<int:fid>")
@login_required
def admin_form_delete(fid):
    db.session.delete(Formation.query.get_or_404(fid))
    db.session.commit()
    flash("Supprimé.", "success")
    return redirect(url_for("admin_formations"))


# ─────────────────────────────────────────────
#  ADMIN — GALERIE
# ─────────────────────────────────────────────

CATEGORIES = [
    ("shoot","Séance Photo"), ("mariage","Mariage"),
    ("enterrement","Enterrement"), ("evenement","Événement"),
    ("portrait","Portrait"), ("autre","Autre"),
]


@app.route("/admin/gallery")
@login_required
def admin_gallery():
    photos = Photo.query.order_by(Photo.created_at.desc()).all()
    return render_template("admin/gallery.html", photos=photos,
                           categories=CATEGORIES, unread=unread_count())


@app.route("/admin/gallery/add", methods=["POST"])
@login_required
def admin_photo_add():
    """Fallback upload serveur (si JS désactivé)."""
    files    = request.files.getlist("photos")
    category = request.form.get("category","autre")
    title    = request.form.get("title","")
    desc     = request.form.get("description","")
    pid      = request.form.get("project_id") or None
    count = 0
    for f in files:
        if f and f.filename:
            url = save_image(f, app.config["PHOTOS_FOLDER"])
            if url:
                db.session.add(Photo(filename=url, title=title,
                                     description=desc, category=category,
                                     project_id=pid))
                count += 1
    db.session.commit()
    flash(f"{count} photo(s) ajoutée(s).", "success")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/gallery/delete/<int:pid>")
@login_required
def admin_photo_delete(pid):
    db.session.delete(Photo.query.get_or_404(pid))
    db.session.commit()
    flash("Photo supprimée.", "success")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/gallery/toggle/<int:pid>")
@login_required
def admin_photo_toggle(pid):
    photo = Photo.query.get_or_404(pid)
    photo.visible = not photo.visible
    db.session.commit()
    return redirect(url_for("admin_gallery"))


# ─────────────────────────────────────────────
#  ADMIN — PROJETS
# ─────────────────────────────────────────────

@app.route("/admin/projects")
@login_required
def admin_projects():
    return render_template("admin/projects.html",
                           projects=Project.query.order_by(Project.order).all(),
                           categories=CATEGORIES, unread=unread_count())


@app.route("/admin/projects/add", methods=["POST"])
@login_required
def admin_project_add():
    cover = ""
    cf = request.files.get("cover_photo")
    if cf and cf.filename:
        cover = save_image(cf, app.config["PHOTOS_FOLDER"]) or ""
    db.session.add(Project(
        title=request.form.get("title",""),
        description=request.form.get("description",""),
        category=request.form.get("category","autre"),
        cover_photo=cover,
        date=request.form.get("date",""),
        order=int(request.form.get("order",0)),
        visible=bool(request.form.get("visible"))
    ))
    db.session.commit()
    flash("Projet ajouté.", "success")
    return redirect(url_for("admin_projects"))


@app.route("/admin/projects/edit/<int:pid>", methods=["POST"])
@login_required
def admin_project_edit(pid):
    p = Project.query.get_or_404(pid)
    p.title=request.form.get("title",p.title)
    p.description=request.form.get("description",p.description)
    p.category=request.form.get("category",p.category)
    p.date=request.form.get("date",p.date)
    p.order=int(request.form.get("order",p.order))
    p.visible=bool(request.form.get("visible"))
    cf = request.files.get("cover_photo")
    if cf and cf.filename:
        url = save_image(cf, app.config["PHOTOS_FOLDER"])
        if url: p.cover_photo = url
    db.session.commit()
    flash("Projet mis à jour.", "success")
    return redirect(url_for("admin_projects"))


@app.route("/admin/projects/delete/<int:pid>")
@login_required
def admin_project_delete(pid):
    db.session.delete(Project.query.get_or_404(pid))
    db.session.commit()
    flash("Projet supprimé.", "success")
    return redirect(url_for("admin_projects"))


# ─────────────────────────────────────────────
#  ADMIN — CONTACTS
# ─────────────────────────────────────────────

CONTACT_TYPES = [
    ("whatsapp","WhatsApp","fab fa-whatsapp"),
    ("phone","Téléphone","fas fa-phone"),
    ("email","Email","fas fa-envelope"),
    ("instagram","Instagram","fab fa-instagram"),
    ("facebook","Facebook","fab fa-facebook"),
    ("tiktok","TikTok","fab fa-tiktok"),
    ("youtube","YouTube","fab fa-youtube"),
    ("autre","Autre","fas fa-link"),
]


@app.route("/admin/contact-info")
@login_required
def admin_contact_info():
    return render_template("admin/contact_info.html",
                           contacts=ContactInfo.query.order_by(ContactInfo.order).all(),
                           contact_types=CONTACT_TYPES, unread=unread_count())


@app.route("/admin/contact-info/add", methods=["POST"])
@login_required
def admin_contact_add():
    ctype = request.form.get("type","autre")
    icon  = next((t[2] for t in CONTACT_TYPES if t[0]==ctype), "fas fa-link")
    db.session.add(ContactInfo(
        type=ctype, label=request.form.get("label",""),
        value=request.form.get("value",""), icon=icon,
        order=int(request.form.get("order",0)),
        visible=bool(request.form.get("visible"))
    ))
    db.session.commit()
    flash("Contact ajouté.", "success")
    return redirect(url_for("admin_contact_info"))


@app.route("/admin/contact-info/edit/<int:cid>", methods=["POST"])
@login_required
def admin_contact_edit(cid):
    ci = ContactInfo.query.get_or_404(cid)
    ci.type=request.form.get("type",ci.type)
    ci.label=request.form.get("label",ci.label)
    ci.value=request.form.get("value",ci.value)
    ci.icon=next((t[2] for t in CONTACT_TYPES if t[0]==ci.type),"fas fa-link")
    ci.order=int(request.form.get("order",ci.order))
    ci.visible=bool(request.form.get("visible"))
    db.session.commit()
    flash("Mis à jour.", "success")
    return redirect(url_for("admin_contact_info"))


@app.route("/admin/contact-info/delete/<int:cid>")
@login_required
def admin_contact_delete(cid):
    db.session.delete(ContactInfo.query.get_or_404(cid))
    db.session.commit()
    flash("Supprimé.", "success")
    return redirect(url_for("admin_contact_info"))


# ─────────────────────────────────────────────
#  ADMIN — MESSAGES
# ─────────────────────────────────────────────

@app.route("/admin/messages")
@login_required
def admin_messages():
    return render_template("admin/messages.html",
                           messages=Message.query.order_by(Message.created_at.desc()).all(),
                           unread=unread_count())


@app.route("/admin/messages/read/<int:mid>")
@login_required
def admin_message_read(mid):
    msg = Message.query.get_or_404(mid)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages/delete/<int:mid>")
@login_required
def admin_message_delete(mid):
    db.session.delete(Message.query.get_or_404(mid))
    db.session.commit()
    flash("Message supprimé.", "success")
    return redirect(url_for("admin_messages"))


@app.route("/admin/change-password", methods=["POST"])
@login_required
def admin_change_password():
    old = request.form.get("old_password","")
    new = request.form.get("new_password","")
    if not current_user.check_password(old):
        flash("Ancien mot de passe incorrect.", "danger")
    elif len(new) < 6:
        flash("Minimum 6 caractères.", "danger")
    else:
        current_user.set_password(new)
        db.session.commit()
        flash("Mot de passe modifié.", "success")
    return redirect(url_for("admin_dashboard"))


# ─────────────────────────────────────────────
#  ERREURS
# ─────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    cfg = {}
    contacts = []
    try:
        cfg = get_all_config()
        contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order).all()
    except Exception:
        pass
    return render_template("public/404.html", cfg=cfg, contacts=contacts), 404


@app.errorhandler(413)
def too_large(e):
    flash("Fichier trop volumineux. Maximum 4 Mo par photo.", "danger")
    return redirect(request.referrer or url_for("admin_gallery"))


# ─────────────────────────────────────────────
#  INIT DB
# ─────────────────────────────────────────────

def init_db():
    try:
        with app.app_context():
            db.create_all()
            if not Admin.query.first():
                a = Admin(username=app.config["ADMIN_USERNAME"])
                a.set_password(app.config["ADMIN_PASSWORD"])
                db.session.add(a)
                db.session.commit()
                print(f"[INIT] Admin créé → {app.config['ADMIN_USERNAME']}")
    except Exception as e:
        # Ne jamais laisser une erreur DB planter toute la fonction serverless.
        print(f"[INIT DB ERROR] {e}")


# Appelé au niveau module pour Vercel serverless (pas de gunicorn)
init_db()


@app.route("/api/debug-files")
def debug_files():
    """Diagnostic temporaire : vérifie quels fichiers sont réellement présents
    dans le déploiement Vercel. À retirer une fois le problème résolu."""
    import json as _json
    info = {"base_dir": BASE_DIR}
    try:
        info["base_dir_contents"] = os.listdir(BASE_DIR)
    except Exception as e:
        info["base_dir_error"] = str(e)

    templates_path = os.path.join(BASE_DIR, "templates")
    info["templates_path"] = templates_path
    info["templates_exists"] = os.path.isdir(templates_path)
    if info["templates_exists"]:
        try:
            info["templates_contents"] = os.listdir(templates_path)
            public_path = os.path.join(templates_path, "public")
            if os.path.isdir(public_path):
                info["public_contents"] = os.listdir(public_path)
        except Exception as e:
            info["templates_list_error"] = str(e)

    return app.response_class(
        response=_json.dumps(info, indent=2, ensure_ascii=False),
        mimetype="application/json"
    )


@app.errorhandler(Exception)
def handle_any_error(e):
    """Filet de sécurité : affiche l'erreur réelle au lieu d'un 500 vide."""
    import traceback
    from werkzeug.exceptions import HTTPException
    app.logger.error(traceback.format_exc())
    if isinstance(e, HTTPException) and e.code == 404:
        return page_not_found(e)
    return f"""
    <div style="font-family:sans-serif;padding:2rem;background:#111;color:#eee;min-height:100vh">
      <h2 style="color:#e57373">Erreur serveur</h2>
      <p style="color:#aaa">Détail technique :</p>
      <pre style="background:#1a1a1a;padding:1rem;border-radius:6px;overflow-x:auto;color:#f5c542;font-size:0.85rem;white-space:pre-wrap">{str(e)}</pre>
    </div>
    """, 500


if __name__ == "__main__":
    app.run(debug=False)
