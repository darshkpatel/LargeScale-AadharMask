from flask import Flask, Response, request, jsonify, redirect, url_for, render_template,session, abort, flash,logging
from werkzeug.utils import secure_filename
import json,os,base64
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import tempfile
import cv2
import base64
from image_processors import qrcode
from image_processors import text_mask
from image_processors import selective_mask
from image_processors import pdf_to_cv
from image_processors import crop_image
from image_processors import new_mask
from pdf_processors.adhar_subha import parse_pdf
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'pdf'])


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

#Sanity Check
@app.route("/ping")
def ping():
    return "Pong"
@app.route("/")
def index():
    return "Please Check URL Endpoint"


# URL Routes

### MASK ALL TEXT
@app.route('/mask', methods=['GET', 'POST'])
def upload_file1():
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

            result = str(text_mask.text_mask(file.read()), "utf-8")
            result = "data:image/jpg;base64,"+result
            return("<img src=\""+result+"\">")
    return '''
    <!doctype html>
    <title>Test Masking Endpoint</title>
    <h1>Test Masking Endpoint</h1>
    <h3>Upload Any .jpg file</h3>
    <form method=post action="/mask" enctype=multipart/form-data>
      <input type=file name=file accept="image/*">
      <input type=submit value=Upload>
    </form>
    '''

# Mask Specific Parts
@app.route('/mask_aadhar', methods=['GET', 'POST'])
@limiter.limit("40 per hour")
def mask_aadhar_specific():
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
            file_string = file.read()
            result = str(qrcode.process(file_string))
            if result and is_aadhar(result):
                uid = str(xml_to_json(result)['uid'])
                imageString, error = selective_mask.mask_specific(file_string, [uid[0:4],uid[4:8]])
                result = "data:image/jpg;base64,"+str(imageString, "utf-8")
                return("<img src=\""+result+"\">")
            else:
                return jsonify({'error':'Not a valid aadhar card image', 'debug': str(is_aadhar(result)), 'data': result})
        else:
            return jsonify({'error':'Empty File'})

            
    return '''
    <!doctype html>
    <title>Test Masking Endpoint</title>
    <h1>Test Masking Endpoint</h1>
    <h3>Upload Any .jpg file</h3>
    <form method=post action="/mask_aadhar" enctype=multipart/form-data>
      <input type=file name=file accept="image/*">
      <input type=submit value=Upload>
    </form>
    '''


"""

NEW MASKING SCRIPT

"""



@app.route('/new_aadhar', methods=['GET', 'POST'])
@limiter.limit("40 per hour")
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
            print(filename)
            with tempfile.TemporaryDirectory() as tmpdir:
                filepath = os.path.join(tmpdir, filename)
                file.save(filepath)
                if filepath.split(".")[-1]=="pdf":
                    img = pdf_to_cv.read(filepath)
                else:
                    img = cv2.imread(filepath)
                error, result = new_mask.mask_image(img)
                if error:
                    return("Unable to mask")

                retval, buffer = cv2.imencode('.jpg', result)
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
    <form method=post action="/new_aadhar" enctype=multipart/form-data>
      <input type=file name=file accept="*">
      <input type=submit value=Upload>
    </form>
    '''
# PDF SUBHADITYA
@app.route('/mask_aadhar_pdf', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def mask_aadhar_pdf():
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
            file.save(os.path.join("./", filename))
            imageString = parse_pdf(os.path.join("./", filename))
            result = "data:image/jpg;base64,"+str(imageString, "utf-8")
            return("<img src=\""+result+"\">")
        else:
            return jsonify({'error':'Empty File'})

            
    return '''
    <!doctype html>
    <title>Test Masking Endpoint</title>
    <h1>Test Masking Endpoint</h1>
    <h3>Upload Any .pdf file</h3>
    <form method=post action="/mask_aadhar_pdf" enctype=multipart/form-data>
      <input type=file name=file accept="application/pdf">
      <input type=submit value=Upload>
    </form>
    '''
@app.route('/aadhar', methods=['GET', 'POST'])
def aadhar():
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

            result = str(qrcode.process(file.read()))
            if result and is_aadhar(result):
                return jsonify(xml_to_json(result))
            else:
                return jsonify({'error':'Not a valid aadhar card image', 'debug': str(is_aadhar(result)), 'data': result})
        else:
            return jsonify({'error':'Empty File'})
            
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post action="/aadhar" enctype=multipart/form-data>
      <input type=file name=file accept="image/*">
      <input type=submit value=Upload>
    </form>
    '''
    

#Helper Functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def xml_to_json(data):
    uid_index_start = data.find('uid=')+5
    uid_index_end = uid_index_start+12
    name_index_start = data.find('name=')+6
    name_index_end = data.find('"',name_index_start)
    gender_index_start = data.find('gender=')+8
    gender_index_end = data.find('"',gender_index_start)
    yob_index_start = data.find('yob=')+5
    yob_index_end = yob_index_start+4
    co_index_start = data.find('co=')+4
    co_index_end = data.find('"',co_index_start)
    lm_index_start = data.find('lm=')+4
    lm_index_end = data.find('"',lm_index_start)
    loc_index_start = data.find('loc=')+5
    loc_index_end = data.find('"',loc_index_start)
    vtc_index_start = data.find('vtc=')+5
    vtc_index_end = data.find('"',vtc_index_start)
    dob_index_start = data.find('dob=')+5
    dob_index_end = data.find('"',dob_index_start)
    dist_index_start = data.find('dist=')+6
    dist_index_end = data.find('"',dist_index_start)
    state_index_start = data.find('state=')+7
    state_index_end = data.find('"',state_index_start)
    house_index_start = data.find('house=')+7
    house_index_end = data.find('"',house_index_start)
    po_index_start = data.find('po=')+4
    po_index_end = data.find('"',po_index_start)
    pc_index_start = data.find('pc=')+4
    pc_index_end = data.find('"',pc_index_start)
    extracted_data =  {'uid':  int(data[uid_index_start:uid_index_end]),
        'name': data[name_index_start:name_index_end],
        'gender': data[gender_index_start:gender_index_end],
        'yob': data[yob_index_start:yob_index_end],
        'po': data[po_index_start:po_index_end],
        'dist': data[dist_index_start:dist_index_end],
        'state': data[state_index_start:state_index_end],
        'pc': data[pc_index_start:pc_index_end]}

    if "version=" not in data[vtc_index_start:vtc_index_end]:
        extracted_data['vtc'] = data[vtc_index_start:vtc_index_end]
    if "version=" not in data[loc_index_start:loc_index_end]:
        extracted_data['loc'] = data[loc_index_start:loc_index_end]
    if "version=" not in data[co_index_start:co_index_end]:
        extracted_data['co'] = data[co_index_start:co_index_end]
    if "version=" not in data[dob_index_start:dob_index_end]:
        extracted_data['dob'] = data[dob_index_start:dob_index_end]
    if "version=" not in data[dob_index_start:dob_index_end]:
        extracted_data['house'] = data[house_index_start:house_index_end]
    if "version=" not in data[lm_index_start:lm_index_end]:
        extracted_data['lm'] = data[lm_index_start:lm_index_end]
    return extracted_data

def is_aadhar(xml):
    """
    Checks if the given bytestring is from a aadhar card qr code or not
    """
    
    if("PrintLetterBarcodeData" in xml and "uid=" in xml):
        return True
    else:
        return False

if __name__ == "__main__":
    Flask.run(app, host='0.0.0.0', port=5000, debug=True)
