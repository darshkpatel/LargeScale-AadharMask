# USAGE
# opencv-text-detection --image images/lebron_james.jpg

# import the necessary packages
import argparse
import os
import time
import base64
import cv2
import numpy as np
import pandas as pd
import pytesseract




def mask_specific(img, textArr):
    npimg = np.fromstring(img, np.uint8)
    image1 = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    # image1 = cv2.imread(r'5aadhaarcrop.jpg', cv2.IMREAD_COLOR)
    orig1 = image1.copy()
    image1 = cv2.resize(image1, (320, 320))
    image_data = pytesseract.image_to_data(image1, output_type=pytesseract.Output.DATAFRAME)
    errors = []
    for word in textArr:
        result = image_data[image_data['text']==word]
        if len(result)>1:
            print("Number of instances of `"+word+"` is not unique")
            errors.append("Number of instances of `"+word+"` is not unique")
        elif len(result)==0:
            print("Cannot find `"+word)
            errors.append("Cannot find text: "+word)
        else:
            cv2.rectangle(image1, (result['left'],result['top']),(result['left']+result['width'],result['top']+result['height']),(0,255,0),-1)
            print("Masked "+word)
    retval, buffer = cv2.imencode('.jpg', image1)
    jpg_as_text = base64.b64encode(buffer)
    return jpg_as_text, errors




if __name__ == '__main__':
    pass
