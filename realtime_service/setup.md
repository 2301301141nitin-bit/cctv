# Windows Setup & Testing Procedure (Phase 1)

## Prerequisites

- **Python 3.12+** installed on your Windows machine.
- **Git** (optional, but good for cloning repositories).
- **DroidCam** installed on both your Android phone and Windows PC.

## Installation

1. Open PowerShell or Command Prompt.
2. Navigate to the `realtime_service` directory:
   ```cmd
   cd c:\Users\nitin\Desktop\cctv\realtime_service
   ```
3. Create a Python virtual environment:
   ```cmd
   python -m venv venv
   ```
4. Activate the virtual environment:
   ```cmd
   .\venv\Scripts\activate
   ```
5. Install the dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
   > **Note on GPU/CUDA Support:** By default, `ultralytics` will try to install the best PyTorch version. On Windows, if you have an NVIDIA GPU and want maximum performance, you should explicitly install the CUDA version of PyTorch first. To do this, run this *before* running the pip install for requirements:
   > ```cmd
   > pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   > ```

6. Create an `.env` file by copying the example:
   ```cmd
   copy .env.example .env
   ```

## Firebase Configuration (Optional for Cloud Sync)

If you want to sync real-time alerts to the cloud:
1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Open your project, go to **Project Settings > Service Accounts**.
3. Click **Generate new private key** and download the JSON file.
4. Rename it to `serviceAccountKey.json` and place it in the `realtime_service` directory.
5. In your `.env` file, set:
   ```env
   FIREBASE_ENABLED=True
   FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
   ```

## Running the Server

Make sure your virtual environment is active, then run:

```cmd
python -m app.main
```

Or using `uvicorn` directly:

```cmd
uvicorn app.main:app --reload
```

The first time you run this, it will automatically download the `yolov8n.pt` weights.

## Testing with DroidCam

1. Start **DroidCam** on your phone.
2. Start the **DroidCam Client** on Windows and connect to your phone.
3. Once the video feed is working in the DroidCam Client, note the device index. DroidCam usually creates a virtual webcam on index `1` or `2` (sometimes `0` if you have no other webcams).
4. Send a POST request to add the camera to the AI engine. You can do this using PowerShell:

   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.0:8000/cameras" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"source": "1", "sampling_rate": 3}'
   ```
   *(Change `"1"` to `"0"` or `"2"` if it doesn't pick up the DroidCam feed)*.

5. A new window should pop up showing your camera feed with YOLO bounding boxes and ByteTrack IDs drawn over objects!

6. To get the latest AI detection events, open your browser or run:
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/events"
   ```
   You will receive a standard JSON response with detections, bounding boxes, and track IDs.
