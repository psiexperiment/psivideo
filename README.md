Installing 
----------

Clone the Git repository and then use pip:

    git clone git@github.com:psiexperiment/psivideo
    pip install -e ./psivideo

This should automatically pull all dependencies you need (including OpenCV, PyAV, and websockets).

Running
-------

This comes with both the server and client. You'll primarily be working with the client. To test the client, run either `demo_sync_client.py` or `demo_async_client.py` in the `scripts` folder.

To quit, select the video window and hit thq "q" key.

To run the server without opening a console window (on Windows), launch it with `psivideow` instead of `psivideo`. Since there is no console, the log is written to `psivideo.log` in the system temp folder (override with `--log-file`). When the client launches the server, pass `console=False` to `VideoClient` to do the same.

Recording from psiexperiment
----------------------------

Add `psivideo.plugin.PSIVideo` to a paradigm to save the video (`recording.mp4`, or `recording.avi` with `--writer cv2`) to the experiment folder, along with `recording_timestamp.csv`, which logs the video frame number and timestamp against the experiment clock once a second. Install with `pip install psivideo[psi]`. The plugin connects to a server that is already running; it does not start one, so start `psivideo` (or `psivideow`) before the experiment. Use `port` and `filename` to record from more than one camera.

Design
------

Five separate threads are used for running the server:

* Video capture. This is very simple and just grabs the next image from the camera and puts it into thread-safe queue that is read by the video process thread.
* Video process. This currently just moves the image from the video processing queue to the video writing queue (if a client has requested the video be saved) as well as the online image display thread.
* Video display. This displays a small window on the screen. This is not necessarily updated at the same rate as the video capture (it updates as fast as possible, but there may be dropped frames). 
* Video write. This compresses the video with H.265 (equivalent to `ffmpeg -vcodec libx265 -crf 28`) as it records and saves it to an MP4 file. Run with `--writer cv2` to save Motion JPEG AVI files instead (much larger).
* Video communication. This listens for incoming connections from a websocket client on port 33331. Payload is json.

Want to customize the program? 

To add new processing features, overide `Video.process` to do what you want. Be sure to check the camera frame rate before and after implementing your changes. If the frame rate drops once the changes are made, you need to set up the capture process to run in a separate process (rather than thread).
