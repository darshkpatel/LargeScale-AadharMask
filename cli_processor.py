from src.image_processors import new_mask
from src.image_processors import pdf_to_cv
import argparse, os, cv2

# Handle Directory Parsing
def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


# Arg Parsing and help message 
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description='Aadhar Masking')
parser.add_argument('--dir',dest='dirpath', help='Process all files inside directory', type=dir_path)
parser.add_argument('--no-crop', dest='nocrop', help='Do not try to crop images', action='store_true')
args = parser.parse_args()


# Handle Arguments
if not args.dirpath:
    print("ERROR, please supply directory to process")
    parser.print_help()
    exit(1)
if not args:
    parser.print_usage()
    exit(1)

f = []
for (dirpath, dirnames, filenames) in os.walk(args.dirpath):
    f.extend(filenames)
    break


total_files = len(f)
print("Processing {} files in {}".format(total_files, args.dirpath))

# Sanity check to create folder
if not os.path.exists(os.path.join(args.dirpath,"processed")):
    print("[INFO] Creating Processed Files Directory")
    os.makedirs(os.path.join(args.dirpath,"processed"))
    
# Parse files sequentially
for index,file in enumerate(f):
    print("[INFO] Processing File {} / {} => {} ".format(index+1,total_files,file))
    if file.split(".")[-1]=="pdf":
        img = pdf_to_cv.read(os.path.join(args.dirpath,file))
    elif file.split(".")[-1] in ["jpg","jpeg","pdf","png"]:
        img = cv2.imread(os.path.join(args.dirpath,file))
    else:
        print("[ERROR] {} is not a supported image or PDF".format(file))
        continue
    if args.nocrop:
        error, result = new_mask.mask_image(img, crop=False)
    else:
        error, result = new_mask.mask_image(img, crop=True)
    if error:
        print("[ERROR] Cannot Process {}".format(file))
    else:
        filename = '.'.join(file.split('.')[:-1])+".png"
        cv2.imwrite(os.path.join(args.dirpath,"processed",filename),result)
        print("[INFO] Processed {}".format(file))
