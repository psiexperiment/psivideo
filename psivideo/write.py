def video_write(ctx, write_queue, recording, stop, log_cb, write_cb):
    while True:
        if recording.wait(0.1):
            write_cb(ctx, write_queue, recording, stop, log_cb)
            ctx.write_t0 = None
        if stop.is_set():
            return


