from psivideo import VideoClient
import asyncio


async def async_test_client():
    async with VideoClient('ws://localhost:33331') as client:
        await client.start('c:/users/lbhb/Desktop/test.avi')
        while True:
            await asyncio.sleep(1)
            print(await client.get_frames_written())


if __name__ == '__main__':
    asyncio.run(async_test_client())
