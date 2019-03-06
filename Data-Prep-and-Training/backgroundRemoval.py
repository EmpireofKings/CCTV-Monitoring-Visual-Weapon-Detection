import cv2
import numpy as np

#shows image and hold window open
def showImage(title, image, hold):
    cv2.imshow(title, image)

    if hold == 1:
        cv2.waitKey(0)
    else:
        return

feed = cv2.VideoCapture(0)

background = None
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(5,5))

while feed.isOpened():
    check, frame = feed.read()

    if check:
        if background is None:
            cv2.imshow("Press enter to capture background", frame)
            key = cv2.waitKey(1)
            
            if key == 13:
                background = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(background, (5,5), 0)

                background = clahe.apply(blurred)
                # background = process(frame)
                # y, u, v = cv2.split(frame)
                # showImage("Y", y, 1)
                # showImage("U", u, 1)
                # showImage("V", v, 1)
                cv2.destroyAllWindows()

        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #processed = process(frame)

            blurred = cv2.GaussianBlur(gray, (5,5), 0)

            equalized = clahe.apply(blurred)

            diff = cv2.absdiff(equalized, background)
            _, binary = cv2.threshold(diff, 65, 255, cv2.THRESH_BINARY)
            structEl = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))

            #eroded = cv2.erode(binary, structEl, 5)
            
            opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, structEl)

            _, contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) > 0:
                largest = max(contours, key=cv2.contourArea)

                x, y, w, h = cv2.boundingRect(largest)
                cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            cv2.imshow("box", frame)
            cv2.waitKey(1)






