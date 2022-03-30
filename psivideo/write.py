from fractions import Fraction
import queue

import av


def video_write(video):
    while True:
        if video.recording.wait(0.1):
            break
        if video.stop.is_set():
            return

    # Ok, it's time to start writing video!
    try:
        print(f'Recording to {video.output_filename}')
        container = av.open(video.output_filename, mode='w')
        stream = container.add_stream('mpeg4', rate=24)
        stream.width, stream.height = 640, 480
        stream.codec_context.time_base = Fraction(1, 1000)

        while True:
            try:
                ts, frame = video.write_queue.get(timeout=1)
                video.frames_written += 1
                frame = av.VideoFrame.from_ndarray(frame[..., ::-1], format='rgb24')
                frame.pts = int(round(ts / stream.codec_context.time_base))
                for packet in stream.encode(frame):
                    container.mux(packet)
            except queue.Empty:
                if video.stop.is_set():
                    break
    except Exception as e:
        video.stop.set()
        raise
    finally:
        container.close()

    print(f'Wrote {video.frames_written} frames.')
