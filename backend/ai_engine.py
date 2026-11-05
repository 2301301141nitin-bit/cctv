import os
import cv2
import torch
import torch.nn.functional as F
import faiss
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, logging as tf_logging
from database import SessionLocal
import models

# Hugging Face Access Token (optional, read from environment)
if os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

# Suppress HuggingFace Hub unauthenticated warning logs
tf_logging.set_verbosity_error()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(os.path.join(STATIC_DIR, "videos"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "frames"), exist_ok=True)

# ─── GPU / CPU Setup ────────────────────────────────────────────────────────
num_cores = os.cpu_count() or 4
torch.set_num_threads(num_cores)

# Detect device — prefer CUDA GPU
if torch.cuda.is_available():
    device = "cuda"
    # Enable cuDNN auto-tuner for fastest convolution algorithms
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.enabled = True
    # Pre-allocate GPU memory for stability
    torch.cuda.empty_cache()
    gpu_name = torch.cuda.get_device_name(0)
    gpu_vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU Detected: {gpu_name} ({gpu_vram:.1f} GB VRAM)")
    print(f"CUDA Version: {torch.version.cuda}")
else:
    device = "cpu"
    print(f"⚠️  No GPU detected — running on CPU ({num_cores} threads)")

print(f"   PyTorch: {torch.__version__} | Device: {device}")

# ─── Load CLIP Model (Upgraded to ViT-L/14 for much better accuracy) ────────
# ViT-L/14: 768-dim embeddings, 304M params — the strongest OpenAI CLIP model
# vs old ViT-B/32: 512-dim, 63M params
model_id = "openai/clip-vit-large-patch14"
print(f"   Loading CLIP model: {model_id} ...")

model = CLIPModel.from_pretrained(model_id)
processor = CLIPProcessor.from_pretrained(model_id)

# Move to GPU and optimize
model = model.to(device).eval()

# Enable FP16 on GPU for 2x memory savings and faster inference
_use_fp16 = device == "cuda"
if _use_fp16:
    model = model.half()
    print("   FP16 (half-precision) enabled for GPU inference")

# Warmup GPU with a dummy forward pass
if device == "cuda":
    with torch.inference_mode():
        dummy_img = processor(images=Image.new("RGB", (224, 224)), return_tensors="pt").to(device)
        if _use_fp16:
            dummy_img = {k: v.half() if v.dtype == torch.float32 else v for k, v in dummy_img.items()}
        model.get_image_features(**dummy_img)
    torch.cuda.synchronize()
    print("   GPU warmup complete ✓")

print(f"   CLIP model loaded successfully on {device.upper()}")

# ─── FAISS Index ─────────────────────────────────────────────────────────────
EMBEDDING_DIM = 768  # ViT-L/14 produces 768-dim vectors (was 512 for ViT-B/32)
index = faiss.IndexFlatIP(EMBEDDING_DIM)
frame_metadata = []


def _to_tensor(features):
    if isinstance(features, torch.Tensor):
        return features
    if hasattr(features, "pooler_output") and features.pooler_output is not None:
        return features.pooler_output
    if hasattr(features, "image_embeds") and features.image_embeds is not None:
        return features.image_embeds
    if hasattr(features, "text_embeds") and features.text_embeds is not None:
        return features.text_embeds
    if hasattr(features, "last_hidden_state") and features.last_hidden_state is not None:
        return features.last_hidden_state[:, 0, :]
    return features[0]


def _normalize_path(filepath):
    """Normalize filepath to use forward slashes for consistent web serving."""
    return filepath.replace("\\", "/")


def rebuild_index():
    """
    Loads all existing frames from SQLite database in strict order and populates FAISS index.
    """
    global index, frame_metadata
    db = SessionLocal()
    try:
        frames = db.query(models.Frame).order_by(models.Frame.id.asc()).all()
        if not frames:
            print("No existing frames in database to index.")
            return

        print(f"Re-building FAISS index from {len(frames)} frames in database...")
        index.reset()
        frame_metadata = []

        valid_frames = []
        images = []

        for frame in frames:
            filepath = frame.filepath
            if not os.path.isabs(filepath):
                filepath = os.path.join(BASE_DIR, filepath)

            if os.path.exists(filepath):
                try:
                    img = Image.open(filepath).convert("RGB")
                    images.append(img)
                    valid_frames.append((frame, filepath))
                except Exception as e:
                    print(f"Could not load image {filepath}: {e}")

        if not images:
            return

        batch_size = 16 if device == "cuda" else 32  # Smaller batches for GPU VRAM management
        for i in range(0, len(images), batch_size):
            batch_imgs = images[i:i+batch_size]
            batch_frames = valid_frames[i:i+batch_size]

            inputs = processor(images=batch_imgs, return_tensors="pt").to(device)
            if _use_fp16:
                inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}

            with torch.inference_mode():
                raw_features = model.get_image_features(**inputs)
                image_features = _to_tensor(raw_features)
                image_features = F.normalize(image_features.float(), p=2, dim=-1)
                embeddings = image_features.cpu().numpy().astype('float32')

            index.add(embeddings)
            for db_f, fpath in batch_frames:
                frame_metadata.append({
                    "video_id": db_f.video_id,
                    "frame_id": db_f.id,
                    "timestamp": db_f.timestamp,
                    "filepath": _normalize_path(fpath)
                })
        print(f"Successfully indexed {index.ntotal} frames.")
    except Exception as e:
        print(f"Error rebuilding index: {e}")
    finally:
        db.close()


from database import engine

# Ensure tables exist before querying them
models.Base.metadata.create_all(bind=engine)

# Rebuild index on module load
rebuild_index()


def extract_and_index_video(video_path: str, video_id: int, fps_extract=1.0, progress_callback=None, batch_size=16):
    """
    Extracts frames from a video using batched CLIP inference with GPU acceleration
    and precise 1-to-1 metadata alignment.
    """
    db = SessionLocal()
    try:
        if not os.path.isabs(video_path):
            video_path = os.path.join(BASE_DIR, video_path)

        # Clear any prior frames for this video to prevent metadata corruption/duplication
        db.query(models.Frame).filter(models.Frame.video_id == video_id).delete()
        db.commit()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error opening video {video_path}")
            if progress_callback:
                progress_callback(-1, -1)
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or np.isnan(fps) or fps <= 0:
            fps = 30.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            total_frames = 1

        frame_interval = int(fps / fps_extract)
        if frame_interval <= 0:
            frame_interval = 1

        expected_extracted_frames = max(1, total_frames // frame_interval)

        frames_dir = os.path.join(STATIC_DIR, "frames", str(video_id))
        os.makedirs(frames_dir, exist_ok=True)

        frame_count = 0
        extracted_count = 0

        pending_pil_images = []
        pending_meta = []
        pending_db_frames = []

        def flush_batch():
            nonlocal pending_pil_images, pending_meta, pending_db_frames, extracted_count
            if not pending_pil_images:
                return

            # Compute embeddings with GPU acceleration
            inputs = processor(images=pending_pil_images, return_tensors="pt").to(device)
            if _use_fp16:
                inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}

            with torch.inference_mode():
                raw_features = model.get_image_features(**inputs)
                image_features = _to_tensor(raw_features)
                image_features = F.normalize(image_features.float(), p=2, dim=-1)
                embeddings = image_features.cpu().numpy().astype('float32')

            # 1. Add vectors to FAISS index
            index.add(embeddings)

            # 2. Add frames to SQLite database
            db.add_all(pending_db_frames)
            db.commit()

            # 3. Exact 1-to-1 metadata alignment using populated DB IDs and timestamps
            for i, meta in enumerate(pending_meta):
                meta["frame_id"] = pending_db_frames[i].id
                frame_metadata.append(meta)

            extracted_count += len(pending_pil_images)
            if progress_callback:
                progress_callback(extracted_count, expected_extracted_frames)

            pending_pil_images = []
            pending_meta = []
            pending_db_frames = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                # Clean timestamp formatting — 2 decimal places
                frame_filename = f"{timestamp:.2f}.jpg"
                frame_filepath = os.path.join(frames_dir, frame_filename)

                # Save frame image
                cv2.imwrite(frame_filepath, frame)

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)

                # Use proper web URL path instead of OS path matching main.py mount
                web_filepath = f"/backend-static/frames/{video_id}/{frame_filename}"
                
                db_frame = models.Frame(video_id=video_id, timestamp=timestamp, filepath=web_filepath)

                pending_pil_images.append(pil_image)
                pending_db_frames.append(db_frame)
                pending_meta.append({
                    "video_id": video_id,
                    "timestamp": timestamp,
                    "filepath": web_filepath
                })

                if len(pending_pil_images) >= batch_size:
                    flush_batch()

            frame_count += 1

        cap.release()
        flush_batch()

        db_video = db.query(models.Video).filter(models.Video.id == video_id).first()
        if db_video:
            db_video.status = "ready"
            db.commit()

        print(f"Processed {video_path}: {extracted_count} frames indexed on {device.upper()}.")
        if progress_callback:
            progress_callback(expected_extracted_frames, expected_extracted_frames)

    except Exception as e:
        print(f"Error processing video: {e}")
        import traceback
        traceback.print_exc()
        db_video = db.query(models.Video).filter(models.Video.id == video_id).first()
        if db_video:
            db_video.status = "error"
            db.commit()
        if progress_callback:
            progress_callback(-1, -1)
    finally:
        db.close()


def search_by_text(query: str, top_k: int = 10, min_score: float = 0.15):
    """
    Search indexed frames using a text query with Prompt Ensembling and score thresholding.
    Uses enhanced surveillance-specific prompt templates for ViT-L/14.
    """
    if index.ntotal == 0:
        return []

    # Enhanced prompt ensembling — more templates = better accuracy
    templates = [
        f"a photo of {query}",
        f"a CCTV security camera frame showing {query}",
        f"a surveillance video frame of {query}",
        f"a clear view of {query}",
        f"a security camera recording of {query}",
        f"an overhead camera view of {query}",
        f"{query} captured on a security camera",
        f"{query}",
    ]

    inputs = processor(text=templates, return_tensors="pt", padding=True, truncation=True).to(device)
    if _use_fp16:
        inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}

    with torch.inference_mode():
        raw_features = model.get_text_features(**inputs)
        text_features = _to_tensor(raw_features)

    text_features = F.normalize(text_features.float(), p=2, dim=-1)
    avg_feature = text_features.mean(dim=0, keepdim=True)
    avg_feature = F.normalize(avg_feature, p=2, dim=-1)

    query_embedding = avg_feature.cpu().numpy().astype('float32')

    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_embedding, k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx < len(frame_metadata):
            score = float(distances[0][i])
            if score >= min_score:
                meta = frame_metadata[idx]
                results.append({
                    "score": score,
                    **meta
                })
    return results


def search_by_image(image: Image.Image, top_k: int = 10, min_score: float = 0.15):
    """
    Search indexed frames using an image query with score thresholding.
    GPU-accelerated with FP16 on supported hardware.
    """
    if index.ntotal == 0:
        return []

    inputs = processor(images=image, return_tensors="pt").to(device)
    if _use_fp16:
        inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}

    with torch.inference_mode():
        raw_features = model.get_image_features(**inputs)
        image_features = _to_tensor(raw_features)

    image_features = F.normalize(image_features.float(), p=2, dim=-1)
    query_embedding = image_features.cpu().numpy().astype('float32')

    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_embedding, k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx < len(frame_metadata):
            score = float(distances[0][i])
            if score >= min_score:
                meta = frame_metadata[idx]
                results.append({
                    "score": score,
                    **meta
                })
    return results
