import time
from analysis import analyze_sprint
import uuid

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import cv2

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp

import os
import shutil
import math

POSE_CONNECTIONS = [
    # Torso
    (11, 12),
    (11, 23),
    (12, 24),
    (23, 24),

    # Left arm
    (11, 13),
    (13, 15),

    # Right arm
    (12, 14),
    (14, 16),

    # Left leg
    (23, 25),
    (25, 27),
    (27, 31),

    # Right leg
    (24, 26),
    (26, 28),
    (28, 32),
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)

# Make everything inside uploads/ accessible from the browser
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

BaseOptions = python.BaseOptions
PoseLandmarker = vision.PoseLandmarker
PoseLandmarkerOptions = vision.PoseLandmarkerOptions

options = PoseLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="pose_landmarker_lite.task"
    ),
    running_mode=vision.RunningMode.VIDEO,
)

# Calculate angle between three points of a joint
def calculate_angle(a, b, c):

    ba = (
        a[0] - b[0],
        a[1] - b[1]
    )

    bc = (
        c[0] - b[0],
        c[1] - b[1]
    )

    dot = ba[0] * bc[0] + ba[1] * bc[1]

    mag_ba = math.sqrt(ba[0]**2 + ba[1]**2)
    mag_bc = math.sqrt(bc[0]**2 + bc[1]**2)

    if mag_ba == 0 or mag_bc == 0:
        return 0

    cos_theta = dot / (mag_ba * mag_bc)
    cos_theta = max(-1.0, min(1.0, cos_theta))

    angle = math.degrees(math.acos(cos_theta))

    return angle

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):

    detector = PoseLandmarker.create_from_options(options)

    # Save uploaded video
    save_path = os.path.join("uploads", file.filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Open video
    cap = cv2.VideoCapture(save_path)

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30

    frame_index = 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    filename = f"processed_{uuid.uuid4().hex}.mp4"

    output_path = os.path.join(
        "uploads",
        filename
)

    fourcc = cv2.VideoWriter_fourcc(*"avc1")

    writer = cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (width, height)
    )
    print("Writer opened:", writer.isOpened())
    print("FPS:", fps)
    print("Size:", width, height)

    frame_metrics = []

    while True:

        success, frame = cap.read()

        if not success:
            break
        
        height, width, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))

        if timestamp_ms <= 0:
            timestamp_ms = int(frame_index * (1000 / fps))

        previous_timestamp = timestamp_ms
                    
        frame_index += 1        

        result = detector.detect_for_video(
            mp_image,
            timestamp_ms
        )   
        print("poses detected:", len(result.pose_landmarks))

        if result.pose_landmarks:

            for landmarks in result.pose_landmarks:

                points = []
                normalized_points = []

                # Save pixel coordinates
                for landmark in landmarks:

                    x = int(landmark.x * width)
                    y = int(landmark.y * height)

                    points.append((x, y))
                    normalized_points.append(
                        (
                            landmark.x,
                            landmark.y,
                            landmark.z
                        )
                    )
                    cv2.circle(
                        frame,
                        (x, y),
                        4,
                        (0,255,0),
                        -1
                    )
                if len(normalized_points) >= 33:
                    # left knee angle and display

                    left_knee_angle = calculate_angle(
                        normalized_points[23],
                        normalized_points[25],
                        normalized_points[27]
                    )

                    cv2.putText(
                        frame,
                        f"{left_knee_angle:.0f}°",
                        points[25],   # knee location
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2
                    )

                    # right knee angle and display

                    right_knee_angle = calculate_angle(
                    normalized_points[24],
                    normalized_points[26],
                    normalized_points[28]
                    )

                    cv2.putText(
                        frame,
                        f"{right_knee_angle:.0f}°",
                        points[26],   # knee location
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2
                    )

                    # left, mid, and right hip angle and display
                    left_hip_angle = calculate_angle(
                    normalized_points[11],
                    normalized_points[23],
                    normalized_points[25]
                    )

                    right_hip_angle = calculate_angle(
                    normalized_points[12],
                    normalized_points[24],
                    normalized_points[26]
                    )

                    left_shoulder = normalized_points[11]
                    right_shoulder = normalized_points[12]

                    mid_shoulder = (
                        (left_shoulder[0] + right_shoulder[0]) / 2,
                        (left_shoulder[1] + right_shoulder[1]) / 2
                    )

                    left_hip = normalized_points[23]
                    right_hip = normalized_points[24]

                    mid_hip = (
                        (left_hip[0] + right_hip[0]) / 2,
                        (left_hip[1] + right_hip[1]) / 2
                    )

                    dx = mid_shoulder[0] - mid_hip[0]
                    dy = mid_hip[1] - mid_shoulder[1]

                    trunk_lean = abs(
                        math.degrees(
                            math.atan2(dx, dy)
                        )
                    )

                    frame_metrics.append({
                        "frame": frame_index,
                        "time": timestamp_ms,

                        "left_knee": left_knee_angle,
                        "right_knee": right_knee_angle,

                        "left_hip": left_hip_angle,
                        "right_hip": right_hip_angle,

                        "trunk_lean": trunk_lean,

                        "left_ankle_x": normalized_points[27][0],
                        "right_ankle_x": normalized_points[28][0],

                        "left_ankle_y": normalized_points[27][1],
                        "right_ankle_y": normalized_points[28][1],

                        "left_hip_x": normalized_points[23][0],
                        "right_hip_x": normalized_points[24][0],
                    })

                    print(
                    f"Left: {left_knee_angle:.1f}° | Right: {right_knee_angle:.1f}° | Left Hip: {left_hip_angle:.1f}° | Right Hip: {right_hip_angle:.1f}°"
                    )
                    print(
                    f"dx={dx:.3f}, dy={dy:.3f}, lean={trunk_lean:.1f}"
                    )

                    print(
                    f"Left Ankle X: {normalized_points[27][0]:.3f} | Right Ankle X: {normalized_points[28][0]:.3f}"
                    )

                # Draw skeleton
                for start, end in POSE_CONNECTIONS:

                    cv2.line(
                        frame,
                        points[start],
                        points[end],
                        (255,0,0),
                        2
                    )
        writer.write(frame)

    results = analyze_sprint(frame_metrics)
    print(results)

    writer.release()
    cap.release()
    detector.close()

    return {
        "video": f"http://127.0.0.1:8000/uploads/{filename}",
        "analysis": results
    }