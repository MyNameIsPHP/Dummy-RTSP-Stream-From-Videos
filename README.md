# Dummy-RTSP-Stream-From-Videos
Create dummy RTSP streams from video files in the "videos" directory with the GStreamer library in Python 

Dev environment:
- Ubuntu 22.04 LTS
- Python 3.9

If you are using Ubuntu 22.04, you can run the code directly by just installing the requirements as in the Dockerfile. 

For GStreamer unsupported OS such as Windows, install Docker and run the following command:
```
docker build -t php/dummy_rtsp_stream .
docker run -itd -v "$PWD/videos":/app/videos -p 8554:8554 php/dummy_rtsp_stream
```
The RTSP links are generated in the format `rtsp://localhost:8554/<video_filename>`. These links are also shown in the container log.

You can specify the width and height of the video stream by modifying the video filename to the format `title_width_height`, ex: `vid1_400_300.mp4`

You can use any VLC software to view the RTSP streams, or simply run the `python3 open_rtsp.py <url>` command to view the stream by URL. Example:
```
python3 open_rtsp.py rtsp://localhost:8554/vid8
```

I also provide a demo of Flask web application to display the video streams from the URLs.
```
python3 test_flask.py
```
