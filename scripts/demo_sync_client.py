import time
from psivideo import SyncVideoClient


def sync_test_client():
    with SyncVideoClient('ws://localhost:33331', True) as client:
        time.sleep(2)
        client.start('c:/users/lbhb/Desktop/test.avi')
        while True:
            time.sleep(1)
            print(client.get_frames_written())



if __name__ == '__main__':
    sync_test_client()
