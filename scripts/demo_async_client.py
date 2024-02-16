from psivideo import VideoClient
import asyncio


async def async_test_client():
    async with VideoClient(port=33332) as client:
        await client.start('c:/users/lbhb/Desktop/test.avi')
        for i in range(5):
            await asyncio.sleep(5)
            print(await client.get_frames_written())


if __name__ == '__main__':
    asyncio.run(async_test_client())
