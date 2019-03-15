import cv2
import numpy as np
import easygui

#shows image and hold window open
def showImage(title, image, hold):
    cv2.imshow(title, image)

    if hold == 1:
        cv2.waitKey(0)
    else:
        return

# file = easygui.fileopenbox()
feed = cv2.VideoCapture(0)

#background = None
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(5,5))
mog = cv2.bgsegm.createBackgroundSubtractorMOG()
mog2 = cv2.createBackgroundSubtractorMOG2()
gmg = cv2.bgsegm.createBackgroundSubtractorGMG()
structEl1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
structEl2 = cv2.getStructuringElement(cv2.MORPH_RECT, (30,30))


while feed.isOpened():
    check, frame = feed.read()

    if check:
        # if background is None:
        #     cv2.imshow("Press enter to capture background", frame)
        #     key = cv2.waitKey(1)
            
        #     if key == 13:
        #         background = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #         blurred = cv2.GaussianBlur(background, (5,5), 0)

        #         background = clahe.apply(blurred)
        #         # background = process(frame)
        #         # y, u, v = cv2.split(frame)
        #         # showImage("Y", y, 1)
        #         # showImage("U", u, 1)
        #         # showImage("V", v, 1)
        #         cv2.destroyAllWindows()

        # else:
            # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # #processed = process(frame)

            # blurred = cv2.GaussianBlur(gray, (5,5), 0)

            # equalized = clahe.apply(blurred)

            # diff = cv2.absdiff(equalized, background)
            # _, binary = cv2.threshold(diff, 65, 255, cv2.THRESH_BINARY)
            # structEl = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))

            # #eroded = cv2.erode(binary, structEl, 5)

        orig1 = frame.copy()
        orig2 = frame.copy()
        orig3 = frame.copy()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (19, 19), 0)
        # frame = clahe.apply(frame)

        mask1 = mog.apply(frame)
        mask2 = mog2.apply(frame)
        mask3 = gmg.apply(frame)

        mask1 = cv2.morphologyEx(mask1, cv2.MORPH_OPEN, structEl1)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, structEl1)
        mask3 = cv2.morphologyEx(mask3, cv2.MORPH_OPEN, structEl1)

        mask1 = cv2.morphologyEx(mask1, cv2.MORPH_GRADIENT, structEl1)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_GRADIENT, structEl1)
        mask3 = cv2.morphologyEx(mask3, cv2.MORPH_GRADIENT, structEl1)

        mask1 = cv2.morphologyEx(mask1, cv2.MORPH_CLOSE, structEl2)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, structEl2)
        mask3 = cv2.morphologyEx(mask3, cv2.MORPH_CLOSE, structEl2)


        cv2.imshow("mogmask", mask1)
        cv2.imshow("mog2mask", mask2)
        cv2.imshow('gmgmask', mask3)


        h, w, c = np.shape(orig1)
        minArea = (h*w) * 0.0075
        print(minArea)


        top = 5

        contours, _ = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea)
        for contour in contours:
            if cv2.contourArea(contour) > minArea:
                print(cv2.contourArea(contour))
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(orig1, (x,y), (x+w, y+h), (0,255,0), 2)

            top -= 1

            if top == 0:
                break


        contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea)
        top = 5
        for contour in contours:
            if cv2.contourArea(contour) > minArea:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(orig2, (x,y), (x+w, y+h), (0,255,0), 2)

            top -= 1

            if top == 0:
                break

        contours, _ = cv2.findContours(mask3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea)
        top = 5
        for contour in contours:
            if cv2.contourArea(contour) > minArea:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(orig3, (x,y), (x+w, y+h), (0,255,0), 2)

            top -= 1

            if top == 0:
                break
        
        
        cv2.imshow("mog", orig1)
        cv2.imshow("mog2", orig2)
        cv2.imshow('gmg', orig3)
        cv2.waitKey(1)






