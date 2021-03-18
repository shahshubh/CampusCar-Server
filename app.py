from flask import Flask,request,jsonify
import cv2
# from matplotlib import pyplot as plt
from PIL import Image
import pytesseract

import imutils
import numpy as np
import os
import glob

app=Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe'
# pytesseract.pytesseract.tesseract_cmd = '/app/.apt/usr/bin/tesseract'

@app.route('/')
def welcome():
    # img = cv2.imread("./images/vietnam_car_rectangle_plate.jpg");
    # text = pytesseract.image_to_string(img, config='--psm 13')
    return jsonify(welcome = "Welcome to Campus Car Server");

@app.route("/upload",methods=['POST'])
def upload():
    target = os.path.join(APP_ROOT, 'images/')
    if not os.path.isdir(target):
        os.mkdir(target)
    else:
        print("Couldn't create upload directory: {}".format(target))

    if request.files:
        img = request.files["image"]
        filename = img.filename

        destination = "/".join([target, filename])
        img.save(destination)
        img = cv2.imread(destination);
        os.remove(destination);

        img = cv2.resize(img, (600,400) )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
        gray = cv2.bilateralFilter(gray, 13, 15, 15) 

        edged = cv2.Canny(gray, 30, 200) 
        contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        
        contours = sorted(contours, key = cv2.contourArea, reverse = True)[:10]

        screenCnt = None
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
            if len(approx) == 4:
                screenCnt = approx
                break

        if screenCnt is None:
            detected = 0
            return jsonify({'success': False, 'error': "Something went wrong. No License Plate detected !!"});
        else:
            cv2.drawContours(img, [screenCnt], -1, (0, 0, 255), 3)
            
            mask = np.zeros(gray.shape,np.uint8)
            new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
            new_image = cv2.bitwise_and(img,img,mask=mask)

            (x, y) = np.where(mask == 255)
            (topx, topy) = (np.min(x), np.min(y))
            (bottomx, bottomy) = (np.max(x), np.max(y))
            Cropped = gray[topx:bottomx+1, topy:bottomy+1]

            # new_cropped, img_bin = cv2.threshold(Cropped,128,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            # new_cropped = cv2.bitwise_not(img_bin)
            # cv2.imwrite(destination, new_cropped)


            text = pytesseract.image_to_string(Cropped, config='--psm 11', lang='eng')
            text = text.strip()

            print("Before Detected license plate Number is:",text)

            getVals = list([val for val in text if val.isalpha() or val.isnumeric()]) 
            text = "".join(getVals)

            print("Detected license plate Number is:",text)
            if(len(text) <= 4):
                return jsonify({ 'success': False, 'error': "Something went wrong. No License Plate detected. Text Detected = " + text + " !!" })
            return jsonify({ 'success': True, 'license_plate': text })
    else:
        return jsonify({'success': False,'error': "Please send some Image File"});

if __name__=='__main__':
    app.run(debug=True,host="localhost",port='3000')
    # 192.168.0.105