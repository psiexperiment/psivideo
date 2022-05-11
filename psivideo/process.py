import queue


def video_process(video):
    try:
        while True:
            try:
                ts, frame = video.process_queue.get(timeout=1)
                ts, frame = video.process_frame(ts, frame)

                # This will be shown as the online video. The `new_frame` event
                # will notify the video thread to update the image. 
                video.current_frame = frame
                video.new_frame.set()

                # If recording, send to the write thread for saving to disk.
                if video.recording.is_set():
                    video.write_queue.put_nowait((ts, frame))

            except queue.Empty:
                if video.stop.is_set():
                    break
    except Exception as e:
        video.stop.set()
        raise
