
import cv2

def main():

    capture_rgb = cv2.VideoCapture("rtsp://localhost:8554/video_stream")
    capture_tcm = cv2.VideoCapture("rtsp://localhost:8554/video_stream")

    while(True):
        ret, frame_rgb = capture_rgb.read()
        ret, frame_tcm = capture_tcm.read()

        gray_frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2GRAY)        
        gray_frame_tcm = cv2.cvtColor(frame_tcm, cv2.COLOR_BGR2GRAY)

        alpha = 0.5
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