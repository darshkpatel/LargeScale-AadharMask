from flask import Flask, Response, request, has_request_context, jsonify, redirect, url_for, render_template,session, abort, flash,logging, render_template_string, send_from_directory, url_for
from flask.logging import default_handler
from werkzeug.utils import secure_filename
import json,os,base64
import tempfile
from celery.signals import after_setup_logger
import numpy.core.multiarray
from cv2 import imread, imencode, imwrite
import time, random
import base64
from celery import Celery
from image_processors import pdf_to_cv
from image_processors import new_mask
from helpers.file_helpers import allowed_file
from flask_user import login_required, UserManager, UserMixin
from flask_mongoengine import MongoEngine
from flask_admin import Admin
from flask_admin.form import rules
import datetime
import flask_admin as admin
from models import *
from flask_admin import expose,helpers
import flask_login as login
from wtforms import form, fields, validators
from flask_admin.form import rules
from flask_admin.menu import MenuLink
from flask_admin.contrib.mongoengine import ModelView
import random, string
from werkzeug.security import generate_password_hash, check_password_hash




#ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'pdf']) # FOUND IN HELPERS allowed_file


#Setup Logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!apsolapolaposkpaopokpokpokpq'
app.config['LOCAL_STORAGE'] = './local-storage-aadhar/'
app.config["CELERY_BROKER_URL"]='redis://localhost:6379'
app.config["CELERY_RESULT_BACKEND"]='redis://localhost:6379'
app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'
app.config["MONGODB_SETTINGS"] = {
    'db':'AadharMaskDB',
    # 'username':None,
    # 'password':None,
     'host':"mongodb://localhost",
    # 'port':None
}




tmpdir = tempfile.TemporaryDirectory() 



def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)
db = MongoEngine(app)

# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return User.objects(username=self.login.data).first()
class RegistrationForm(form.Form):
    username = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if User.objects(username=self.username.data):
            raise validators.ValidationError('Duplicate username')



class UserView(ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated()
    column_filters = ['username']

    column_searchable_list = ('username', 'password')

    form_ajax_refs = {
        'tags': {
            'fields': ('name',)
        }
    }

class FilesView(ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated
    can_create = False
    can_export = True

class MyHomeView(AdminIndexView):
    def is_accessible(self):
        return login.current_user.is_authenticated
    @expose('/')
    def index(self):
        labels = ['JAN', 'FEB', 'MAR', 'APR','MAY', 'JUN', 'JUL', 'AUG','SEP', 'OCT', 'NOV', 'DEC']
        values = [967.67, 1190.89, 1079.75, 1349.19,2328.91, 2504.28, 2873.83, 4764.87,4349.29, 6458.30, 9907, 16297]
        return self.render('admin/index.html', max=max(values), labels = labels , values = values )


def init_login():
    login_manager = login.LoginManager()
    login_manager.setup_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(username=user_id).first()

@app.route('/register/', methods=('GET', 'POST'))
def register_view():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User()

        form.populate_obj(user)
        user.save()

        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('form.html', form=form)
@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))
@app.route('/login/', methods=('GET', 'POST'))
def login_view():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = form.get_user()
        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('form.html', form=form)


# Flask views
@app.route('/')
def index():
    return render_template('index.html', user=login.current_user)

admin = admin.Admin(app, 'Aadhar Masking Endpoint', index_view=MyHomeView())

init_login()

# Add views
admin.add_view(UserView(User,name="User Details", category="User Management"))
admin.add_view(FilesView(Files, name="File Info"))
admin.add_view(ModelView(Tag, name = "Tags/Roles",category="User Management"))
admin.add_link(MenuLink(name='Logout', url='/logout'))


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = handle_file.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'filename':'',
            'task_status':''

        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'filename': task.info.get('filename', ''),
            'task_status': task.info.get('task_status', '')
        }
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'filename':'',
            'task_status':'',
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@app.route('/test', methods=['GET'])
def longtask():
    task = long_task.apply_async("hello", " world")
    return redirect(url_for('taskstatus', task_id=task.id))

#Sanity Check
@app.route("/ping")
def ping():
    return "pong"
# @app.route("/")
# def index():
#     return "Nothing Here"

@app.route('/local-storage-aadhar/<path:path>')
def send_files(path):
    return send_from_directory('local-storage-aadhar', path.split('/')[-1])
# URL Routes

### MASK ALL TEXT

"""

NEW MASKING SCRIPT

"""



@app.route('/aadhar_single', methods=['GET', 'POST'])
def new_aadhar():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'error':'Empty File'})
        file = request.files['file']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({'error':'Empty File'})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            app.logger.info('Got Uploaded File: %s ', filename)
            with tempfile.TemporaryDirectory() as tmpdir:
                filepath = os.path.join(tmpdir, filename)
                file.save(filepath)
                if filepath.split(".")[-1]=="pdf":
                    img = pdf_to_cv.read(filepath)
                else:
                    img = imread(filepath)
                error, result = new_mask.mask_image(img)
                if error:
                    return("Unable to mask")

                retval, buffer = imencode('.jpg', result)
                jpg_as_text = base64.b64encode(buffer)
                result = "data:image/jpg;base64,"+str(jpg_as_text, "utf-8")
                return("<img src=\""+result+"\">")
        else:
            return jsonify({'error':'Empty File'})

            
    return '''
    <!doctype html>
    <title>Test Masking Endpoint</title>
    <h1>Test Masking Endpoint</h1>
    <h3>Upload Any file</h3>
    <form method=post action="/aadhar_single" enctype=multipart/form-data>
      <input type=file name=file accept="*">
      <input type=submit value=Upload>
    </form>
    '''


@celery.task(bind=True)
def handle_file(self, file_name, file_path, store_local=True, store_remote=False):
    local_path = ''

    if file_name.split(".")[-1]=="pdf":
        img = pdf_to_cv.read(file_path)
    else:
        img = imread(file_path)
    self.update_state(state='PROGRESS', meta={'filename': file_name, 'task_status':"Masking Aadhar" })
    error, result = new_mask.mask_image(img)
    if error:
        os.remove(file_path)
        raise ValueError('Unable to Process Aadhar')

    # retval, buffer = imencode('.jpg', result)

    # Image Storage
    if(store_local):
        random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        random_name+='.png'
        if os.path.exists(os.path.join(app.config['LOCAL_STORAGE'], random_name)):
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            random_name+='.png'
        local_path = os.path.join(app.config['LOCAL_STORAGE'], random_name)
        try:
            imwrite(local_path,result)
            file_metadata = Files(location=local_path, orig_name=file_name)
            file_metadata.save()
            print("Saved ! ")
        except:
            print("Error Saving File on Disk Or DB")
            app.logger.error('Unable to Save Processed file: %s at %s ', file_path, os.path.join(app.config['LOCAL_STORAGE'], random_name))

    try:
        os.remove(file_path)
        self.update_state(state='PROGRESS', meta={'filename': file_name, 'task_status':"Removed Temp File" })
    except:
        app.logger.error('Unable to delete: %s ', file_path)

    self.update_state(state='PROGRESS', meta={'filename': file_name, 'task_status':"Done !", 'local_path':local_path })

    return {'filename': file_name, 'task_status':"Done !", 'local_path':local_path}


@app.route('/aadhar_multi', methods=['GET', 'POST'])
def multi_aadhar():
    if request.method == 'POST':
        # check if the post request has the file part
        uploaded_files = request.files.getlist("file")
        file_objs = []

        for file in uploaded_files:
            if file.filename == '':
                continue
                # return jsonify({'error':'Empty File'})
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                app.logger.info('Got Uploaded File: %s ', filename)

                filepath = os.path.join(tmpdir.name, filename)
                file.save(filepath)
                file_objs.append({"task_id":handle_file.apply_async(args=[filename, filepath]).id, "filename":filename})
            else:
                continue
                # return jsonify({'error':'Invalid or Corrupt File'})

        return jsonify({"data":file_objs, "status":"ok"})
                
                    



            
    return '''
    <!doctype html>
    <title>Test Masking Endpoint</title>
    <h1>Test Masking Endpoint</h1>
    <h3>Upload Any file</h3>
    <form method=post action="/aadhar_multi" enctype=multipart/form-data>
      <input type=file name=file accept="*" multiple>
      <input type=submit value=Upload>
    </form>
    '''


if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5000, debug=True)
