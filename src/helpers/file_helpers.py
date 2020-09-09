ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'pdf']) # FOUND IN HELPERS allowed_file

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_local(filename, filepath):
    
    pass