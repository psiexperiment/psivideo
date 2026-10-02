import cv2


class Writer:

    def __init__(self, filename, fps, width, height, log):
        frame_size = int(width), int(height)
        log.info(f'Recording to {filename} with fps {fps} and frame size {frame_size}')
        self.out = cv2.VideoWriter(filename,
                                   cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                   fps,
                                   frame_size)
        if not self.out.isOpened():
            raise IOError(f'Unable to open {filename} for writing')

    def write(self, pts, frame):
        self.out.write(frame)

    def close(self):
        self.out.release()
