import logging.config
import os
from pathlib import Path
import sys
import tempfile

from .branding import set_app_id
from .video import Video


log_config = {
    'version': 1,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'websockets': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'psivideo': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
}


def main(default_log_file=None):
    from argparse import ArgumentParser
    parser = ArgumentParser('psivideo')
    parser.add_argument('-s', '--source', default=0, type=int)
    parser.add_argument('-p', '--port', default=33331, type=int)
    parser.add_argument('--size', type=str)
    parser.add_argument('--writer', default='av', choices=['av', 'cv2'],
                        help='av compresses with H.265 while recording; '
                        'cv2 saves much larger Motion JPEG AVI files.')
    parser.add_argument('-o', '--output', type=Path,
                        help='Start recording to this file as soon as the '
                        'camera starts (mainly for testing).')
    parser.add_argument('--log-file', type=Path, default=default_log_file,
                        help='Write the log to this file instead of the '
                        'console.')
    args = parser.parse_args()
    if args.log_file is not None:
        log_config['handlers']['console'] = {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(args.log_file),
            'mode': 'w',
            'encoding': 'utf-8',
        }
    logging.config.dictConfig(log_config)
    # Before the video window exists, which is when Windows binds the process
    # to a taskbar button.
    set_app_id()
    video = Video(source=args.source, port=args.port, frame_size=args.size,
                  writer=args.writer)
    video.start()
    if args.output is not None:
        video.handle_start(str(args.output))
    video.join()


def main_gui():
    '''
    Entry point for the psivideow GUI script, which runs under pythonw so no
    console window is created.
    '''
    # pythonw leaves these as None, so anything that writes to them (e.g.,
    # print) would raise.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    main(default_log_file=Path(tempfile.gettempdir()) / 'psivideo.log')


if __name__ == '__main__':
    main()
