import cv2


def video_display(video):
    while not video.stop.is_set():
        try:
            if video.new_frame.wait(1):
                if video.recording.is_set():
                    display_frame = video.current_frame.copy()
                    width = display_frame.shape[1]
                    cv2.circle(display_frame, (width - 25, 25), 7, (0, 0, 255), -1)
                else:
                    display_frame = video.current_frame
                cv2.imshow('Video', display_frame)
                video.new_frame.clear()
                if cv2.waitKey(1) == ord('q'):
                    video.stop.set()
        except:
            video.stop.set()
            raise

    cv2.destroyAllWindows()
