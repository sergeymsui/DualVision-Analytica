

import cv2
import gi

import numpy as np

from filter_rtsp_server import GstServer

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GObject, GLib


def main():
    # Gst.init(None)

    # server_rgb = GstServer("8557")

    # loop = GLib.MainLoop()
    # loop.run()

    capture_rgb = cv2.VideoCapture("rtsp://localhost:8554/video_stream")
    capture_tcm = cv2.VideoCapture("rtsp://localhost:8554/thermal_stream")

    while(True):
        ret, frame_rgb = capture_rgb.read()
        ret, frame_tcm = capture_tcm.read()


        gray_frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2GRAY)        
        gray_frame_tcm = cv2.cvtColor(frame_tcm, cv2.COLOR_BGR2GRAY)

        
        
        # Укажите коэффициент наложения (alpha) и коэффициент прозрачности (beta)
        alpha = 0.7
        beta = 1 - alpha

        # Наложение изображений
        result = cv2.addWeighted(gray_frame_rgb, alpha, gray_frame_tcm, beta, 0)

        cv2.imshow('gray_frame_rgb', gray_frame_rgb)
        cv2.imshow('gray_frame_tcm', gray_frame_tcm)

        cv2.imshow('result', result)

      
        if cv2.waitKey(1) == 27:
            break
  
    capture_rgb.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()