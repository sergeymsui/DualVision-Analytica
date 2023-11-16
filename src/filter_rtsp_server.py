
import gi
import cv2
import os
from os import listdir
from os.path import isfile, join

stream_uri = "/filter_stream"

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject, GLib

# Sensor Factory class which inherits the GstRtspServer base class and add
# properties to it.
class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, **properties):
        super(SensorFactory, self).__init__(**properties)
        
        self.cap_rgb = cv2.VideoCapture("rtsp://localhost:8554/video_stream")
        self.cap_tcm = cv2.VideoCapture("rtsp://localhost:8554/thermal_stream")

        self.number_frames = 0
        self.fps = 10

        self.image_width = 640
        self.image_height = 512

        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96' \
                             .format(self.image_width, self.image_height, self.fps)

    # method to capture the video feed from the camera and push it to the
    # streaming buffer.
    def on_need_data(self, src, length):
        ret, frame_rgb = self.cap_rgb.read()
        ret, frame_tcm = self.cap_tcm.read()
        # It is better to change the resolution of the camera 
        # instead of changing the image shape as it affects the image quality.
                
        frame_rgb = cv2.resize(frame_rgb, (self.image_width, self.image_height), interpolation = cv2.INTER_LINEAR)
        frame_tcm = cv2.resize(frame_tcm, (self.image_width, self.image_height), interpolation = cv2.INTER_LINEAR)

        gray_frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2HLS)

        # gray_frame_tcm = cv2.cvtColor(frame_tcm, cv2.COLOR_BGR2LUV)

        # result_frame = cv2.add(gray_frame_rgb, gray_frame_tcm)

        data = gray_frame_rgb.tobytes()

        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        buf.duration = self.duration
        timestamp = self.number_frames * self.duration
        buf.pts = buf.dts = int(timestamp)
        buf.offset = timestamp
        self.number_frames += 1
        retval = src.emit('push-buffer', buf)
        print('pushed buffer, frame {}, duration {} ns, durations {} s'.format(self.number_frames,
                                                                                       self.duration,
                                                                                       self.duration / Gst.SECOND))
        if retval != Gst.FlowReturn.OK:
            print(retval)

    # attach the launch string to the override method
    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)
    
    # attaching the source element to the rtsp media
    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)

class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, port, **properties):
        super(GstServer, self).__init__(**properties)
        self.factory = SensorFactory()
        self.factory.set_shared(True)
        self.set_service(port)
        self.get_mount_points().add_factory(stream_uri, self.factory)
        self.attach(None)

