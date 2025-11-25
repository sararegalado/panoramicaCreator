import cv2
import numpy as np
import customtkinter as ctk  # Librería principal de UI moderna
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import threading
from pathlib import Path
import time
from datetime import datetime
import platform

# Importar nuestro stitcher
from panorama_stitcher import PanoramaStitcher

# Configuración global de CustomTkinter
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")  

class PanoramaCreatorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.title("Creador de panorámicas")
        self.geometry("1200x800")
        
        # Configurar grid principal (2 columnas: panel lateral y preview)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Variables de estado
        self.cap = None                    
        self.is_capturing = False          
        self.captured_images = []          
        self.panorama = None               
        self.preview_running = False       
        self.last_sequence_from_camera = False  
        self._app_start_time = time.time()
        
        # Variables de configuración (adaptadas a CTk)
        self.n_photos_var = tk.IntVar(value=5)        
        self.interval_var = tk.DoubleVar(value=2.0)   
        self.camera_index_var = tk.StringVar(value="0") # Cambiado a String para ComboBox
        
        # Directorios
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Construir la interfaz
        self.setup_ui()
        
        # Intentar conectar con el iPhone automáticamente
        self.after(100, self._auto_connect)

    def setup_ui(self):
        # --- PANEL IZQUIERDO (CONTROLES) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Empujar contenido hacia arriba

        # Título en el sidebar
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="CREA TU\nPANORÁMICA", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Crear paneles de control
        self.create_connection_panel()
        self.create_settings_panel()
        self.create_capture_panel()
        self.create_status_panel()

        # --- PANEL DERECHO (PREVIEW) ---
        self.preview_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.preview_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        # Título Preview
        self.preview_title = ctk.CTkLabel(
            self.preview_frame, 
            text="", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.preview_title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Canvas tk.Canvas para actualizar frames
        # Lo envolvemos en un frame CTk para el borde
        self.canvas_container = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        self.canvas_container.grid(row=1, column=0, sticky="nsew")
        
        self.preview_canvas = tk.Canvas(
            self.canvas_container,
            bg="#1a1a1a", # Fondo oscuro neutro
            highlightthickness=0
        )
        self.preview_canvas.pack(fill="both", expand=True)
        
        # Placeholder inicial
        self.preview_canvas.create_text(
            400, 300, 
            text="Esperando conexión...", 
            fill="#808080", 
            font=("Arial", 14), 
            tags='placeholder'
        )

    def create_connection_panel(self):
        # Frame contenedor
        frame = ctk.CTkFrame(self.sidebar_frame)
        frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        lbl = ctk.CTkLabel(frame, text="CONEXIÓN", font=ctk.CTkFont(size=12, weight="bold"))
        lbl.pack(pady=5)

        # Estado
        self.connection_label = ctk.CTkLabel(frame, text="🔴 Desconectado", text_color="red")
        self.connection_label.pack(pady=(0, 5))

        # Selector de cámara (ComboBox es más moderno que Spinbox)
        cam_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cam_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(cam_frame, text="Cámara:").pack(side="left")
        self.camera_combo = ctk.CTkComboBox(
            cam_frame, 
            values=["0", "1", "2", "3"],
            variable=self.camera_index_var,
            width=60
        )
        self.camera_combo.pack(side="left", padx=5)
        
        # Botón buscar
        btn_search = ctk.CTkButton(
            cam_frame, text="🔍", width=30, command=self.search_cameras
        )
        btn_search.pack(side="left")

        # Botones Conectar/Desconectar
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        self.connect_btn = ctk.CTkButton(
            btn_frame, text="Conectar", width=90, command=self.connect_camera
        )
        self.connect_btn.pack(side="left", padx=5)
        
        self.disconnect_btn = ctk.CTkButton(
            btn_frame, text="Cortar", width=90, fg_color="#D32F2F", hover_color="#B71C1C",
            state="disabled", command=self.disconnect_camera
        )
        self.disconnect_btn.pack(side="left", padx=5)

    def create_settings_panel(self):
        frame = ctk.CTkFrame(self.sidebar_frame)
        frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(frame, text="CONFIGURACIÓN", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
        
        # Slider Fotos
        self.lbl_photos = ctk.CTkLabel(frame, text=f"Fotos: {self.n_photos_var.get()}")
        self.lbl_photos.pack(anchor="w", padx=10)
        
        slider_photos = ctk.CTkSlider(
            frame, from_=2, to=20, number_of_steps=18, variable=self.n_photos_var,
            command=lambda v: self.update_slider_labels()
        )
        slider_photos.pack(fill="x", padx=10, pady=(0, 10))
        
        # Slider Intervalo
        self.lbl_interval = ctk.CTkLabel(frame, text=f"Intervalo: {self.interval_var.get()}s")
        self.lbl_interval.pack(anchor="w", padx=10)
        
        slider_interval = ctk.CTkSlider(
            frame, from_=0.5, to=5.0, number_of_steps=9, variable=self.interval_var,
            command=lambda v: self.update_slider_labels()
        )
        slider_interval.pack(fill="x", padx=10, pady=(0, 10))
        
        # Resumen
        self.config_summary_lbl = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=11, slant="italic"), text_color="gray")
        self.config_summary_lbl.pack(pady=5)
        self.update_slider_labels() # Inicializar textos

    def create_capture_panel(self):
        frame = ctk.CTkFrame(self.sidebar_frame)
        frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(frame, text="ACCIONES", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)

        # Botón Captura
        self.capture_btn = ctk.CTkButton(
            frame, text="INICIAR CAPTURA", font=ctk.CTkFont(weight="bold"),
            height=40, state="disabled", command=self.start_capture_sequence
        )
        self.capture_btn.pack(fill="x", padx=10, pady=5)
        
        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=5)

        # Botones Proceso
        self.process_btn = ctk.CTkButton(
            frame, text="Crear Panorama", state="disabled", command=self.create_panorama
        )
        self.process_btn.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(
            frame, text="Guardar Resultado", fg_color="#388E3C", hover_color="#2E7D32",
            state="disabled", command=self.save_panorama
        )
        self.save_btn.pack(fill="x", padx=10, pady=5)

        # Botones Extra
        extra_frame = ctk.CTkFrame(frame, fg_color="transparent")
        extra_frame.pack(fill="x", padx=5, pady=5)
        
        self.upload_btn = ctk.CTkButton(
            extra_frame, text="📂 Subir", width=80, command=self.import_sequence_from_files
        )
        self.upload_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(
            extra_frame, text="🗑️ Limpiar", width=80, fg_color="#555555", hover_color="#333333",
            command=self.clear_sequence
        )
        self.clear_btn.pack(side="right", padx=5)

    def create_status_panel(self):
        frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        
        ctk.CTkLabel(frame, text="Log de Estado:", anchor="w").pack(fill="x")
        
        self.status_text = ctk.CTkTextbox(frame, height=100, font=("Consolas", 11))
        self.status_text.pack(fill="both", expand=True)
        self.status_text.configure(state="disabled")
        
        self.log_message("Sistema iniciado - Interfaz Moderna")

    # Actualiza las etiquetas de los sliders y el resumen
    def update_slider_labels(self):
        n = self.n_photos_var.get()
        i = self.interval_var.get()
        self.lbl_photos.configure(text=f"Fotos: {n}")
        self.lbl_interval.configure(text=f"Intervalo: {i:.1f}s")
        self.config_summary_lbl.configure(text=f"Tiempo total estimado: ~{n*i:.1f}s")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.configure(state="normal")
        self.status_text.insert("end", f"[{timestamp}] {message}\n")
        self.status_text.see("end")
        self.status_text.configure(state="disabled")

    # Lógica de autoconexión
    def _auto_connect(self):
        found = []
        for i in range(3):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret: found.append(str(i))
                    cap.release()
            except: pass
        
        if found:
            # Actualizar combo box
            self.camera_combo.configure(values=found)
            preferred = "1" if "1" in found else found[0]
            self.camera_index_var.set(preferred)
            self.camera_combo.set(preferred)
            try: self.connect_camera()
            except: pass
        else:
            self.log_message("No se detectaron cámaras automáticamente")

    def search_cameras(self):
        self.log_message("Buscando cámaras...")
        found = []
        for i in range(5):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        found.append(str(i))
                        self.log_message(f"✓ Cámara {i} detectada")
                    cap.release()
            except: pass
            
        if found:
            self.camera_combo.configure(values=found)
            self.camera_combo.set(found[0])
            self.log_message(f"Cámaras encontradas: {found}")
        else:
            self.log_message("No se encontraron cámaras")

    def connect_camera(self):
        try:
            idx = int(self.camera_index_var.get())
            if self.cap: self.cap.release()
            
            self.cap = cv2.VideoCapture(idx)
            if not self.cap.isOpened(): raise Exception("No abre")
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
            # Actualizar UI
            self.connection_label.configure(text="🟢 Conectado", text_color="#00E676")
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.capture_btn.configure(state="normal")
            self.camera_combo.configure(state="disabled")
            
            self.preview_running = True
            self.update_preview()
            self.log_message(f"Conectado a cámara {idx}")
            
        except Exception as e:
            self.log_message(f"Error conexión: {e}")
            if time.time() - self._app_start_time > 2:
                messagebox.showerror("Error", "No se pudo conectar a la cámara")

    def disconnect_camera(self):
        self.preview_running = False
        if self.cap: 
            self.cap.release()
            self.cap = None
            
        self.connection_label.configure(text="🔴 Desconectado", text_color="red")
        self.connect_btn.configure(state="normal")
        self.disconnect_btn.configure(state="disabled")
        self.capture_btn.configure(state="disabled")
        self.camera_combo.configure(state="normal")
        
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            self.preview_canvas.winfo_width()//2, self.preview_canvas.winfo_height()//2,
            text="Desconectado", fill="gray", font=("Arial", 14)
        )
        self.log_message("Cámara desconectada")

    def update_preview(self):
        if not self.preview_running or self.cap is None: return
        
        try:
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.display_image_on_canvas(frame_rgb)
            else:
                self.preview_running = False
        except:
            self.preview_running = False
            
        if self.preview_running:
            self.after(30, self.update_preview)

    def display_image_on_canvas(self, img_rgb, title=None):
        # Función auxiliar para dibujar en el Canvas de Tkinter
        w_canvas = self.preview_canvas.winfo_width()
        h_canvas = self.preview_canvas.winfo_height()
        
        if w_canvas < 10 or h_canvas < 10: return

        h_img, w_img = img_rgb.shape[:2]
        scale = min(w_canvas/w_img, h_canvas/h_img)
        
        # Reducir un poco si es una visualización estática para dejar margen
        if title: scale *= 0.95
            
        new_w, new_h = int(w_img * scale), int(h_img * scale)
        img_resized = cv2.resize(img_rgb, (new_w, new_h))
        
        pil_img = Image.fromarray(img_resized)
        photo = ImageTk.PhotoImage(pil_img)
        
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            w_canvas//2, h_canvas//2, image=photo, anchor="center"
        )
        self.preview_canvas.image = photo
        
        if title:
            self.preview_canvas.create_text(
                w_canvas//2, 20, text=title, fill="#00E676", font=("Arial", 14, "bold")
            )

    def start_capture_sequence(self):
        self.is_capturing = True
        self.captured_images = []
        self.capture_btn.configure(state="disabled", text="📷 Capturando...")
        self.progress_bar.set(0)
        
        n = self.n_photos_var.get()
        interval = self.interval_var.get()
        
        threading.Thread(target=self._capture_thread, args=(n, interval), daemon=True).start()

    def _capture_thread(self, n, interval):
        for i in range(n):
            if not self.is_capturing: break
            
            if self.cap:
                ret, frame = self.cap.read()
                if ret:
                    self.captured_images.append(frame)
                    self.last_sequence_from_camera = True
                    self.log_message(f"Foto {i+1}/{n} capturada")
                    self.progress_bar.set((i+1)/n)
            
            if i < n-1: time.sleep(interval)
            
        self.is_capturing = False
        self.after(0, self._finish_capture)

    def _finish_capture(self):
        self.capture_btn.configure(state="normal", text="INICIAR CAPTURA")
        if self.captured_images:
            self.log_message(f"Secuencia finalizada: {len(self.captured_images)} fotos")
            self.process_btn.configure(state="normal")
            
            last_img = cv2.cvtColor(self.captured_images[-1], cv2.COLOR_BGR2RGB)
            self.display_image_on_canvas(last_img, "Última captura")
        else:
            messagebox.showwarning("Aviso", "No se capturaron imágenes")

    def create_panorama(self):
        if len(self.captured_images) < 2:
            messagebox.showwarning("Error", "Se necesitan mínimo 2 fotos")
            return
            
        self.process_btn.configure(state="disabled", text="⏳ Procesando...")
        self.progress_bar.set(0)
        self.log_message("Iniciando stitching...")
        
        threading.Thread(target=self._stitch_thread, daemon=True).start()

    def _stitch_thread(self):
        try:
            # Preprocesamiento (Aplanamiento)
            imgs = self.captured_images.copy()
            if self.last_sequence_from_camera:
                 self.after(0, lambda: self.log_message("Normalizando exposición..."))
                 imgs = self._apply_photometric_flattening(imgs)
            
            self.after(0, lambda: self.progress_bar.set(0.3))
            
            # Stitching
            stitcher = PanoramaStitcher(output_dir=str(self.output_dir))
            stitcher.images = imgs
            
            result = stitcher.create_panorama()
            if result is None: raise Exception("Fallo en el algoritmo de stitching")
            
            self.after(0, lambda: self.progress_bar.set(0.6))
            self.after(0, lambda: self.log_message("Recortando bordes..."))
            
            stitcher.crop_black_borders()
            self.panorama = stitcher.panorama
            
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, self._finish_panorama_success)
            
        except Exception as e:
            self.after(0, lambda: self._finish_panorama_error(str(e)))

    def _finish_panorama_success(self):
        self.process_btn.configure(state="normal", text="Crear Panorama")
        self.save_btn.configure(state="normal")
        
        h, w = self.panorama.shape[:2]
        self.log_message(f"Panorama ÉXITO: {w}x{h} px")
        
        pano_rgb = cv2.cvtColor(self.panorama, cv2.COLOR_BGR2RGB)
        self.display_image_on_canvas(pano_rgb, "Panorama Final")
        messagebox.showinfo("Éxito", "Panorama creado correctamente")

    def _finish_panorama_error(self, err):
        self.process_btn.configure(state="normal", text="Crear Panorama")
        self.log_message(f"ERROR: {err}")
        messagebox.showerror("Error", f"Fallo al crear panorama:\n{err}")

    def save_panorama(self):
        if self.panorama is None: return
        filename = f"panorama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = filedialog.asksaveasfilename(
            initialfile=filename, defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")]
        )
        if path:
            cv2.imwrite(path, self.panorama)
            self.log_message(f"Guardado en: {Path(path).name}")
            messagebox.showinfo("Guardado", "Archivo guardado exitosamente")

    def import_sequence_from_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("Imágenes", "*.jpg *.png *.jpeg")])
        if not paths: return
        
        loaded = []
        for p in paths:
            img = cv2.imread(p)
            if img is not None: loaded.append(img)
            
        if loaded:
            self.captured_images = loaded
            self.last_sequence_from_camera = False
            self.process_btn.configure(state="normal")
            self.save_btn.configure(state="disabled")
            
            img_rgb = cv2.cvtColor(loaded[-1], cv2.COLOR_BGR2RGB)
            self.display_image_on_canvas(img_rgb, f"Cargada: {Path(paths[-1]).name}")
            self.log_message(f"Importadas {len(loaded)} imágenes")

    def clear_sequence(self):
        self.captured_images = []
        self.panorama = None
        self.progress_bar.set(0)
        self.process_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        
        if self.preview_running: self.update_preview()
        else: 
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                400, 300, text="Listo", fill="gray", font=("Arial", 14)
            )
        self.log_message("Secuencia borrada")

    def _apply_photometric_flattening(self, images):
        processed = []
        if not images: return []
        
        # Calcular media simple para normalizar brillo
        target_mean = 128.0
        for img in images:
            try:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                mean = np.mean(gray)
                if mean > 0:
                    alpha = target_mean / mean
                    img = cv2.convertScaleAbs(img, alpha=alpha, beta=0)
                processed.append(img)
            except:
                processed.append(img)
        return processed

    def run(self):
        self.mainloop()


def main():
    # Crear y ejecutar la aplicación
    app = PanoramaCreatorGUI()
    app.run()


if __name__ == "__main__":
    main()