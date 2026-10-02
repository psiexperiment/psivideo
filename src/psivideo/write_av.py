from pathlib import Path

import av


# Equivalent to `ffmpeg -vcodec libx265 -crf 28` (ffmpeg's default preset is
# medium). Encoding is done on the fly, so no post-processing is needed.
CODEC = 'libx265'
CODEC_OPTIONS = {
    'crf': '28',
    'preset': 'medium',
    'x265-params': 'log-level=error',
}

# Fragmented MP4 writes the index as it goes rather than at the end, so the
# file is still readable (up to the last keyframe) if psivideo crashes.
CONTAINER_OPTIONS = {
    'movflags': 'frag_keyframe+empty_moov+default_base_moof',
}


def output_filename(filename, log):
    # AVI can't hold H.265, so switch to MP4.
    filename = Path(filename)
    if filename.suffix.lower() != '.mp4':
        new_filename = filename.with_suffix('.mp4')
        log.warning(f'Saving as {new_filename} rather than {filename} since '
                    f'{CODEC} requires an MP4 container.')
        filename = new_filename
    return str(filename)


class Writer:

    def __init__(self, filename, fps, width, height, log):
        filename = output_filename(filename, log)
        log.info(f'Recording to {filename}')
        self.container = av.open(filename, mode='w', options=CONTAINER_OPTIONS)
        try:
            self.stream = self.container.add_stream(CODEC, rate=fps,
                                                    options=CODEC_OPTIONS)
            self.stream.width, self.stream.height = width, height
            self.stream.pix_fmt = 'yuv420p'
        except:
            self.container.close()
            raise

    def write(self, pts, frame):
        frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
        frame.pts = pts
        self.container.mux(self.stream.encode(frame))

    def close(self):
        try:
            # Flush frames still buffered in the encoder.
            self.container.mux(self.stream.encode())
        finally:
            self.container.close()
