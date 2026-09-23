import logging
log = logging.getLogger(__name__)

from functools import partial
import time

import cv2


# Snapshot icon lives in the overlay bar, just left of the recording timer.
# Offsets are from the right edge of the frame.
SNAPSHOT_X_OFFSET = 130
SNAPSHOT_Y = 25
SNAPSHOT_HIT_HALF_WIDTH = 15
SNAPSHOT_HIT_HALF_HEIGHT = 14
SNAPSHOT_FLASH_DURATION = 0.5


def snapshot_icon_center(frame):
    return frame.shape[1] - SNAPSHOT_X_OFFSET, SNAPSHOT_Y


def draw_camera_icon(frame, color):
    x, y = snapshot_icon_center(frame)
    cv2.rectangle(frame, (x - 5, y - 9), (x + 2, y - 6), color, -1)
    cv2.rectangle(frame, (x - 11, y - 6), (x + 11, y + 8), color, -1)
    cv2.circle(frame, (x, y + 1), 5, (0, 0, 0), -1, cv2.LINE_AA)
    cv2.circle(frame, (x, y + 1), 3, color, 1, cv2.LINE_AA)


def snapshot_icon_color(video):
    if video.data_folder is None:
        return (110, 110, 110)
    t = video.last_snapshot_time
    if t is not None and (time.monotonic() - t) < SNAPSHOT_FLASH_DURATION:
        return (0, 200, 0)
    return (255, 255, 255)


def on_mouse(video, event, x, y, flags, param):
    if event != cv2.EVENT_LBUTTONDOWN or video.current_frame is None:
        return
    cx, cy = snapshot_icon_center(video.current_frame)
    if abs(x - cx) <= SNAPSHOT_HIT_HALF_WIDTH and \
            abs(y - cy) <= SNAPSHOT_HIT_HALF_HEIGHT:
        try:
            video.save_snapshot()
        except Exception as e:
            log.exception(e)


def video_display(video):
    cv2.namedWindow('Video')
    cv2.setMouseCallback('Video', partial(on_mouse, video))
    while not video.stop.is_set():
        try:
            if video.new_frame.wait(1):
                display_frame = video.current_frame.copy()
                width = display_frame.shape[1]
                if video.recording.is_set():
                    cv2.circle(display_frame, (width - 25, 25), 7, (0, 0, 255), -1)
                draw_camera_icon(display_frame, snapshot_icon_color(video))
                cv2.imshow('Video', display_frame)
                video.new_frame.clear()
                if cv2.waitKey(1) == ord('q'):
                    video.stop.set()
        except:
            video.stop.set()
            raise

    cv2.destroyAllWindows()
