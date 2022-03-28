import cv2 as cv
from time import time

feed = cv.VideoCapture(0)
for i in range(10):
    _ = feed.read()

for i in range(10):
    loop_start = time()
    for i in range(100):
        _ = feed.read()
    fps = 100/(time() - loop_start)
    print(f'FPS: {fps}')
