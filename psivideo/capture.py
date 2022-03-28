import cv2
import time


def video_capture(video):
    '''
    Function to execute in a thread that captures video. Basic tests suggest
    threading is enough and we do not need to go to multiprocessing for speed.
    '''
    stream = cv2.VideoCapture(video.source)

    # For some reason, first capture is very slow. Let's just grab and discard
    # the frame to get it out of the way.
    stream.read()

    # We need to track the actual capture time since the rate is a bit
    # variable. The video muxer we use can handle variable framerates. t0 is
    # time since the beginning of the video. t1 is the time of the current
    # frame. t2 is used to track the approximate frame rate.
    t1 = t0 = time.time()
    while True:
        try:
            grabbed, frame = stream.read()
            t2 = time.time()
            if not grabbed:
                # Something is wrong with the video camera interface
                break
            if video.stop.is_set():
                # Time to stop the video
                break

            # This will be shown as the online video. The `new_frame` event
            # will notify the video thread to update the image. 
            video.current_frame = frame
            video.new_frame.set()

            # If recording, send to the write thread for saving to disk.
            if video.recording.is_set():
                video.frames_captured += 1
                video.write_queue.put_nowait((t2-t0, frame))

            if (video.frames_captured % 500) == 0:
                fps = 500 / (t2-t1)
                t1 = t2
                print(f'Estimated FPS: {fps:.0f}')

        except Exception as e:
            # Notify other threads that it's time to stop.
            video.stop.set()
            raise

    fps = video.frames_captured / (t2-t0)
    print(f'Captured {video.frames_captured} frames. Estimated capture rate was {fps:.0f} FPS')
