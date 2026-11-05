import os
import threading
import shutil
import cv2
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import models
from database import engine, get_db

import ai_engine
import license_manager

# Ensure database and directories exist
models.Base.metadata.create_all(bind=engine)
os.makedirs("static/videos", exist_ok=True)
os.makedirs("static/frames", exist_ok=True)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def format_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d} ({seconds:.1f}s)"
    return f"{mins:02d}:{secs:02d} ({seconds:.1f}s)"

class LicenseActivationWindow(ctk.CTk):
    def __init__(self, error_msg="License Activation Required"):
        super().__init__()
        
        self.title("Antigravity CCTV - License Activation")
        self.geometry("600x480")
        self.resizable(False, False)
        self.activated = False
        
        lbl_title = ctk.CTkLabel(self, text="Software License Activation", font=ctk.CTkFont(size=22, weight="bold"))
        lbl_title.pack(pady=(25, 5))
        
        lbl_status = ctk.CTkLabel(self, text=error_msg, text_color="#FF6B6B", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_status.pack(pady=(0, 15))
        
        frame = ctk.CTkFrame(self)
        frame.pack(padx=30, pady=10, fill="both", expand=True)
        
        # Machine HWID Display
        ctk.CTkLabel(frame, text="Your Machine Hardware ID (HWID):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 2))
        
        hwid_frame = ctk.CTkFrame(frame, fg_color="transparent")
        hwid_frame.pack(fill="x", padx=20, pady=(0, 10))
        hwid_frame.grid_columnconfigure(0, weight=1)
        
        self.hwid_str = license_manager.get_machine_hwid()
        self.entry_hwid = ctk.CTkEntry(hwid_frame, font=ctk.CTkFont(size=14, weight="bold"))
        self.entry_hwid.insert(0, self.hwid_str)
        self.entry_hwid.configure(state="readonly")
        self.entry_hwid.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        btn_copy = ctk.CTkButton(hwid_frame, text="Copy HWID", command=self.copy_hwid, width=100)
        btn_copy.grid(row=0, column=1)
        
        # License Key Entry
        ctk.CTkLabel(frame, text="Paste License Key:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 2))
        
        self.text_key = ctk.CTkTextbox(frame, height=90)
        self.text_key.pack(fill="x", padx=20, pady=(0, 15))
        
        # Action Buttons
        btn_activate = ctk.CTkButton(frame, text="Activate Software", command=self.activate_key, height=40, font=ctk.CTkFont(size=15, weight="bold"))
        btn_activate.pack(fill="x", padx=20, pady=5)
        
    def copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.hwid_str)
        messagebox.showinfo("Copied", "Hardware ID copied to clipboard! Send this HWID to get your License Key.")
        
    def activate_key(self):
        key_str = self.text_key.get("1.0", "end").strip()
        is_valid, msg, payload = license_manager.verify_license_key(key_str)
        
        if is_valid:
            license_manager.save_license(key_str)
            messagebox.showinfo("Success", f"License Activated Successfully!\nClient: {payload.get('client')}\nExpiry: {payload.get('expiry')}")
            self.activated = True
            self.destroy()
        else:
            messagebox.showerror("Activation Error", f"License Activation Failed:\n{msg}")

class CCTVApp(ctk.CTk):
    def __init__(self, license_payload=None):
        super().__init__()
        
        self.license_payload = license_payload or {}
        client = self.license_payload.get("client", "Licensed User")
        expiry = self.license_payload.get("expiry", "Lifetime")
        
        self.title(f"Antigravity CCTV AI Analysis System — [{client} | Expiry: {expiry}]")
        self.geometry("1100x750")
        
        self.db = next(get_db())
        
        # Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main Tabview
        self.tabview = ctk.CTkTabview(self, width=1050, height=700)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_upload = self.tabview.add("Upload Footage")
        self.tab_search = self.tabview.add("Analyze & Search")
        self.tab_live = self.tabview.add("Live IP Webcam")
        
        self.setup_upload_tab()
        self.setup_search_tab()
        self.setup_live_tab()

    def setup_upload_tab(self):
        self.tab_upload.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(self.tab_upload, text="Upload & Process CCTV Video", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, pady=(30, 10))
        
        lbl_desc = ctk.CTkLabel(self.tab_upload, text="Select long CCTV footage (.mp4, .avi, .mov) for high-performance AI indexing.", text_color="gray")
        lbl_desc.grid(row=1, column=0, pady=(0, 20))

        # Frame extraction rate setting
        fps_frame = ctk.CTkFrame(self.tab_upload, fg_color="transparent")
        fps_frame.grid(row=2, column=0, pady=10)
        
        lbl_fps = ctk.CTkLabel(fps_frame, text="Extraction Sampling Rate:", font=ctk.CTkFont(weight="bold"))
        lbl_fps.grid(row=0, column=0, padx=10)
        
        self.option_fps = ctk.CTkOptionMenu(
            fps_frame,
            values=[
                "1.0 Frame / sec (High Detail)",
                "0.5 Frames / sec (Standard - Long Video)",
                "0.2 Frames / sec (Fast)",
                "0.1 Frames / sec (Ultra Fast)"
            ]
        )
        self.option_fps.set("0.5 Frames / sec (Standard - Long Video)")
        self.option_fps.grid(row=0, column=1, padx=10)
        
        self.btn_upload = ctk.CTkButton(self.tab_upload, text="Select Video File", command=self.upload_video_dialog, height=50, width=220, font=ctk.CTkFont(size=15, weight="bold"))
        self.btn_upload.grid(row=3, column=0, pady=20)
        
        self.progress_bar = ctk.CTkProgressBar(self.tab_upload, width=500)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=4, column=0, pady=10)
        self.progress_bar.grid_remove()
        
        self.lbl_status = ctk.CTkLabel(self.tab_upload, text="", font=ctk.CTkFont(size=14))
        self.lbl_status.grid(row=5, column=0, pady=10)

    def upload_video_dialog(self):
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if filepath:
            self.process_video(filepath)

    def get_selected_fps(self) -> float:
        val = self.option_fps.get()
        if "1.0" in val:
            return 1.0
        elif "0.5" in val:
            return 0.5
        elif "0.2" in val:
            return 0.2
        elif "0.1" in val:
            return 0.1
        return 0.5

    def process_video(self, source_path):
        filename = os.path.basename(source_path)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dest_dir = os.path.join(base_dir, "static", "videos")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        
        if os.path.abspath(source_path) != os.path.abspath(dest_path):
            try:
                shutil.copy(source_path, dest_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not copy file: {e}")
                return
            
        db_video = models.Video(filename=filename, filepath=dest_path, status="processing")
        self.db.add(db_video)
        self.db.commit()
        self.db.refresh(db_video)
        
        fps_extract = self.get_selected_fps()
        
        self.btn_upload.configure(state="disabled")
        self.option_fps.configure(state="disabled")
        self.progress_bar.grid()
        self.progress_bar.set(0)
        self.lbl_status.configure(text=f"Ingesting {filename} at {fps_extract} FPS...", text_color="white")
        
        thread = threading.Thread(target=self.run_ai_engine, args=(dest_path, db_video.id, fps_extract), daemon=True)
        thread.start()

    def run_ai_engine(self, dest_path, video_id, fps_extract):
        def progress_cb(current, total):
            def update_ui():
                if total > 0 and current >= 0:
                    pct = min(1.0, current / total)
                    self.progress_bar.set(pct)
                    self.lbl_status.configure(text=f"Processed {current}/{total} frames ({int(pct*100)}%)...", text_color="white")
                elif current == -1:
                    self.lbl_status.configure(text="Error processing video.", text_color="red")
                    self.btn_upload.configure(state="normal")
                    self.option_fps.configure(state="normal")
            self.after(0, update_ui)
                
        ai_engine.extract_and_index_video(dest_path, video_id, fps_extract=fps_extract, progress_callback=progress_cb, batch_size=32)
        
        def finish_ui():
            self.btn_upload.configure(state="normal")
            self.option_fps.configure(state="normal")
            self.lbl_status.configure(text="Processing & Indexing complete!", text_color="#00FF7F")
            self.progress_bar.set(1)
        self.after(0, finish_ui)

    def setup_search_tab(self):
        self.tab_search.grid_columnconfigure(0, weight=1)
        self.tab_search.grid_rowconfigure(2, weight=1)
        
        # Search controls
        control_frame = ctk.CTkFrame(self.tab_search, fg_color="transparent")
        control_frame.grid(row=0, column=0, pady=10, sticky="ew")
        control_frame.grid_columnconfigure(1, weight=1)
        
        self.search_mode = ctk.StringVar(value="Text")
        
        radio_text = ctk.CTkRadioButton(control_frame, text="Keyword Search", variable=self.search_mode, value="Text", command=self.on_search_mode_change)
        radio_text.grid(row=0, column=0, padx=10)
        
        radio_image = ctk.CTkRadioButton(control_frame, text="Image Search", variable=self.search_mode, value="Image", command=self.on_search_mode_change)
        radio_image.grid(row=0, column=1, padx=10, sticky="w")
        
        # Top-K Selector
        lbl_topk = ctk.CTkLabel(control_frame, text="Max Results:")
        lbl_topk.grid(row=0, column=2, padx=(20, 5))
        
        self.option_top_k = ctk.CTkOptionMenu(control_frame, values=["5 Results", "10 Results", "20 Results", "50 Results"], width=120)
        self.option_top_k.set("10 Results")
        self.option_top_k.grid(row=0, column=3, padx=10)
        
        # Input area
        self.input_frame = ctk.CTkFrame(self.tab_search, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_query = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., 'person in black jacket', 'red car', 'someone walking'")
        self.entry_query.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.btn_search = ctk.CTkButton(self.input_frame, text="AI Search", command=self.perform_search, font=ctk.CTkFont(weight="bold"))
        self.btn_search.grid(row=0, column=1, padx=10)
        
        self.image_query_path = None
        self.btn_select_image = ctk.CTkButton(self.input_frame, text="Select Reference Image", command=self.select_reference_image)
        self.btn_select_image.grid(row=0, column=0, padx=10, sticky="ew")
        self.btn_select_image.grid_remove()
        
        # Results area (scrollable)
        self.results_frame = ctk.CTkScrollableFrame(self.tab_search)
        self.results_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    def on_search_mode_change(self):
        mode = self.search_mode.get()
        if mode == "Text":
            self.btn_select_image.grid_remove()
            self.entry_query.grid(row=0, column=0, padx=10, sticky="ew")
        else:
            self.entry_query.grid_remove()
            self.btn_select_image.grid(row=0, column=0, padx=10, sticky="ew")
            
    def select_reference_image(self):
        filepath = filedialog.askopenfilename(
            title="Select Reference Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if filepath:
            self.image_query_path = filepath
            self.btn_select_image.configure(text=os.path.basename(filepath))

    def get_selected_top_k(self) -> int:
        val = self.option_top_k.get()
        digits = [int(s) for s in val.split() if s.isdigit()]
        return digits[0] if digits else 10

    def perform_search(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        mode = self.search_mode.get()
        top_k = self.get_selected_top_k()
        
        lbl_searching = ctk.CTkLabel(self.results_frame, text="Performing AI Ensembled Vector Search...", font=ctk.CTkFont(size=14))
        lbl_searching.grid(row=0, column=0, pady=20)
        self.btn_search.configure(state="disabled")
        
        if mode == "Text":
            query = self.entry_query.get().strip()
            if not query:
                lbl_searching.configure(text="Please enter a search keyword.")
                self.btn_search.configure(state="normal")
                return
            target_func = lambda: ai_engine.search_by_text(query, top_k=top_k)
        else:
            if not self.image_query_path:
                lbl_searching.configure(text="Please select an image first.")
                self.btn_search.configure(state="normal")
                return
            try:
                img = Image.open(self.image_query_path).convert("RGB")
            except Exception as e:
                lbl_searching.configure(text=f"Error reading image: {e}")
                self.btn_search.configure(state="normal")
                return
            target_func = lambda: ai_engine.search_by_image(img, top_k=top_k)

        def search_thread():
            results = target_func()
            def update_results():
                lbl_searching.destroy()
                self.btn_search.configure(state="normal")
                self.display_results(results)
            self.after(0, update_results)

        threading.Thread(target=search_thread, daemon=True).start()

    def display_results(self, results):
        if not results:
            lbl = ctk.CTkLabel(self.results_frame, text="No matching video frames found.", text_color="gray", font=ctk.CTkFont(size=14))
            lbl.grid(row=0, column=0, pady=20, padx=20)
            return
            
        columns = 3
        for i, res in enumerate(results):
            row = i // columns
            col = i % columns
            
            card = ctk.CTkFrame(self.results_frame)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="n")
            
            try:
                img_path = res["filepath"]
                if not os.path.isabs(img_path):
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    img_path = os.path.join(base_dir, img_path)
                
                img = Image.open(img_path).convert("RGB")
                img.thumbnail((260, 260))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(260, 160))
                
                lbl_img = ctk.CTkLabel(card, image=ctk_img, text="")
                lbl_img.image = ctk_img
                lbl_img.pack(padx=5, pady=5)
                
                ts_formatted = format_timestamp(res['timestamp'])
                score_pct = res['score'] * 100
                
                color = "#00FF7F" if score_pct >= 70 else "#FFD700" if score_pct >= 50 else "#FFA500"
                
                lbl_info = ctk.CTkLabel(
                    card,
                    text=f"Time: {ts_formatted}\nMatch: {score_pct:.1f}%",
                    justify="left",
                    text_color=color,
                    font=ctk.CTkFont(weight="bold")
                )
                lbl_info.pack(padx=8, pady=(0, 8), anchor="w")
                
            except Exception as e:
                print(f"Error loading image {res.get('filepath')}: {e}")
                lbl_err = ctk.CTkLabel(card, text="Error loading frame", text_color="red")
                lbl_err.pack(padx=5, pady=5)

    def setup_live_tab(self):
        self.tab_live.grid_columnconfigure(0, weight=1)
        self.tab_live.grid_rowconfigure(3, weight=1)

        # Control Frame
        control_frame = ctk.CTkFrame(self.tab_live, fg_color="transparent")
        control_frame.grid(row=0, column=0, pady=10, sticky="ew")
        
        lbl_url = ctk.CTkLabel(control_frame, text="IP Camera URL / RTSP:", font=ctk.CTkFont(weight="bold"))
        lbl_url.grid(row=0, column=0, padx=10)
        
        self.entry_cam_url = ctk.CTkEntry(control_frame, width=400, placeholder_text="http://192.168.1.100:8080/video or rtsp://...")
        self.entry_cam_url.grid(row=0, column=1, padx=10)
        
        self.btn_connect = ctk.CTkButton(control_frame, text="Connect", command=self.connect_camera, fg_color="green", hover_color="darkgreen")
        self.btn_connect.grid(row=0, column=2, padx=10)
        
        self.btn_disconnect = ctk.CTkButton(control_frame, text="Disconnect", command=self.disconnect_camera, fg_color="red", hover_color="darkred", state="disabled")
        self.btn_disconnect.grid(row=0, column=3, padx=10)
        
        self.ai_enabled = ctk.BooleanVar(value=False)
        self.chk_ai = ctk.CTkSwitch(control_frame, text="Enable Real-Time AI Tracking", variable=self.ai_enabled, command=self.toggle_ai)
        self.chk_ai.grid(row=0, column=4, padx=10)
        
        # Second row of controls for YOLO-World Semantic Search
        control_frame_2 = ctk.CTkFrame(self.tab_live, fg_color="transparent")
        control_frame_2.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        
        lbl_targets = ctk.CTkLabel(control_frame_2, text="Custom AI Targets:", font=ctk.CTkFont(weight="bold"))
        lbl_targets.grid(row=0, column=0, padx=10)
        
        self.entry_targets = ctk.CTkEntry(control_frame_2, width=400, placeholder_text="e.g. red shirt, backpack, black car")
        self.entry_targets.grid(row=0, column=1, padx=10)
        
        self.btn_update_targets = ctk.CTkButton(control_frame_2, text="Update Targets", command=self.update_ai_targets, width=120)
        self.btn_update_targets.grid(row=0, column=2, padx=10)
        
        # Add Confidence Threshold Slider
        self.lbl_conf = ctk.CTkLabel(control_frame_2, text="Strictness: 25%", font=ctk.CTkFont(weight="bold"))
        self.lbl_conf.grid(row=0, column=3, padx=(20, 5))
        
        self.slider_conf = ctk.CTkSlider(control_frame_2, from_=0.05, to=0.95, number_of_steps=90, command=self.on_conf_change)
        self.slider_conf.set(0.25)
        self.slider_conf.grid(row=0, column=4, padx=5)
        
        # Status Label
        self.lbl_cam_status = ctk.CTkLabel(self.tab_live, text="Disconnected", text_color="gray")
        self.lbl_cam_status.grid(row=2, column=0, pady=(0, 10))
        
        # Video Display Frame
        # Video Display Frame
        self.video_frame = ctk.CTkLabel(self.tab_live, text="No Video Signal", bg_color="black", width=800, height=450)
        self.video_frame.grid(row=3, column=0, padx=20, pady=10)
        
        self.cap = None
        self.is_streaming = False

    def on_conf_change(self, value):
        self.lbl_conf.configure(text=f"Strictness: {int(value*100)}%")
        
    def toggle_ai(self):
        if self.ai_enabled.get():
            if getattr(self, 'yolo_model', None) is None:
                self.lbl_cam_status.configure(text="Loading Open-Vocabulary AI Model...", text_color="yellow")
                def load_model():
                    try:
                        from ultralytics import YOLO
                        # Load YOLOv8l-worldv2 which is significantly more accurate and reduces hallucinations
                        self.yolo_model = YOLO("yolov8l-worldv2.pt")
                        self.update_ai_targets() # Apply default or custom targets immediately
                        self.lbl_cam_status.configure(text="Open-Vocabulary AI Model Loaded", text_color="green")
                    except Exception as e:
                        print(f"Error loading AI model: {e}")
                        self.lbl_cam_status.configure(text="Failed to load AI", text_color="red")
                        self.ai_enabled.set(False)
                threading.Thread(target=load_model, daemon=True).start()
                
    def update_ai_targets(self):
        if not getattr(self, 'yolo_model', None):
            return
            
        targets_str = self.entry_targets.get().strip()
        if not targets_str:
            targets_str = "person, car, animal" # default classes if empty
            
        classes = [t.strip() for t in targets_str.split(",") if t.strip()]
        if classes:
            try:
                self.yolo_model.set_classes(classes)
                self.lbl_cam_status.configure(text=f"AI targets updated to: {', '.join(classes)}", text_color="green")
            except Exception as e:
                print(f"Failed to set classes: {e}")
        
    def connect_camera(self):
        url = self.entry_cam_url.get().strip()
        if not url:
            self.lbl_cam_status.configure(text="Please enter a valid URL", text_color="red")
            return
            
        self.btn_connect.configure(state="disabled")
        self.entry_cam_url.configure(state="disabled")
        self.btn_disconnect.configure(state="normal")
        self.lbl_cam_status.configure(text="Connecting...", text_color="yellow")
        
        self.is_streaming = True
        threading.Thread(target=self.camera_loop, args=(url,), daemon=True).start()
        
    def disconnect_camera(self):
        self.is_streaming = False
        self.btn_connect.configure(state="normal")
        self.entry_cam_url.configure(state="normal")
        self.btn_disconnect.configure(state="disabled")
        self.lbl_cam_status.configure(text="Disconnected", text_color="gray")
        self.video_frame.configure(image="", text="No Video Signal")
        
    def camera_loop(self, url):
        import time
        # We need to handle the case if url is an integer (for local webcams like '0')
        if url.isdigit():
            url = int(url)
            
        self.cap = cv2.VideoCapture(url)
        # Minimize OpenCV's internal buffer to reduce latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not self.cap.isOpened():
            def ui_fail():
                self.lbl_cam_status.configure(text="Connection Failed", text_color="red")
                self.disconnect_camera()
            self.after(0, ui_fail)
            return
            
        def ui_success():
            self.lbl_cam_status.configure(text="Connected - Live", text_color="green")
        self.after(0, ui_success)
        
        self.latest_frame = None
        self.is_reading = True
        
        # Dedicated thread to constantly pull frames and prevent OpenCV buffer lag
        def read_frames():
            while self.is_reading:
                ret, frame = self.cap.read()
                if not ret:
                    self.is_reading = False
                    break
                self.latest_frame = frame
                
        reader_thread = threading.Thread(target=read_frames, daemon=True)
        reader_thread.start()
        
        last_ai_time = 0
        ai_interval = 0.033  # ~30 FPS for AI processing
        last_annotated_frame = None
        
        while self.is_streaming and self.is_reading:
            if self.latest_frame is None:
                time.sleep(0.005)
                continue
                
            frame = self.latest_frame.copy()
            
            # AI Inference
            if getattr(self, 'ai_enabled', None) and self.ai_enabled.get() and getattr(self, 'yolo_model', None) is not None:
                current_time = time.time()
                if current_time - last_ai_time > ai_interval:
                    try:
                        current_conf = self.slider_conf.get()
                        # Use dynamic confidence threshold
                        results = self.yolo_model(frame, verbose=False, conf=current_conf)
                        if results and len(results) > 0:
                            last_annotated_frame = results[0].plot()
                    except Exception as e:
                        pass
                    last_ai_time = current_time
                    
                # If we have a recent annotated frame, show it instead of the raw frame
                if last_annotated_frame is not None:
                    frame = last_annotated_frame
            else:
                last_annotated_frame = None
                
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame)
            pil_img.thumbnail((800, 450))
            
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            
            def update_frame(img=ctk_img):
                if self.is_streaming:
                    self.video_frame.configure(image=img, text="")
            self.after(0, update_frame)
            
            # Small sleep to prevent 100% CPU lock on the UI update thread
            time.sleep(0.01)
            
        self.is_reading = False
        if self.cap:
            self.cap.release()
            
        def ui_disconnect():
            if self.is_streaming:
                self.lbl_cam_status.configure(text="Connection Lost", text_color="red")
                self.disconnect_camera()
        self.after(0, ui_disconnect)

def main():
    is_valid, msg, payload = license_manager.verify_stored_license()
    if not is_valid:
        act_win = LicenseActivationWindow(error_msg=msg)
        act_win.mainloop()
        if not act_win.activated:
            return
        is_valid, msg, payload = license_manager.verify_stored_license()
        
    app = CCTVApp(license_payload=payload)
    app.mainloop()

if __name__ == "__main__":
    main()
