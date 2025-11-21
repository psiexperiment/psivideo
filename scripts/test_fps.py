import cv2
import sys
import time

# Use DirectShow as established
stream = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Optional: Force MJPG and high res to test bandwidth
# stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

fps = stream.get(cv2.CAP_PROP_FPS)
w = stream.get(cv2.CAP_PROP_FRAME_WIDTH)
h = stream.get(cv2.CAP_PROP_FRAME_HEIGHT)
# Get the packed integer
icodec = int(stream.get(cv2.CAP_PROP_FOURCC))
codec = icodec.to_bytes(4, byteorder=sys.byteorder).decode()

print(f'{w}x{h} at {fps} Hz, {codec}')

prev_frame_time = None
new_frame_time = 0

while True:
    ret, frame = stream.read()
    if not ret:
        break

    new_frame_time = time.time()
    if prev_frame_time is None:
        prev_frame_time = new_frame_time
        continue

    fps = int(1 / (new_frame_time - prev_frame_time))
    prev_frame_time = new_frame_time
    cv2.putText(frame, f"FPS: {fps}", (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 3,
                (100, 255, 0), 3, cv2.LINE_AA)
    cv2.imshow('FPS Test', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

stream.release()
cv2.destroyAllWindows()
