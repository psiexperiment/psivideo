import logging.config

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


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser('psivideo')
    parser.add_argument('-s', '--source', default=0, type=int)
    parser.add_argument('-p', '--port', default=33331, type=int)
    parser.add_argument('--size', type=str)
    parser.add_argument('--writer', default='av', choices=['av', 'cv2'],
                        help='av compresses with H.265 while recording; '
                        'cv2 saves much larger Motion JPEG AVI files.')
    args = parser.parse_args()
    logging.config.dictConfig(log_config)
    # Before the video window exists, which is when Windows binds the process
    # to a taskbar button.
    set_app_id()
    video = Video(source=args.source, port=args.port, frame_size=args.size,
                  writer=args.writer)
    video.start()
    video.join()


if __name__ == '__main__':
    main()
