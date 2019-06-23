import tempfile
from pdf2image import convert_from_path
import os
import cv2
import numpy as np

def read(filename): 
    with tempfile.TemporaryDirectory() as path:
         images_from_path = convert_from_path(filename, output_folder=path, last_page=1, first_page =0) 

    return cv2.cvtColor(np.array(images_from_path[0]), cv2.COLOR_RGB2BGR)