from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    __tablename__ = "admin"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SiteConfig(db.Model):
    __tablename__ = "site_config"
    id    = db.Column(db.Integer, primary_key=True)
    key   = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default="")


class Experience(db.Model):
    __tablename__ = "experience"
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    company     = db.Column(db.String(200), default="")
    description = db.Column(db.Text, default="")
    year_start  = db.Column(db.String(10), default="")
    year_end    = db.Column(db.String(10), default="")
    order       = db.Column(db.Integer, default=0)
    visible     = db.Column(db.Boolean, default=True)


class Formation(db.Model):
    __tablename__ = "formation"
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    institution = db.Column(db.String(200), default="")
    year        = db.Column(db.String(10), default="")
    description = db.Column(db.Text, default="")
    order       = db.Column(db.Integer, default=0)
    visible     = db.Column(db.Boolean, default=True)


class Project(db.Model):
    __tablename__ = "project"
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    category    = db.Column(db.String(100), default="autre")
    cover_photo = db.Column(db.String(500), default="")
    date        = db.Column(db.String(20), default="")
    order       = db.Column(db.Integer, default=0)
    visible     = db.Column(db.Boolean, default=True)
    photos      = db.relationship("Photo", backref="project", lazy=True,
                                  cascade="all, delete-orphan")


class Photo(db.Model):
    __tablename__ = "photo"
    id          = db.Column(db.Integer, primary_key=True)
    filename    = db.Column(db.String(500), nullable=False)   # URL ImgBB complète
    title       = db.Column(db.String(200), default="")
    description = db.Column(db.Text, default="")
    category    = db.Column(db.String(100), default="autre")
    project_id  = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=True)
    order       = db.Column(db.Integer, default=0)
    visible     = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class ContactInfo(db.Model):
    __tablename__ = "contact_info"
    id      = db.Column(db.Integer, primary_key=True)
    type    = db.Column(db.String(50), nullable=False)
    label   = db.Column(db.String(100), default="")
    value   = db.Column(db.String(300), nullable=False)
    icon    = db.Column(db.String(50), default="")
    order   = db.Column(db.Integer, default=0)
    visible = db.Column(db.Boolean, default=True)


class Message(db.Model):
    __tablename__ = "message"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), nullable=False)
    email      = db.Column(db.String(200), default="")
    phone      = db.Column(db.String(50), default="")
    subject    = db.Column(db.String(300), default="")
    body       = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
