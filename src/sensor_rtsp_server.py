
import gi
import cv2
import os
from os import listdir
from os.path import isfile, join

import threading
from threading import Lock

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject, GLib


frame_number = 0
mutex = Lock()

# Sensor Factory class which inherits the GstRtspServer base class and add
# properties to it.
class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, path, **properties):
        super(SensorFactory, self).__init__(**properties)
        
        self.path = path
        self.number_frames = 0
        self.fps = 10

        self.image_width = 640
        self.image_height = 512
        
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds        
        self.launch_string = 'appsrc name=source is-live=true block=false format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96' \
                             .format(self.image_width, self.image_height, self.fps)
        
    def load(self):
        onlyfiles = [f for f in listdir(self.path) if isfile(join(self.path, f))]
        file_paths = [str(n) for n in onlyfiles]
        file_paths.sort()

        os.chdir(self.path)

        self.images = []
        for image in file_paths:
            self.images.append(cv2.imread(image))
            if len(self.images) > 300:
                break

        return self

    # method to capture the video feed from the camera and push it to the
    # streaming buffer.
    def on_need_data(self, src, length):

        mutex.acquire()

        global frame_number
        frame_pointer = frame_number - (300 * int(frame_number/300))
        frame_number = frame_number + 1

        mutex.release()

        # self.frame_pointer = self.frame_pointer + 1 if self.frame_pointer < len(self.images)-1 else 0
        frame = self.images[frame_pointer]

        # It is better to change the resolution of the camera 
        # instead of changing the image shape as it affects the image quality.
        frame = cv2.resize(frame, (self.image_width, self.image_height), interpolation = cv2.INTER_AREA)

        data = frame.tobytes()
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


# Rtsp server implementation where we attach the factory sensor with the stream uri
class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, port, refs, **properties):
        super(GstServer, self).__init__(**properties)

        for it in refs:
            stream_url = it['url']
            stream_path = it['path']

            self.factory = SensorFactory(stream_path).load()
            self.factory.set_shared(True)
            self.get_mount_points().add_factory(stream_url, self.factory)
        
        self.set_service(port)
        self.attach(None)
        
        