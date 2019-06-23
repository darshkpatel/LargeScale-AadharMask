import os
import time
import base64

import cv2
from nms import nms
import numpy as np

import pytesseract
import re

from PIL import Image
from .pdf_to_cv import read
from .crop_image import process_image


def deskew(image):
    print("Deskewing Image")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)

    # threshold the image, setting all foreground pixels to
    # 255 and all background pixels to 0
    thresh = cv2.threshold(gray, 0, 255,
                           cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # grab the (x, y) coordinates of all pixel values that
    # are greater than zero, then use these coordinates to
    # compute a rotated bounding box that contains all
    # coordinates
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]

    # the `cv2.minAreaRect` function returns values in the
    # range [-90, 0); as the rectangle rotates clockwise the
    # returned angle trends to 0 -- in this special case we
    # need to add 90 degrees to the angle
    if angle < -45:
        angle = -(90 + angle)

    # otherwise, just take the inverse of the angle to make
    # it positive
    else:
        angle = -angle

    # rotate the image to deskew it
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    # draw the correction angle on the image so we can validate it
    
    #Resize Image
    img = cv2.resize(rotated,None,fx=1.5,fy=1.5,interpolation=cv2.INTER_CUBIC)

    return img


def thresholding(img):
    print("Adjusting Image Thresholds")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.bilateralFilter(img,15,75,75)
    cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 3)
    #plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return img

# Add Sanity checks such as masking area ,etc.  
def mask(img,dfs):
    masked = img.copy()
    for index,df in dfs.iterrows():
        cv2.rectangle(masked, (df['left'],df['top']),(df['left']+df['width'],df['top']+df['height']),(0,255,0),-1)
    return masked
    



def mask_image(img ,thresh=15, crop=True):
    #img =cv2.imread(r'test04.png')
    if crop:
        print("Cropping Image [This may cause bugs in already cropped images]")
        PILImage = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        PILImage = process_image(PILImage)
        img = cv2.cvtColor(np.array(PILImage), cv2.COLOR_RGB2BGR)

    orig = img = deskew(img)
    img = thresholding(img)

    CONFIDENCE_THRESHOLD=thresh
    config = ("--oem 3 --psm 11 -l eng -c preserve_interword_spaces=1" )
    print("Extracting text with confidence threshold: "+str(CONFIDENCE_THRESHOLD))
    extracted_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DATAFRAME, config=config)
    extracted_data = extracted_data.dropna()
    extracted_data.text = extracted_data.text.map(lambda x: re.sub(r'[^a-zA-Z0-9\/]+', '', x))
    extracted_data = extracted_data[(extracted_data.conf > CONFIDENCE_THRESHOLD)  & (extracted_data.text.str.len()>2)]

    # dob = extracted_data[extracted_data.text.str.match(r'\d+/\d+/\d+')]
    # if dob.empty:
    #     dob = extracted_data[extracted_data.text.str.match(r'(?i)\bDOB\b|\bYEAR\b')].block_num
    #     if not dob.empty:
    #         dob = extracted_data[extracted_data.block_num==int(dob)].tail(1)
    #     else:
    #         print("DOB Not Found")

    aadhar_uid = extracted_data[(extracted_data.text.str.match(r'\d{4}'))]
    # Filter blocks containing more than 2 sets of 4 digit numbers
    aadhar_uid=aadhar_uid.groupby('block_num').filter(lambda x: len(x) >= 2)
    if aadhar_uid.empty:
        print("[ERROR] Unable to process image, no UID found")
        return True, ""
    to_mask = aadhar_uid.head(2)
    try:
        masked_image = mask(orig,to_mask)
    except Exception as e:
        print("[ERROR] Failed Masking Image")
        print(e)
        print("[ERROR] Exception Caught, Continuing")
    print("Masked Successfully")
    return False, masked_image

