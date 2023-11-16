
import os
import gi
from sensor_rtsp_server import GstServer

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GObject, GLib

def main():
    Gst.init(None)
    
    path_rgb = os.path.abspath("./data/RGB")
    path_tcm = os.path.abspath("./data/TCM")

    server_rgb = GstServer("8554", [
        {'url': '/video_stream', 'path': path_rgb},
        {'url': '/thermal_stream', 'path': path_tcm},
    ])

    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()