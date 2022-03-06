from flask import Flask, render_template, Response, redirect
import cv2
import subprocess
import re
import threading

app = Flask(__name__)

camera_ids = []
cameras = []


class VideoCamera(object):
    def __init__(self, id, width, height):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()


@app.before_first_request
def detect_cameras():
    print('DETECT CAMERAS')
    global camera_ids, cameras
    camera_ids, cameras = [], []
    devices = []
    output = subprocess.check_output(['v4l2-ctl', '--list-devices'], shell=False).splitlines()
    for o in output:
        text = o.decode('utf-8')
        if re.search('video', text):
            devices.append(int(re.search('\\d', text).group(0)))
    for device in devices:
        try:
            cap = cv2.VideoCapture(device)
            if cap.read()[0]:
                camera_ids.append(device)
                cap.release()
        except:
            continue
    cv2.destroyAllWindows()
    for _id in camera_ids:
        # camera = VideoCamera()
        cameras.append(cv2.VideoCapture(_id))


def gen_frames(camera_id, frameHeight=640, frameWidth=480):  # generate frame by frame from camera
    camera = cameras[camera_id]
    camera.set(3, frameWidth)
    camera.set(4, frameHeight)
    camera.set(10,150)
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    while True:
        # Capture frame-by-frame
        try:
            success, frame = camera.read()  # read the camera frame
            if not success:
                pass
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
        except Exception as e:
            camera.release()
            pass


def video_feed(camera_id, width, heigth):
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(camera_id, width, heigth), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_1')
def video_feed_1():
    return video_feed(0, 640, 480)

@app.route('/video_feed_2')
def video_feed_2():
    return video_feed(1, 1280, 720)


@app.route('/cam1')
def camera_1():
    """Video streaming home page."""
    return render_template('cam1.html')

@app.route('/cam2')
def camera_2():
    """Video streaming home page."""
    return render_template('cam2.html')

@app.route('/reload')
def reload_cameras():
    for cam in cameras:
        print(cam)
        cam.release()
    cv2.destroyAllWindows()
    detect_cameras()
    return redirect('/')

@app.route('/')
def index():
    """Video streaming home page."""

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)