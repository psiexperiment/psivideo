import time
from psivideo import SyncVideoClient


def sync_test_client():
    with SyncVideoClient('ws://localhost:33331', True) as client:
        #time.sleep(5)
        #client.start('c:/users/lbhb/Desktop/test.avi')
        time.sleep(30)
        #for i in range(5):
        #    time.sleep(0.2)
        #    print(f'Frames written: {client.get_frames_written()}')
        client.stop()


if __name__ == '__main__':
    sync_test_client()
