import gi
import cv2
import argparse
import os 
import re

# import required library like Gstreamer and GstreamerRtspServer
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

parser = argparse.ArgumentParser()
parser.add_argument("--fps", default=30, required=False, help="fps of the camera", type=int)
parser.add_argument("--image_width", default=400, required=False, help="video frame width", type=int)
parser.add_argument("--image_height", default=300, required=False, help="video frame height", type=int)
parser.add_argument("--port", default=8554, help="port to stream video", type=int)
parser.add_argument("--urls", nargs='+', help="additional URLs along with width and height", default=[])

# Replace hardcoded values with calls to os.getenv()
# parser.add_argument("--fps", default=os.getenv('FPS', 30), required=False, help="fps of the camera", type=int)
# parser.add_argument("--image_width", default=os.getenv('IMAGE_WIDTH', 400), required=False, help="video frame width", type=int)
# parser.add_argument("--image_height", default=os.getenv('IMAGE_HEIGHT', 300), required=False, help="video frame height", type=int)
# parser.add_argument("--port", default=os.getenv('PORT', 8554), help="port to stream video", type=int)
# parser.add_argument("--urls", nargs='+', help="additional URLs along with width and height", default=os.getenv('URLS', []))


opt = parser.parse_args()

class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, video_source, image_width = opt.image_width, image_height = opt.image_height, fps=opt.fps, **properties):
        super(SensorFactory, self).__init__(**properties)
        self.video_source = video_source
        self.image_width = image_width
        self.image_height = image_height
        self.cap = cv2.VideoCapture(self.video_source)  # Change to read from file
        self.number_frames = 0
        self.frame_counter = 0
        self.fps = fps
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96' \
                             .format(self.image_width, self.image_height, self.fps)
                             
    def on_need_data(self, src, length):
        if(self.cap.isOpened()):
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (self.image_width, self.image_height), interpolation=cv2.INTER_LINEAR)
                data = frame.tostring()
                buf = Gst.Buffer.new_allocate(None, len(data), None)
                buf.fill(0, data)
                buf.duration = self.duration
                timestamp = self.number_frames * self.duration
                buf.pts = buf.dts = int(timestamp)
                self.number_frames += 1
                self.frame_counter += 1
                retval = src.emit('push-buffer', buf)

                if (self.frame_counter == self.cap.get(cv2.CAP_PROP_FRAME_COUNT)):
                    self.frame_counter = 0
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            
    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)
    
    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)

class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, **properties):
        super(GstServer, self).__init__(**properties)
        self.set_service(str(opt.port))
        self.attach(None)
        self.create_streams_from_dir("videos")

    def create_streams_from_dir(self, videos_folder):
        video_files = [f for f in os.listdir(videos_folder) if f.endswith('.mp4')]
     
        for video_file in video_files:
            # Check if video_file name is in the format title_width_height.mp4
            # if yes, extract the title, width and height
            match = re.match(r'^(.+?)_(\d+)_(\d+)\.mp4$', video_file)
            if match:
                title, width, height = match.groups()
                factory = SensorFactory(os.path.join(videos_folder, video_file), int(width), int(height))

            else:
                factory = SensorFactory(os.path.join(videos_folder, video_file))        
            print(f"Video {video_file} is stream at rtsp://localhost:{opt.port}/{video_file.replace('.mp4', '')}")
            factory.set_shared(True)
            self.get_mount_points().add_factory(f"/{video_file.replace('.mp4', '')}", factory)

    def add_cam_stream(self, image_width = opt.image_width, image_height = opt.image_height, fps=opt.fps):
        cam_factory = SensorFactory(0, image_width, image_height, fps)        
        cam_factory.set_shared(True)
        self.get_mount_points().add_factory(f"/cam_stream", cam_factory)

    def add_stream_from_url(self, url, stream_uri, image_width = opt.image_width, image_height = opt.image_height, fps=opt.fps):
        if (url.startswith("device")):
            url = int(url.split(".")[1])
        cam_factory = SensorFactory(url, image_width, image_height, fps)        
        cam_factory.set_shared(True)
        print(f"URL {url} is stream at rtsp://localhost:{opt.port}/{stream_uri}")
        self.get_mount_points().add_factory(f"/{stream_uri}", cam_factory)
        
GObject.threads_init()
Gst.init(None)
server = GstServer()

for url_info in opt.urls:
    parts = url_info.split(',')
    if len(parts) == 4:
        url, stream_uri, width, height = parts
        server.add_stream_from_url(url, stream_uri, int(width), int(height))
    else:
        print("Invalid format for additional URL info:", url_info)
# server.add_cam_stream()
loop = GObject.MainLoop()
loop.run()

# Example execute command: python3 stream.py --urls "device.0,cam_stream,640,480" "rtsp://192.168.1.5,stream_1,640,480"
import gi
import cv2
import argparse
import os 
import re

# import required library like Gstreamer and GstreamerRtspServer
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

parser = argparse.ArgumentParser()
parser.add_argument("--fps", default=30, required=False, help="fps of the camera", type=int)
parser.add_argument("--image_width", default=400, required=False, help="video frame width", type=int)
parser.add_argument("--image_height", default=300, required=False, help="video frame height", type=int)
parser.add_argument("--port", default=8554, help="port to stream video", type=int)
parser.add_argument("--urls", nargs='+', help="additional URLs along with width and height", default=[])

opt = parser.parse_args()

class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, video_source, image_width = opt.image_width, image_height = opt.image_height, fps=opt.fps, **properties):
        super(SensorFactory, self).__init__(**properties)
        self.video_source = video_source
        self.image_width = image_width
        self.image_height = image_height
        self.cap = cv2.VideoCapture(self.video_source)  # Change to read from file
        self.number_frames = 0
        self.frame_counter = 0
        self.fps = fps
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96' \
                             .format(self.image_width, self.image_height, self.fps)
                             
    def on_need_data(self, src, length):
        if(self.cap.isOpened()):
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (self.image_width, self.image_height), interpolation=cv2.INTER_LINEAR)
                data = frame.tostring()
                buf = Gst.Buffer.new_allocate(None, len(data), None)
                buf.fill(0, data)
                buf.duration = self.duration
                timestamp = self.number_frames * self.duration
                buf.pts = buf.dts = int(timestamp)
                self.number_frames += 1
                self.frame_counter += 1
                retval = src.emit('push-buffer', buf)

                if (self.frame_counter == self.cap.get(cv2.CAP_PROP_FRAME_COUNT)):
                    self.frame_counter = 0
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            
    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)
    
    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)

class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, **properties):
        super(GstServer, self).__init__(**properties)
        self.set_service(str(opt.port))
        self.attach(None)
        self.create_streams_from_dir("videos")

    def create_streams_from_dir(self, videos_folder):
        video_files = [f for f in os.listdir(videos_folder) if f.endswith('.mp4')]
     
        for video_file in video_files:
            # Check if video_file name is in the format title_width_height.mp4
            # if yes, extract the title, width and height
            match = re.match(r'^(.+?)_(\d+)_(\d+)\.mp4$', video_file)
            if match:
                title, width, height = match.groups()
                factory = SensorFactory(os.path.join(videos_folder, video_file), int(width), int(height))

            else:
                factory = SensorFactory(os.path.join(videos_folder, video_file))        
            print(f"Video {video_file} is stream at rtsp://localhost:{opt.port}/{video_file.replace('.mp4', '')}")
            factory.set_shared(True)
            self.get_mount_points().add_factory(f"/{video_file.replace('.mp4', '')}", factory)

    def add_cam_stream(self, image_width = opt.image_width, image_height = opt.image_height, fps=opt.fps):
        cam_factory = SensorFactory(0, image_width, image_height, fps)        
        cam_factory.set_shared(True)
        self.get_mount_points().add_factory(f"/cam_stream", cam_factory)

    def add_stream_from_url(self, url, stream_uri, image_width = opt.image_width, image_height = opt.image_height, fps=opt.fps):
        if (url.startswith("device")):
            url = int(url.split(".")[1])
        cam_factory = SensorFactory(url, image_width, image_height, fps)        
        cam_factory.set_shared(True)
        print(f"URL {url} is stream at rtsp://localhost:{opt.port}/{stream_uri}")
        self.get_mount_points().add_factory(f"/{stream_uri}", cam_factory)


if __name__ == "__main__":
 
    GObject.threads_init()
    Gst.init(None)
    server = GstServer()

    for url_info in opt.urls:
        parts = url_info.split(',')
        if len(parts) == 4:
            url, stream_uri, width, height = parts
            server.add_stream_from_url(url, stream_uri, int(width), int(height))
        else:
            print("Invalid format for additional URL info:", url_info)
    # server.add_cam_stream()
    loop = GObject.MainLoop()
    loop.run()

# Example execute command: python3 stream.py --urls "device.0,cam_stream,640,480" "rtsp://192.168.1.5,stream_1,640,480"
