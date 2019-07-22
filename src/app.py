from flask import Flask, Response, request, has_request_context, jsonify, redirect, url_for, render_template,session, abort, flash,logging
from flask.logging import default_handler
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
import json,os,base64
import tempfile
import numpy.core.multiarray
from cv2 import imread, imencode
import time, random
import base64
from celery import Celery
from image_processors import pdf_to_cv
from image_processors import new_mask
from helpers.file_helpers import allowed_file


#ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'pdf']) # FOUND IN HELPERS allowed_file


#Setup Logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config["MONGO_URI"] = "mongodb://localhost:27017/AadharMaskDB"
app.config["CELERY_BROKER_URL"]='redis://localhost:6379'
app.config["CELERY_RESULT_BACKEND"]='redis://localhost:6379'
app.config['UPLOAD_FOLDER'] = "uploaded-files/"


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
mongo = PyMongo(app)


@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}





@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@app.route('/test', methods=['GET'])
def longtask():
    task = long_task.apply_async()
    return redirect(url_for('taskstatus', task_id=task.id))

#Sanity Check
@app.route("/ping")
def ping():
    return "pong"
@app.route("/")
def index():
    return "Nothing Here"



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

@app.route('/aadhar_multi', methods=['GET', 'POST'])
def multi_aadhar():
    if request.method == 'POST':
        # check if the post request has the file part
        uploaded_files = request.files.getlist("file")
        filenames = []
        print(uploaded_files)


        with tempfile.TemporaryDirectory() as tmpdir:
            for file in uploaded_files:
                if file.filename == '':
                    app.logger.error('Empty File Name')
                    return jsonify({'error':'Empty File Name'})
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    app.logger.info('Got Uploaded File: %s ', filename)
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
                    # jpg_as_text = base64.b64encode(buffer)
                    # result = "data:image/jpg;base64,"+str(jpg_as_text, "utf-8")
                    # return("<img src=\""+result+"\">")
                else:
                    app.logger.info('Invalid File Extension Uploaded: %s ', file.filename)
                    return jsonify({'error':'Invalid File Uploaded '+file.filename})

            
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
