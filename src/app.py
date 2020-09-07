from flask import Flask, Response, request, has_request_context, jsonify, redirect, url_for, render_template,session, abort, flash,logging, render_template_string, send_from_directory, url_for
# from flask.logging import default_handler
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
from helpers.date_helpers import *
from helpers.aws_upload import *
from flask_login import login_required, LoginManager, UserMixin, login_user
from flask_mongoengine import MongoEngine
import datetime
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
     'host':"mongodb://mongodb/AadharMaskDB",
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


class UserView(ModelView):
    def is_accessible(self):
       
        is_admin = User.objects(username=str(login.current_user.username), tags__in=Tag.objects.filter(name='Administrator').all()).count() >= 1
        return login.current_user.is_authenticated and is_admin
    column_filters = ['username']

    column_searchable_list = ('username', 'password')
    def on_model_change(self, form, model, is_created):
        model.password = generate_password_hash(model.password)
    form_ajax_refs = {
        'tags': {
            'fields': ('name',)
        }
    }


class FilesView(ModelView):
    def is_accessible(self):
        is_admin = User.objects(username=str(login.current_user.username), tags__in=Tag.objects.filter(name='Administrator').all()).count() >= 1
        return login.current_user.is_authenticated and is_admin
    can_create = False
    can_export = True
    can_delete = True
    can_edit = False
class SettingsView(ModelView):
    def is_accessible(self):
       
        is_admin = User.objects(username=str(login.current_user.username), tags__in=Tag.objects.filter(name='Administrator').all()).count() >= 1
        return login.current_user.is_authenticated and is_admin
    can_create = True
    can_export = False
    can_delete = False

class MyHomeView(AdminIndexView):
    def is_accessible(self):
       
        is_admin = User.objects(username=str(login.current_user.username), tags__in=Tag.objects.filter(name='Administrator').all()).count() >= 1
        return login.current_user.is_authenticated and is_admin
    @expose('/')
    def index(self):
        labels = ['JAN', 'FEB', 'MAR', 'APR','MAY', 'JUN', 'JUL', 'AUG','SEP', 'OCT', 'NOV', 'DEC']
        first_days,last_days = get_arrays(datetime.datetime.now().year)
        values = []      
        for month in range(0,12):
            values.append(Files.objects(saved_at__gte=first_days[month],saved_at__lte=last_days[month]).count())
        # values = [967.67, 1190.89, 1079.75, 1349.19,2328.91, 2504.28, 2873.83, 4764.87,4349.29, 6458.30, 9907, 16297]
        return self.render('admin/index.html', max=max(values), labels = labels , values = values )


def init_login():
    login_manager = login.LoginManager()
    login_manager.setup_app(app)
    login_manager.login_view = 'login_post'

    # @login_manager.user_loader
    # def load_user(user_id):
    #     # since the user_id is just the primary key of our user table, use it in the query for the user
    #     return User.query.get(int(username))
    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(username=user_id).first()

admin = admin.Admin(app, 'Aadhar Masking Endpoint', index_view=MyHomeView())

init_login()

# Add views
admin.add_view(UserView(User,name="User Details", category="User Management"))
admin.add_view(FilesView(Files, name="File Info"))
admin.add_view(SettingsView(Settings, name="Settings"))

#Extra Links
admin.add_link(MenuLink(name='Logout', url='/logout'))

#Direct Model Views
admin.add_view(ModelView(Tag, name = "Tags/Roles",category="User Management"))



@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))




@app.route('/login', methods=['POST','GET'])
def login_post():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.objects(username=username).first()

        # check if user actually exists
        # take the user supplied password, hash it, and compare it to the hashed password in database
        if not user or not check_password_hash(user.password, password): 
            flash('Please check your login details and try again.')
            return redirect(url_for('login_post')) # if user doesn't exist or password is wrong, reload the page

        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)

        return redirect(url_for(request.args.get('next', 'index')))
    else:
        return render_template('login.html')

@app.route('/')
def index():
    if login.current_user.is_authenticated:
        
        return render_template('index.html', user=login.current_user)
    else:
        return redirect(url_for('login_post'))



#Unauthenticated for now
@app.route('/status/<task_id>')
@login_required
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


#Sanity Check
@app.route("/ping")
def ping():
    return "pong"

@app.route('/local-storage/<path:path>')
@login.login_required
def send_files(path):
    is_admin = User.objects(username=str(login.current_user.username), tags__in=Tag.objects.filter(name='Administrator').all()).count() >= 1
    if login.current_user.is_authenticated and is_admin:
        return send_from_directory('local-storage-aadhar', path.split('/')[-1])
    else:
        return abort(403)

@app.route('/remote-storage/<path:path>')
@login.login_required
def show_remote_files(path):
    is_admin = User.objects(username=str(login.current_user.username), tags__in=Tag.objects.filter(name='Administrator').all()).count() >= 1
    if login.current_user.is_authenticated and is_admin:
        return render_template('remote-view.html', location = create_presigned_url(path))
    else:
        return abort(403)
# URL Routes

### MASK ALL TEXT

"""

NEW MASKING SCRIPT

"""



@app.route('/aadhar_single', methods=['GET', 'POST'])
@login_required
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
                isErrorOccured = False
                error, result = new_mask.mask_image(img)
                if error and not isErrorOccured:
                    print("masking without crop")
                    error, result = new_mask.mask_image(img,crop=False)
                    isErrorOccured = True
                elif error and isErrorOccured:
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
def handle_file(self, file_name, file_path, uploader):
    local_path = ''

    if file_name.split(".")[-1]=="pdf":
        img = pdf_to_cv.read(file_path)
    else:
        img = imread(file_path)
    self.update_state(state='PROGRESS', meta={'filename': file_name, 'task_status':"Masking Aadhar" })

    should_crop = Settings.objects().first().crop_images
    error, result = new_mask.mask_image(img, crop=should_crop)
    if error:
        print("Unable to mask, not cropping image and retrying")
        error, result = new_mask.mask_image(img,crop=False)
        if error:
            os.remove(file_path)
            raise Exception('Unable to Process Aadhar')
    remote_storage = Settings.objects().first().remote_storage

    random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    random_name+='.png'
    if( not remote_storage):
    # In case of collision
        # if os.path.exists(os.path.join(app.config['LOCAL_STORAGE'], random_name)):
        #     random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        #     random_name+='.png'
        local_path = os.path.join(app.config['LOCAL_STORAGE'], random_name)
        try:
            imwrite(local_path,result)
            print("Saved ! ")
        except Exception as e:
            print("Error Saving File on Disk")
            app.logger.error(e)
            app.logger.error('Unable to Save Processed file: %s at %s ', file_path, os.path.join(app.config['LOCAL_STORAGE'], random_name))
            raise Exception(" Cannot Save File On Disk")
    else:
        print("Uploading File to AWS")
        with tempfile.TemporaryDirectory() as tmpdirname:
            temp_location = os.path.join(tmpdirname,random_name)
            imwrite(temp_location,result)
            if not upload_to_aws(temp_location, random_name):
                print("Cannot Upload File to AWS")
                raise Exception("Cannot Upload File to AWS")
    
    
    #Store on DB
    try:
        # print(str(login.current_user.username))
        user_uploader = User.objects(username = uploader).first().username
        # print(uploader.first().to_json())
        print(uploader)
        file_metadata = Files(location=random_name, orig_name=file_name, uploader=str(user_uploader))
        file_metadata.save()
    except Exception as e:
        print(str(e))
        print("Error Saving File Details to DB, deleting file ")
        if not remote_storage:
            os.remove(local_path)
            print("Deleted local file")

    try:
        print("Removing Temp File")
        os.remove(file_path)
        self.update_state(state='PROGRESS', meta={'filename': file_name, 'task_status':"Removed Temp File" })
    except:
        app.logger.error('Unable to delete: %s ', file_path)

    self.update_state(state='PROGRESS', meta={'filename': file_name, 'task_status':"Done !", 'filename':random_name })

    return {'filename': file_name, 'task_status':"Done !", 'filename':random_name}


@app.route('/aadhar_multi', methods=['GET', 'POST'])
@login_required
def multi_aadhar():
    if request.method == 'POST':
        # check if the post request has the file part
        uploaded_files = request.files.getlist("file")
        file_objs = []
        print("Uploader: ", str(login.current_user.username))

        for file in uploaded_files:
            if file.filename == '':
                continue
                # return jsonify({'error':'Empty File'})
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                app.logger.info('Got Uploaded File: %s ', filename)

                filepath = os.path.join(tmpdir.name, filename)
                uploader =  str(login.current_user.username)
                file.save(filepath)
                file_objs.append({"task_id":handle_file.apply_async(args=[filename, filepath, uploader]).id, "filename":filename})
            else:
                # continue
                return jsonify({'error':'Invalid or Corrupt File'})

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
