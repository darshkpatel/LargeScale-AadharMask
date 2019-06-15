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

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", type=str, help="path to input image")
ap.add_argument(
    "-east", "--east", type=str, help="path to input EAST text detector")
ap.add_argument(
    "-c",
    "--min-confidence",
    type=float,
    default=0.5,
    help="minimum probability required to inspect a region")
ap.add_argument(
    "-w",
    "--width",
    type=int,
    default=320,
    help="resized image width (should be multiple of 32)")
ap.add_argument(
    "-e",
    "--height",
    type=int,
    default=320,
    help="resized image height (should be multiple of 32)")
args = vars(ap.parse_args())
image = cv2.imread(args["image"])
def identify_blobs():
    global image

    orig = image.copy()
    (H, W) = image.shape[:2]

    (newW, newH) = (args["width"], args["height"])
    rW = W / float(newW)
    rH = H / float(newH)

    image = cv2.resize(image, (newW, newH))
    (H, W) = image.shape[:2]
    layerNames = ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"]

    print("[INFO] loading EAST text detector...")
    net = cv2.dnn.readNet(args["east"])

    blob = cv2.dnn.blobFromImage(
        image, 1.0, (W, H), (123.68, 116.78, 103.94), swapRB=True, crop=False)
    start = time.time()
    net.setInput(blob)
    (scores, geometry) = net.forward(layerNames)
    end = time.time()

    print("[INFO] text detection took {:.6f} seconds".format(end - start))

    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    for y in range(0, numRows):

        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(0, numCols):

            if scoresData[x] < args["min_confidence"]:
                continue

            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
    boxes = non_max_suppression(np.array(rects), probs=confidences)

    for (startX, startY, endX, endY) in boxes:

        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)

    # cv2.imshow('test',orig)
    # cv2.waitKey(0)

    return boxes

def censor(boxes):
    rois= []
    global image
    (H, W) = image.shape[:2]
    # copy_img = image.copy()

    (newW, newH) = (args["width"], args["height"])
    rW = W / float(newW)
    rH = H / float(newH)

    digits = datasets.load_digits()
    features = digits.data
    labels = digits.target

    clf = SVC(gamma = 0.001)
    clf.fit(features, labels)
    for (startX, startY, endX, endY) in boxes:

        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        temp = image[startY:endY,startX:endX]
        # gray = cv2.cvtColor(temp, cv2.COLOR_BGR2GRAY)

        # gray = cv2.threshold(gray, 0, 255,
            # cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # gray = cv2.medianBlur(gray, 3)

        text = pytesseract.image_to_string(temp,lang='eng',
           config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
        print(text)

        cv2.imshow('test',temp)
        cv2.waitKey(0)
        # break
        chk = [x.isdigit() for x in list(text)].count(True)
        if chk>1:

            rois.append((startX,startY,endX,endY))


    for a in rois:
        cv2.rectangle(image, (a[0], a[1]), (a[2], a[3]), (0, 255, 0), -1)

    cv2.imshow('aad',image)
    cv2.waitKey(0)


def pdf_to_img():
    pages = convert_from_path('test.pdf', 500)
    for page in pages:
        image = Image.frombytes('RGBA', (128,128), page, 'raw')


# censor(identify_blobs())
# identify_blobs()
pdf_to_img()
