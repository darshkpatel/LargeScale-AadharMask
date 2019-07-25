from flask_admin.contrib.mongoengine import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from flask_user import login_required, UserManager, UserMixin
from flask_mongoengine import mongoengine as db
import datetime
from werkzeug.security import check_password_hash

class User(db.Document, UserMixin):
    active = db.BooleanField(default=True)
    username = db.StringField(max_length=40, unique=True, required=True)
    password = db.StringField(max_length=40, required=True)
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
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)


class Tag(db.Document):
    name = db.StringField(max_length=50)
    def __unicode__(self):
        return self.name

class Files(db.Document):
    location = db.StringField(required=True, unique=True)
    orig_name = db.StringField(required=True)
    saved_at = db.DateTimeField(default=datetime.datetime.now)
    uploader = db.ListField(db.ReferenceField('User'))
    remote_storage = db.BooleanField(default = False)
# Customized admin views



