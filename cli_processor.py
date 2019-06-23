from src.image_processors.new_mask import mask_image
import argparse, os

# Handle Directory Parsing
def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

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
print("Processing {} files in {}".format(len(f), args.dirpath))



