from imutils.object_detection import non_max_suppression
import numpy as np
import argparse
import time
import cv2
from sklearn import datasets
from sklearn.svm import SVC
from scipy import misc
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
import os
from pytesseract import Output

import argparse
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--pdf", type=str, help="path to input pdf")
args = vars(ap.parse_args())
def pdf_to_img(img):
    for a in os.listdir('temp/'):
        os.remove('temp/'+a)
    for a in os.listdir('outputs/'):
        os.remove('outputs/'+a)

    pages = convert_from_path(img, 500)
    count=0
    for page in pages:
        page.save('temp/'+str(count)+'.jpg')
        count+=1


def ip(img):
    lower_black = np.array([0,0,0], dtype = "uint16")
    upper_black = np.array([70,70,70], dtype = "uint16")
    image = cv2.inRange(img, lower_black, upper_black)
    image = cv2.bitwise_not(image)
    print(['[INFO] Done thresholding'])

    # cv2.imshow('mask0',image)
    # cv2.waitKey(0)
    return image

def identify_blobs_backup(img):
    # global orig
    d = pytesseract.image_to_data(img, output_type=Output.DICT)
    n_boxes = len(d['level'])
    print('[INFO] {} ROIS'.format(n_boxes-1))
    for i in range(1,n_boxes):
        (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])

        temp = img[y:y+h,x:x+w]


        print('[INFO] Extracting from ROI {}'.format(i))
        text = pytesseract.image_to_string(temp,lang='eng',
                   config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
        text = ''.join(list(text))
        text = text.replace(' ','')
        chk = [x.isdigit() for x in list(text)]
        print(text)
        if chk.count(True)>=4 and 'Y' not in chk:


            cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 255, 0), -1)


    # cv2.imwrite('temp/0.jpg',orig)
    return orig


# orig = cv2.imread('outputs/0.jpg')

pdf_to_img(args['pdf'])
for a in os.listdir('temp'):
    print('[INFO] image {}'.format(a))
    orig = cv2.imread('temp/'+a)
    cv2.imwrite('outputs/'+a,identify_blobs_backup(ip(orig)))
