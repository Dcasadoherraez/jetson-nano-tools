# ==========================================================
# video_pipeline.py
# This tool was made for testing GStreamer on Ubuntu 20.04
# webcam. The server thread creates the sending pipeline
# while the client thread creates the reciving pipeline. 
# Modify the device accordingly to your camera.
# ==========================================================

from threading import Thread
import cv2
from time import sleep
import signal
import sys
import os

WINDOW_NAME = 'UDP'


def open_cam_pc(connection, device):
    # create UDP server pipeline to send H264 videos
    os.system(("gst-launch-1.0 v4l2src do-timestamp=TRUE device={} ! \
                videoconvert ! x264enc tune=zerolatency ! rtph264pay ! \
                udpsink host={} port={}").format(device, *connection))    

def get_cam_pc(connection):
    # create UDP client pipeline to receive H264 videos
    print("Getting UDP camera on {} port {}".format(*connection))
    gst_str = 'udpsrc port={} caps="application/x-rtp,media=(string)video,encoding-name=(string)H264" ! \
               rtph264depay ! decodebin ! videoconvert ! queue ! appsink'.format(connection[1])
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

def open_window(width, height):
    print("Opening window")
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, width, height)
    cv2.moveWindow(WINDOW_NAME, 0, 0)
    cv2.setWindowTitle(WINDOW_NAME, 'UDP GStreamer')

def read_cam(cap):
    while True:
        if cv2.getWindowProperty(WINDOW_NAME, 0) < 0:
            break
        _, img = cap.read() # grab the next image frame from camera
        cv2.imshow(WINDOW_NAME, img)
        key = cv2.waitKey(10)
        if key == 27: # ESC key: quit program
            break

class ServerThread(Thread):
    def __init__(self, dev):
        self.dev = dev
        super().__init__()

    def udp_server(self):
        server_address = ('localhost', 5004)
        print("[SERVER] Starting on {} port {}".format(*server_address))
        open_cam_pc(server_address, self.dev)

    def join(self):
        Thread.join(self)
        if self.exc:
            raise self.exc

    def run(self):
        print("[SERVER] Starting server thread")
        try:
            self.udp_server()
        except BaseException as e:
            self.exc = e

class ClientThread(Thread):

    def udp_client(self):
        client_connection = ('localhost', 5004)
        print("[CLIENT] Connecting to {} port {}".format(*client_connection))

        cap = get_cam_pc(client_connection)
        print("Bro esto")
        if not cap.isOpened():
            sys.exit('Failed to open camera!')

        open_window(500, 500)
        read_cam(cap)

    def join(self):
        Thread.join(self)
        if self.exc:
            raise self.exc

    def run(self):
        print("[CLIENT] Starting client thread")
        try:
            self.udp_client()
        except BaseException as e:
            self.exc = e

def udp_stop(*args):
    for thread in thread_list:
        thread.join()
    print("udp stopped")

    sys.exit(0)

if __name__ == "__main__": 
    cam_dev = '/dev/video0'
    client_thread = ClientThread()
    server_thread = ServerThread(cam_dev)

    thread_list = [client_thread, server_thread]

    server_thread.start()
    sleep(1)
    client_thread.start()

    # Override SIGINT
    signal.signal(signal.SIGINT, udp_stop)
