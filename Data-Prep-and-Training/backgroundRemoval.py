import cv2
import numpy as np




def process(imgOrig):
    img = imgOrig.copy()

    #getting image parameters for use later
    h, w, c = np.shape(img)

    #convert to YUV color space so we can extract the luminance channel for equalizing
    yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    lum, u, v = cv2.split(yuv)

    #creating a contrast limited adaptive histogram equalization object
    k = (int(h*0.03), int(w*0.03))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=k)

    #apply clahe to luminance channel
    lumEqualized = clahe.apply(lum)

    #merge the equalized channel back with the rest
    merged = cv2.merge((lumEqualized, u, v))

    #convert it back to bgr
    bgr = cv2.cvtColor(merged, cv2.COLOR_YUV2BGR)

    #getting k size
    k = [int(h*0.02), int(w*0.02)]

    #error prevention, ensuring acceptable input for gaussian
    if k[0] % 2 != 1:
        k[0] += 1

    if k[1] % 2 != 1:
        k[1] += 1

    k = (k[0], k[1])
		
    #apply gaussain blur
    gaussian = cv2.GaussianBlur(bgr, k, 0)

    #apply bilateral filter, this won't scale well, need to find way to dynamically choose the parameters
    #I tried to base them on width, height and averages but couldn't find the right balance, needs more testing.
    biLat = cv2.bilateralFilter(bgr, 30, 30, 30)

    #bilateral filter leaves slightly too much blur, so take away a gaussian blur to sharpen slightly
    bgrSub = cv2.addWeighted(biLat, 1.5, gaussian, -0.5, 0)
    gray = cv2.cvtColor(bgrSub, cv2.COLOR_BGR2GRAY)

    #use Laplacian operator to bring out the edges
    grayLap = cv2.Laplacian(gray, cv2.CV_8U)

    #subtract the laplacian from the grayscale to clean up the image
    graySub = cv2.addWeighted(gray, 1.5, grayLap, -0.3, 0)
	
	# #show images at each step if user requested it
    # showImage("Luminance Channel Equalized", lumEqualized, 1)
    # showImage("Merged back with U and V", merged, 1)
    # showImage("Converted back to BGR", bgr, 1)
    # showImage("Gaussian blurred", gaussian, 1)
    # showImage("Bilateral Filters", biLat, 1)
    # showImage("Gaussian Blur(-0.3) subtracted from Bilater filter(1.5)", bgrSub, 1)
    # showImage("Converted to grayscale", gray, 1)
    # showImage("Laplacian Operator used on gray", grayLap, 1)
    # showImage("Laplacian subtracted from grayscale", graySub, 1)

    return graySub

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

        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #processed = process(frame)

            blurred = cv2.GaussianBlur(gray, (5,5), 0)

            equalized = clahe.apply(blurred)

            diff = cv2.absdiff(equalized, background)
            _, binary = cv2.threshold(diff, 75, 255, cv2.THRESH_BINARY)
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






