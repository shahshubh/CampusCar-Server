from flask_ngrok import run_with_ngrok
from flask import Flask,request,jsonify
import cv2
import pytesseract
import imutils
import numpy as np
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe'

app=Flask(__name__)
run_with_ngrok(app)

@app.route('/')
def welcome():
    return jsonify(welcome = "Welcome to Campus Car Server");

@app.route("/upload",methods=['POST'])
def upload():
    target = os.path.join(APP_ROOT, 'images/')
    if not os.path.isdir(target):
        os.mkdir(target)
    else:
        print("Couldn't create upload directory: {}".format(target))

    if request.files:
        img = request.files["upload"]
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

            getVals = list([val for val in text if val.isalpha() or val.isnumeric()]) 
            text = "".join(getVals)

            print("Detected license plate Number is:",text)
            if(len(text) <= 4):
                return jsonify({ 'success': False, 'error': "Something went wrong. No License Plate detected. Text Detected = " + text + " !!" })
            return jsonify({ 'success': True, 'license_plate': text })
    else:
        return jsonify({'success': False,'error': "Please send some Image File"});

if __name__=='__main__':
    app.run()