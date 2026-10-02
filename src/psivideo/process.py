import queue


def video_process(video):
    # Recording that frames are currently being sent to the writer for. This
    # thread is the only one feeding the writer, so tracking it here
    # guarantees the end-of-recording marker follows the recording's last
    # frame.
    session = None
    try:
        while True:
            try:
                ts, frame = video.process_queue.get(timeout=1)
            except queue.Empty:
                if video.stop.is_set():
                    break
                frame = None

            # Tell the writer when a recording ends so it can close the file
            # even if no more frames arrive. If a new recording started
            # without the old one being seen to stop, the writer notices the
            # session change instead.
            current = video.recording_session if video.recording.is_set() else None
            if session is not None and current is None:
                video.write_queue.put_nowait(None)
            session = current

            if frame is None:
                continue

            ts, frame = video.process_frame(ts, frame)

            # This will be shown as the online video. The `new_frame` event
            # will notify the video thread to update the image.
            video.current_ts = ts
            video.current_frame = frame
            video.new_frame.set()

            # If recording, send to the write thread for saving to disk.
            if session is not None:
                video.write_queue.put_nowait((session, ts, frame))
    except Exception as e:
        video.stop.set()
        raise
