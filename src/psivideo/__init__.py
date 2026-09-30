import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

from .client import VideoClient, SyncVideoClient
