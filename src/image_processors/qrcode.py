import numpy as np
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol

__all__ = ["order_points"]
def order_points(pts):
	# initialzie a list of coordinates that will be ordered
	# such that the first entry in the list is the top-left,
	# the second entry is the top-right, the third is the
	# bottom-right, and the fourth is the bottom-left
	rect = np.zeros((4, 2), dtype = "float32")

	# the top-left point will have the smallest sum, whereas
	# the bottom-right point will have the largest sum
	s = pts.sum(axis = 1)
	rect[0] = pts[np.argmin(s)]
	rect[2] = pts[np.argmax(s)]

	# now, compute the difference between the points, the
	# top-right point will have the smallest difference,
	# whereas the bottom-left will have the largest difference
	diff = np.diff(pts, axis = 1)
	rect[1] = pts[np.argmin(diff)]
	rect[3] = pts[np.argmax(diff)]

	# return the ordered coordinates
	return rect

def four_point_transform(image, pts):
	# obtain a consistent order of the points and unpack them
	# individually
	rect = order_points(pts)
	(tl, tr, br, bl) = rect

	# compute the width of the new image, which will be the
	# maximum distance between bottom-right and bottom-left
	# x-coordiates or the top-right and top-left x-coordinates
	widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
	widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
	maxWidth = max(int(widthA), int(widthB))

	# compute the height of the new image, which will be the
	# maximum distance between the top-right and bottom-right
	# y-coordinates or the top-left and bottom-left y-coordinates
	heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
	heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
	maxHeight = max(int(heightA), int(heightB))

	# now that we have the dimensions of the new image, construct
	# the set of destination points to obtain a "birds eye view",
	# (i.e. top-down view) of the image, again specifying points
	# in the top-left, top-right, bottom-right, and bottom-left
	# order
	dst = np.array([
		[0, 0],
		[maxWidth - 1, 0],
		[maxWidth - 1, maxHeight - 1],
		[0, maxHeight - 1]], dtype = "float32")

	# compute the perspective transform matrix and then apply it
	M = cv2.getPerspectiveTransform(rect, dst)
	warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

	# return the warped image
	return warped


def process(img):
	"""
	Reads from a 'Image String' , extracts and processes the qr code, returns qrcode data or False
	"""
	
	#image = cv2.imread("1.jpg")
	npimg = np.fromstring(img, np.uint8)
	image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	# equalize lighting
	clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
	gray = clahe.apply(gray)

	# edge enhancement
	edge_enh = cv2.Laplacian(gray, ddepth = cv2.CV_8U,
							ksize = 3, scale = 1, delta = 0)
	# bilateral blur, which keeps edges
	blurred = cv2.bilateralFilter(edge_enh, 13, 50, 50)
	# use simple thresholding. adaptive thresholding might be more robust
	(_, thresh) = cv2.threshold(blurred, 55, 255, cv2.THRESH_BINARY)
	# do some morphology to isolate just the barcode blob
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
	closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
	closed = cv2.erode(closed, None, iterations = 4)
	closed = cv2.dilate(closed, None, iterations = 4)
	# find contours left in the image
	(cnts, _) = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	for contour in sorted(cnts, key = cv2.contourArea, reverse = True):
		rect = cv2.minAreaRect(contour)
		box = np.int0(cv2.boxPoints(rect))
		cv2.drawContours(image, [box], -1, (0, 255, 0), 3)
		#retval = cv2.imwrite("found.jpg", image)
		warped = four_point_transform(image, box)
		decoded = decode(warped, symbols=[ZBarSymbol.QRCODE])
		if(decoded):
			return decoded[0].data
	return False

