from flask_admin.contrib.mongoengine import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from flask_user import login_required, UserManager, UserMixin
from flask_mongoengine import mongoengine as db
import datetime
class User(db.Document, UserMixin):
    active = db.BooleanField(default=True)
    username = db.StringField(max_length=40, unique=True, required=True)
    password = db.StringField(max_length=40, required=True)
    tags = db.ListField(db.ReferenceField('Tag'), default=[])

    def __unicode__(self):
        return self.name

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
class UserView(ModelView):
    column_filters = ['username']

    column_searchable_list = ('username', 'password')

    form_ajax_refs = {
        'tags': {
            'fields': ('name',)
        }
    }

class FilesView(ModelView):
    can_create = False
    can_export = True

class MyHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        labels = ['JAN', 'FEB', 'MAR', 'APR','MAY', 'JUN', 'JUL', 'AUG','SEP', 'OCT', 'NOV', 'DEC']
        values = [967.67, 1190.89, 1079.75, 1349.19,2328.91, 2504.28, 2873.83, 4764.87,4349.29, 6458.30, 9907, 16297]
        return self.render('admin/index.html', max=max(values), labels = labels , values = values )




