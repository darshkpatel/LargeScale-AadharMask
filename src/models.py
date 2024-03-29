from flask_admin.contrib.mongoengine import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from flask_login import UserMixin
from flask_mongoengine import mongoengine as db
import datetime
from werkzeug.security import check_password_hash, generate_password_hash

class User(db.Document, UserMixin):
    active = db.BooleanField(default=True)
    username = db.StringField(max_length=40, unique=True, required=True, min_length=3)
    password = db.StringField(required=True,min_length=8)
    tags = db.ListField(db.ReferenceField('Tag'), default=[])

    def __unicode__(self):
        return self.username
    
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    @staticmethod
    def show_tag(self):
        names = []
        for tag in self.tags:
            names.append(tag.name)
        return names
    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)


class Tag(db.Document):
    name = db.StringField(max_length=20, unique=True,  min_length=3, required=True)
    def __unicode__(self):
        return self.name

class Files(db.Document):
    location = db.StringField(required=True, unique=True)
    orig_name = db.StringField(required=True)
    saved_at = db.DateTimeField(default=datetime.datetime.now)
    uploader = db.StringField()
    aadhar_hash = db.StringField()
    remote_storage = db.BooleanField(default = False)

class Settings(db.Document):
    remote_storage = db.BooleanField(default = False, unique=True)
    crop_images = db.BooleanField(default = True, unique=True)

# Customized admin views



