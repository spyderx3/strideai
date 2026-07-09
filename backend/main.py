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
    running_mode=vision.RunningMode.IMAGE,
)

detector = PoseLandmarker.create_from_options(options)

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):

    # Save uploaded video
    save_path = os.path.join("uploads", file.filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Open video
    cap = cv2.VideoCapture(save_path)

    success, frame = cap.read()

    if not success:
        return {"error": "Could not read from uploaded video."}

    # Convert BGR -> RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert image for MediaPipe
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # Run pose detection
    result = detector.detect(mp_image)

    # Draw landmarks manually
    if result.pose_landmarks:

        for landmarks in result.pose_landmarks:

            for landmark in landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])

                cv2.circle(
                    frame,
                    (x, y),
                    5,
                    (0,255,0),
                    -1
                )

    output_image = "uploads/processed_frame.jpg"

    cv2.imwrite(output_image, frame)

    cap.release()

    return {
        "image": "http://127.0.0.1:8000/uploads/processed_frame.jpg"
    }