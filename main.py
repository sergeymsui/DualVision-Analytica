
import gi
import cv2
import os
from os import listdir
from os.path import isfile, join

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject, GLib

image_width = 640
image_height = 512
stream_uri = "/video_stream"
images = []

# Sensor Factory class which inherits the GstRtspServer base class and add
# properties to it.
class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, **properties):
        super(SensorFactory, self).__init__(**properties)
        
        self.images = []
        self.load_images()
        print("== upload ==")
        
        self.frame_pointer = 0
        self.number_frames = 0
        self.fps = 30
        
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96' \
                             .format(image_width, image_height, self.fps)
        
    def load_images(self):
        path = 'RGB'
        onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
        file_paths = [str(n) for n in onlyfiles]
        file_paths.sort()

        os.chdir(path)

        max_items = 300
        for image in file_paths:
            self.images.append(cv2.imread(image))
            if len(self.images) > max_items:
                break

    # method to capture the video feed from the camera and push it to the
    # streaming buffer.
    def on_need_data(self, src, length):
        self.frame_pointer = self.frame_pointer + 1 if self.frame_pointer < len(self.images)-1 else 0
        frame = self.images[self.frame_pointer]
        # It is better to change the resolution of the camera 
        # instead of changing the image shape as it affects the image quality.
        frame = cv2.resize(frame, (image_width, image_height), interpolation = cv2.INTER_LINEAR)

        data = frame.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        buf.duration = self.duration
        timestamp = self.number_frames * self.duration
        buf.pts = buf.dts = int(timestamp)
        buf.offset = timestamp
        self.number_frames += 1
        frame_counter = self.number_frames
        retval = src.emit('push-buffer', buf)
        print('pushed buffer, frame {}, duration {} ns, durations {} s'.format(self.number_frames,
                                                                                       self.duration,
                                                                                       self.duration / Gst.SECOND))

        if retval != Gst.FlowReturn.OK:
            print(retval)

        if frame_counter % 60 == 0: 
            raw_data_location = frame
            raw_data_extension = ".jpg"

            # replace * with your model version number for inference
            inference_endpoint = ["obs-3", 16]
            upload_destination = "obs-3"

                #     conditionals = {
                #         "required_objects_count" : 0,
                #         "required_class_count": 0,
                #         "target_classes": [],
                #         "minimum_size_requirement" : float('-inf'),
                #         "maximum_size_requirement" : float('inf'),
                #         "confidence_interval" : [10,90],
                #     }


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
    def __init__(self, **properties):
        super(GstServer, self).__init__(**properties)
        self.factory = SensorFactory()
        self.factory.set_shared(True)
        self.set_service(str(8554))
        self.get_mount_points().add_factory(stream_uri, self.factory)
        self.attach(None)

def main():
    GObject.threads_init()
    Gst.init(None)
    server = GstServer()
    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()