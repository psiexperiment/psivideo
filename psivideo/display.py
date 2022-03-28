import cv2


def video_display(video):
    while not video.stop.is_set():
        try:
            if video.new_frame.wait(1):
                cv2.imshow('Video', video.current_frame)
                video.new_frame.clear()
                if cv2.waitKey(1) == ord('q'):
                    video.stop.set()
        except:
            video.stop.set()
            raise

    cv2.destroyAllWindows()
    print('Exiting show thread')
