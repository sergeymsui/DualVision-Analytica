
import os
import gi

from filter_rtsp_server import GstServer

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GObject, GLib

def main():
    Gst.init(None)

    server_rgb = GstServer("8557", '/video_stream')

    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()