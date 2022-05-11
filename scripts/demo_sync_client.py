import time
from psivideo import SyncVideoClient


def sync_test_client():
    with SyncVideoClient('ws://localhost:33331', True) as client:
        client.start('c:/users/lbhb/Desktop/test.avi')
        for i in range(5):
            time.sleep(5)
            print(f'Frames written: {client.get_timing()}')
        client.stop()


if __name__ == '__main__':
    sync_test_client()
