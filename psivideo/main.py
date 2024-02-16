import logging.config

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
    args = parser.parse_args()
    logging.config.dictConfig(log_config)
    video = Video(source=args.source, port=args.port)
    video.start()
    video.join()


if __name__ == '__main__':
    main()
