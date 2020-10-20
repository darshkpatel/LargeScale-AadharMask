import numpy as np
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol

def masker(img):
    # Load image
    # img = cv2.imread('uma.jpeg')
    print('Masking QRCode')
    img = cv2.imencode('.png', img)[1].tostring()
    npimg = np.fromstring(img, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
	# original = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9,9), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Morph close
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find contours and filter for QR code
    cnts = cv2.findContours(close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        x,y,w,h = cv2.boundingRect(approx)
        area = cv2.contourArea(c)
        ar = w / float(h)
        if len(approx) == 4 and area > 1000 and (ar > .85 and ar < 1.3):
            isd = cv2.rectangle(img, (x, y), (x + w, y + h), (36,255,12), -1)
            # ROI = original[y:y+h, x:x+w]
	        # cv2.imwrite(img, isd)
            return isd


def process(img):
	"""
	Reads from a 'Image String' , extracts and processes the qr code, returns qrcode data or False
	"""
	
	#image = cv2.imread("1.jpg")
	# npimg = np.fromstring(img, np.uint8)
	# img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
	img = masker(img)
	return img

