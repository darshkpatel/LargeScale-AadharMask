from flask import Flask, Response, request, jsonify, redirect, url_for, render_template,session, abort, flash,logging
from werkzeug.utils import secure_filename
import json,os
from image_processors import qrcode
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'


#Sanity Check
@app.route("/ping")
def ping():
    return "Pong"


# URL Routes


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            result = str(qrcode.process(file.read()))
            if result and is_aadhar(result):
                return jsonify(xml_to_json(result))
            
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
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
    po_index_start = data.find('po=')+4
    po_index_end = data.find('"',po_index_start)
    pc_index_start = data.find('pc=')+4
    pc_index_end = data.find('"',pc_index_start)
    return {'uid':  int(data[uid_index_start:uid_index_end]),
        'name': data[name_index_start:name_index_end],
        'gender': data[gender_index_start:gender_index_end],
        'yob': data[yob_index_start:yob_index_end],
        'co': data[co_index_start:co_index_end],
        'lm': data[lm_index_start:lm_index_end],
        'loc': data[loc_index_start:loc_index_end],
        'vtc': data[vtc_index_start:vtc_index_end],
        'po': data[po_index_start:po_index_end],
        'dist': data[dist_index_start:dist_index_end],
        'state': data[state_index_start:state_index_end],
        'pc': data[pc_index_start:pc_index_end],
        'dob': data[dob_index_start:dob_index_end]}
    

def is_aadhar(xml):
    """
    Checks if the given bytestring is from a aadhar card qr code or not
    """
    if("b'</?xml version=\"1.0\" encoding=\"UTF-8\"?> <PrintLetterBarcodeData uid=" in xml):
        return True
    else:
        return False

if __name__ == "__main__":
    Flask.run(app, host='0.0.0.0', port=5000, debug=True)