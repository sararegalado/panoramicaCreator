import cv2
import numpy as np
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
from pathlib import Path
import time
from datetime import datetime
import platform

# Importar nuestro stitcher
from panorama_stitcher import PanoramaStitcher

# Interfaz gráfica para la creación de panoramas
class PanoramaCreatorGUI:
    def __init__(self):
        # Configuración de la ventana principal
        self.window = tk.Tk()
        self.window.title("Panorama Creator")
        self.window.geometry("1200x800")
        
        # Tema minimalista y claro
        self.window.configure(bg='#ffffff')
        
        # Configuracion de fuentes
        sys_plat = platform.system()
        if sys_plat == 'Darwin':
            base_family = 'Helvetica Neue'
        elif sys_plat == 'Windows':
            base_family = 'Segoe UI'
        else:
            base_family = 'DejaVu Sans'

        self.base_font_family = base_family

        try:
            default_font = tkfont.nametofont('TkDefaultFont')
            default_font.configure(family=self.base_font_family, size=11)
        except Exception:
            pass

        # Ajustes para otros tipos de fuentes usados por Tk
        for name, size in (('TkHeadingFont', 12), ('TkTextFont', 11), ('TkFixedFont', 10)):
            try:
                f = tkfont.nametofont(name)
                f.configure(family=self.base_font_family, size=size)
            except Exception:
                pass
        
        # Variables de estado
        self.cap = None                    
        self.is_capturing = False          
        self.captured_images = []          
        self.panorama = None               
        self.preview_running = False       
        self.last_sequence_from_camera = False  
        
        # Timestamp de inicio para detectar conexión automática vs manual
        import time
        self._app_start_time = time.time()
        
        # Variables de configuración (con valores por defecto)
        self.n_photos_var = tk.IntVar(value=5)        
        self.interval_var = tk.DoubleVar(value=2.0)   
        self.camera_index_var = tk.IntVar(value=0)    
        
        # Directorios
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Construir la interfaz
        self.setup_ui()
        
        # Intentar conectar con el iPhone automáticamente
        # Usar after para no bloquear el inicio de la UI
        self.window.after(100, self._auto_connect)


    # Construir interfaz de usuario    
    def setup_ui(self):
        # Titulo
        title_frame = tk.Frame(self.window, bg='#ffffff', height=60)
        title_frame.pack(fill='x', pady=(0, 10))
        title_label = tk.Label(
            title_frame,
            text="CREA TU PANORÁMICA",
            font=(self.base_font_family, 22, 'bold'),
            bg='#ffffff',
            fg='#111111'
        )
        title_label.pack(pady=10)
        subtitle_label = tk.Label(
            title_frame,
            text="Control de cámara • Stitching automático",
            font=(self.base_font_family, 10),
            bg='#ffffff',
            fg='#666666'
        )
        subtitle_label.pack()
        
        # Contenedor principal
        main_container = tk.Frame(self.window, bg='#ffffff')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Dividir en dos columnas: izquierda (controles) y derecha (preview)
        
        # Col. izquierda
        left_panel = tk.Frame(main_container, bg='#ffffff', width=400)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        
        # Panel de Estado de Conexión
        self.create_connection_panel(left_panel)
        
        # Panel de Configuración
        self.create_settings_panel(left_panel)
        
        # Panel de Controles de Captura
        self.create_capture_panel(left_panel)
        
        # Panel de Estado
        self.create_status_panel(left_panel)
        
        # Col. derecha
        right_panel = tk.Frame(main_container, bg='#ffffff')
        right_panel.pack(side='right', fill='both', expand=True)
        
        self.create_preview_panel(right_panel)
    
    # Panel de estado de conexion con el iPhone
    def create_connection_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Conexión",
            font=(self.base_font_family, 12, 'bold'),
            bg='#f7f7f7',
            fg='#222222',
            padx=12,
            pady=12,
            relief='flat'
        )
        frame.pack(fill='x', pady=(0, 15))
        
        # Estado de conexión
        self.connection_label = tk.Label(
            frame,
            text="Desconectado",
            font=(self.base_font_family, 11),
            bg='#f7f7f7',
            fg='#cc0000'
        )
        self.connection_label.pack(pady=(0, 10))
        
        # Botones de conexión
        btn_frame = tk.Frame(frame, bg='#f7f7f7')
        btn_frame.pack()
        
        self.connect_btn = tk.Button(
            btn_frame,
            text="Conectar",
            command=self.connect_camera,
            font=(self.base_font_family, 10),
            bg='#f0f0f0',
            fg='#111111',
            padx=12,
            pady=6,
            cursor='hand2',
            relief='flat'
        )
        self.connect_btn.pack(side='left', padx=5)
        
        self.disconnect_btn = tk.Button(
            btn_frame,
            text="Desconectar",
            command=self.disconnect_camera,
            font=(self.base_font_family, 10),
            bg='#f0f0f0',
            fg='#111111',
            padx=12,
            pady=6,
            cursor='hand2',
            state='disabled',
            relief='flat'
        )
        self.disconnect_btn.pack(side='left', padx=5)
        
        # Selector de cámara
        camera_frame = tk.Frame(frame, bg='#f7f7f7')
        camera_frame.pack(pady=(10, 0))
        
        tk.Label(
            camera_frame,
            text="Índice de cámara:",
            bg='#f7f7f7',
            fg='#333333',
            font=(self.base_font_family, 9)
        ).pack(side='left', padx=(0, 5))
        
        camera_spinbox = tk.Spinbox(
            camera_frame,
            from_=0,
            to=5,
            textvariable=self.camera_index_var,
            width=5,
            font=(self.base_font_family, 9)
        )
        camera_spinbox.pack(side='left', padx=(0, 5))
        
        # Botón para buscar cámaras
        search_cam_btn = tk.Button(
            camera_frame,
            text="🔍",
            command=self.search_cameras,
            font=(self.base_font_family, 9),
            bg='#f0f0f0',
            fg='#111111',
            padx=5,
            pady=2,
            cursor='hand2',
            relief='flat'
        )
        search_cam_btn.pack(side='left')

    # Panel de configuracion de captura   
    def create_settings_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Configuración",
            font=(self.base_font_family, 12, 'bold'),
            bg='#f7f7f7',
            fg='#222222',
            padx=12,
            pady=12,
            relief='flat'
        )
        frame.pack(fill='x', pady=(0, 15))
        
        # Número de fotos
        photos_frame = tk.Frame(frame, bg='#f7f7f7')
        photos_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            photos_frame,
            text="Número de fotos:",
            bg='#f7f7f7',
            fg='#333333',
            font=(self.base_font_family, 10)
        ).pack(anchor='w')
        
        photos_scale = tk.Scale(
            photos_frame,
            from_=2,
            to=20,
            orient='horizontal',
            variable=self.n_photos_var,
            bg='#f7f7f7',
            fg='#333333',
            highlightthickness=0,
            troughcolor='#dddddd',
            activebackground='#aaaaaa'
        )
        photos_scale.pack(fill='x', pady=(5, 0))
        
        # Intervalo entre fotos
        interval_frame = tk.Frame(frame, bg='#f7f7f7')
        interval_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            interval_frame,
            text="Intervalo (segundos):",
            bg='#f7f7f7',
            fg='#333333',
            font=(self.base_font_family, 10)
        ).pack(anchor='w')
        
        interval_scale = tk.Scale(
            interval_frame,
            from_=0.5,
            to=5.0,
            resolution=0.5,
            orient='horizontal',
            variable=self.interval_var,
            bg='#f7f7f7',
            fg='#333333',
            highlightthickness=0,
            troughcolor='#dddddd',
            activebackground='#aaaaaa'
        )
        interval_scale.pack(fill='x', pady=(5, 0))
        
        # Resumen de configuración
        self.config_summary = tk.Label(
            frame,
            text=self.get_config_summary(),
            bg='#f7f7f7',
            fg='#333333',
            font=(self.base_font_family, 9, 'italic'),
            justify='left'
        )
        self.config_summary.pack(anchor='w', pady=(10, 0))
        
        # Actualizar resumen cuando cambian los valores
        self.n_photos_var.trace('w', lambda *args: self.update_config_summary())
        self.interval_var.trace('w', lambda *args: self.update_config_summary())
    
    # Panel de botones de control de captura
    def create_capture_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Captura",
            font=(self.base_font_family, 12, 'bold'),
            bg='#f7f7f7',
            fg='#222222',
            padx=12,
            pady=12,
            relief='flat'
        )
        frame.pack(fill='x', pady=(0, 15))
        
        # Botón principal de captura
        self.capture_btn = tk.Button(
            frame,
            text="Iniciar captura",
            command=self.start_capture_sequence,
            font=(self.base_font_family, 12, 'bold'),
            bg='#f0f0f0',
            fg='#111111',
            padx=16,
            pady=10,
            cursor='hand2',
            state='disabled',
            relief='flat'
        )
        self.capture_btn.pack(fill='x', pady=(0, 10))
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # Botón de procesamiento
        self.process_btn = tk.Button(
            frame,
            text="Crear panorama",
            command=self.create_panorama,
            font=(self.base_font_family, 12, 'bold'),
            bg='#f0f0f0',
            fg='#111111',
            padx=16,
            pady=10,
            cursor='hand2',
            state='disabled',
            relief='flat'
        )
        self.process_btn.pack(fill='x', pady=(0, 10))
        
        # Botón de guardar
        self.save_btn = tk.Button(
            frame,
            text="Guardar panorama",
            command=self.save_panorama,
            font=(self.base_font_family, 10),
            bg='#f0f0f0',
            fg='#111111',
            padx=12,
            pady=8,
            cursor='hand2',
            state='disabled',
            relief='flat'
        )
        self.save_btn.pack(fill='x', pady=(0, 5))
        
        # Botón para subir una secuencia desde el file system (nueva opción)
        self.upload_btn = tk.Button(
            frame,
            text="Subir secuencia",
            command=self.import_sequence_from_files,
            font=(self.base_font_family, 10),
            bg='#f0f0f0',
            fg='#111111',
            padx=12,
            pady=8,
            cursor='hand2',
            relief='flat'
        )
        self.upload_btn.pack(fill='x', pady=(0, 8))

        # Botón de limpiar
        self.clear_btn = tk.Button(
            frame,
            text="🗑️ Nueva Secuencia",
            command=self.clear_sequence,
            font=(self.base_font_family, 10),
            bg='#757575',
            fg='white',
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.clear_btn.pack(fill='x')

    # Panel de información de estado   
    def create_status_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Estado",
            font=(self.base_font_family, 12, 'bold'),
            bg='#f7f7f7',
            fg='#222222',
            padx=15,
            pady=15
        )
        frame.pack(fill='both', expand=True)
        
        # Información de estado
        self.status_text = tk.Text(
            frame,
            height=10,
            bg='#ffffff',
            fg='#222222',
            font=('Courier', 9),
            wrap='word',
            state='disabled'
        )
        self.status_text.pack(fill='both', expand=True)
        
        # Mensaje inicial
        self.log_message("💡 Sistema iniciado")
        self.log_message("📱 Opciones:")
        self.log_message("   1. Click 'Conectar' para usar iPhone")
        self.log_message("   2. Click 'Subir secuencia' para usar archivos")
    
    # Panel de preview
    def create_preview_panel(self, parent):
        # Título del preview
        preview_title = tk.Label(
            parent,
            text="Preview en vivo",
            font=(self.base_font_family, 14, 'bold'),
            bg='#ffffff',
            fg='#111111'
        )
        preview_title.pack(pady=(10, 10))
        
        # Canvas para mostrar video/imagen
        self.preview_canvas = tk.Canvas(
            parent,
            bg='#ffffff',
            highlightthickness=1,
            highlightbackground='#dddddd'
        )
        self.preview_canvas.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Mensaje cuando no hay preview
        self.preview_canvas.create_text(
            400, 300,
            text="Esperando conexión con iPhone...",
            fill='#999999',
            font=(self.base_font_family, 14),
            tags='placeholder'
        )

    # Generar resumen de configuracion    
    def get_config_summary(self):
        n_photos = self.n_photos_var.get()
        interval = self.interval_var.get()
        total_time = n_photos * interval
        
        return (f"Configuración:\n"
                f"   • {n_photos} fotos\n"
                f"   • {interval}s entre fotos\n"
                f"   • Tiempo total: ~{total_time}s")
    
    def update_config_summary(self):
        self.config_summary.config(text=self.get_config_summary())
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.config(state='normal')
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')
        self.status_text.config(state='disabled')
    
    # Intenta conectarse al iphone al principio
    def _auto_connect(self):
        # Buscar cámaras disponibles
        found = []
        for i in range(3):  # Solo buscar 0, 1, 2
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        found.append(i)
                    cap.release()
            except:
                pass
        
        if not found:
            self.log_message("No se encontraron cámaras disponibles")
            return
        
        # Preferir índice 1 si existe (iPhone)
        if 1 in found:
            self.camera_index_var.set(1)
            self.log_message("iPhone detectado (índice 1)")
        else:
            self.camera_index_var.set(found[0])
            self.log_message(f"Usando cámara {found[0]}")
        
        # Intentar conectar
        try:
            self.connect_camera()
        except Exception as e:
            pass
    
    # Busca camaras disponibles
    def search_cameras(self):
        self.log_message("Buscando cámaras disponibles...")
        
        found = []
        for i in range(6):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        found.append(i)
                        self.log_message(f"  ✓ Cámara {i}: {w}x{h}")
                    cap.release()
            except:
                pass
        
        if not found:
            self.log_message("No se encontraron cámaras")
        else:
            self.log_message(f"{len(found)} cámara(s) encontrada(s): {found}")
            if len(found) == 1:
                self.camera_index_var.set(found[0])
                self.log_message(f"→ Usando cámara {found[0]}")
            else:
                msg = "Cámaras encontradas:\n\n"
                for idx in found:
                    cam_type = "iPhone (Continuity)" if idx == 1 else f"Cámara {idx}"
                    msg += f"• Índice {idx}: {cam_type}\n"
                msg += f"\n¿Usar cámara {found[0]}?"
                
                if messagebox.askyesno("Cámaras Encontradas", msg):
                    self.camera_index_var.set(found[0])
                    self.log_message(f"→ Usando cámara {found[0]}")
    

    # Conecta con la camara del iPhone (via Continuity Camera)
    def connect_camera(self):
        camera_index = self.camera_index_var.get()
        self.log_message(f"Intentando conectar con cámara {camera_index}...")
        
        try:
            # Liberar cámara anterior si existe
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            
            self.cap = cv2.VideoCapture(camera_index)
            
            # Verificar si se conectó correctamente
            if not self.cap.isOpened():
                self.cap = None
                raise Exception(f"No se pudo abrir la cámara en índice {camera_index}")
            
            # Intentar leer un frame para verificar que funciona
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.cap.release()
                self.cap = None
                raise Exception("La cámara no responde correctamente")
            
            # Configurar resolución alta
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
            # Actualizar UI
            self.connection_label.config(text="🟢 iPhone Conectado", fg='#00ff88')
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
            self.capture_btn.config(state='normal')
            
            self.log_message("✅ iPhone conectado exitosamente")
            self.log_message(f"📷 Resolución: {int(self.cap.get(3))}x{int(self.cap.get(4))}")
            
            # Iniciar preview en vivo
            self.preview_running = True
            self.update_preview()
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            
            import time
            if not hasattr(self, '_app_start_time'):
                self._app_start_time = time.time()
            
            time_since_start = time.time() - self._app_start_time
            
            # Si han pasado más de 2 segundos, el usuario hizo click manualmente
            if time_since_start > 2.0:
                messagebox.showwarning(
                    "Cámara No Disponible",
                    f"No se pudo conectar con la cámara (índice {camera_index}).\n\n"
                )
    
    # Desconectar camara
    def disconnect_camera(self):
        self.preview_running = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.connection_label.config(text="🔴 Desconectado", fg='#ff4444')
        self.connect_btn.config(state='normal')
        self.disconnect_btn.config(state='disabled')
        self.capture_btn.config(state='disabled')
        
        self.log_message("iPhone desconectado")
        
        # Limpiar preview
        self.preview_canvas.delete('all')
        self.preview_canvas.create_text(
            400, 300,
            text="Desconectado",
            fill='#999999',
            font=(self.base_font_family, 14),
            tags='placeholder'
        )
    
    # Actualizar el preview en vivo de la camara
    def update_preview(self):
        if not self.preview_running or self.cap is None:
            return
        
        try:
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                # Convertir de BGR a RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Redimensionar para ajustar al canvas
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                if canvas_width > 1 and canvas_height > 1:
                    h, w = frame_rgb.shape[:2]
                    scale = min(canvas_width / w, canvas_height / h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    
                    frame_resized = cv2.resize(frame_rgb, (new_w, new_h))
                    
                    # Convertir a ImageTk
                    image = Image.fromarray(frame_resized)
                    photo = ImageTk.PhotoImage(image)
                    
                    # Actualizar canvas
                    self.preview_canvas.delete('all')
                    self.preview_canvas.create_image(
                        canvas_width // 2,
                        canvas_height // 2,
                        image=photo,
                        anchor='center'
                    )
                    self.preview_canvas.image = photo  # Mantener referencia
            else:
                # Si no se puede leer frame, detener preview
                self.preview_running = False
                self.log_message("Preview detenido - no se pueden leer frames")
                return
                
        except Exception as e:
            # Manejar errores silenciosamente y detener preview
            self.preview_running = False
            self.log_message(f"Preview detenido - error: {str(e)}")
            return
        
        # Programar siguiente actualización solo si preview sigue activo
        if self.preview_running:
            self.window.after(30, self.update_preview)
    
    # Inicia la captura de secuencia de fotos
    def start_capture_sequence(self):
        self.is_capturing = True
        self.captured_images = []
        self.capture_btn.config(state='disabled', text="⏸️ CAPTURANDO...")
        self.process_btn.config(state='disabled')
        self.progress_var.set(0)
        
        n_photos = self.n_photos_var.get()
        interval = self.interval_var.get()
        
        self.log_message(f"Iniciando captura de {n_photos} fotos...")
        self.log_message(f"Intervalo: {interval}s entre fotos")
        
        # Ejecutar captura en thread separado para no bloquear UI
        thread = threading.Thread(
            target=self._capture_sequence_thread,
            args=(n_photos, interval)
        )
        thread.daemon = True
        thread.start()
    
    def _capture_sequence_thread(self, n_photos, interval):
        for i in range(n_photos):
            if not self.is_capturing:
                break
            
            # Capturar frame
            ret, frame = self.cap.read()
            
            if ret:
                self.captured_images.append(frame)
                # Marcar que la secuencia proviene de la cámara
                self.last_sequence_from_camera = True
                progress = ((i + 1) / n_photos) * 100
                self.progress_var.set(progress)
                self.log_message(f"  ✓ Foto {i+1}/{n_photos} capturada")
                
                # Sonido de captura (opcional)
                # print('\a')
                
            else:
                self.log_message(f"Error capturando foto {i+1}")
            
            # Esperar intervalo (excepto en la última foto)
            if i < n_photos - 1:
                time.sleep(interval)
        
        # Finalizar captura
        self.is_capturing = False
        self.window.after(0, self._finish_capture)
    
    # Finaliza proceso de captura y actualiza UI
    def _finish_capture(self):
        self.capture_btn.config(state='normal', text="📸 INICIAR CAPTURA")
        
        if len(self.captured_images) > 0:
            self.log_message(f"Captura completada: {len(self.captured_images)} fotos")
            self.process_btn.config(state='normal')
            
            # Mostrar preview de la última imagen capturada
            self.show_image_in_preview(self.captured_images[-1], "Última foto capturada")
        else:
            self.log_message("No se capturaron imágenes")
            messagebox.showwarning("Captura Fallida", "No se pudieron capturar imágenes")

    # Permite seleccionar secuencia de imgs desde el file system y las carga como si se hubieran sacado con la cámara
    def import_sequence_from_files(self):
        filepaths = filedialog.askopenfilenames(
            title="Selecciona imágenes (múltiples)",
            initialdir='.',
            filetypes=[
                ("Imagenes", ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff")),
                ("Todos los archivos", "*")
            ]
        )

        if not filepaths:
            self.log_message("No se seleccionaron archivos")
            return

        self.log_message(f"Cargando {len(filepaths)} archivos desde disco...")

        loaded = []
        for p in filepaths:
            try:
                img = cv2.imread(p)
                if img is None:
                    self.log_message(f"No se pudo leer: {Path(p).name}")
                else:
                    loaded.append(img)
                    self.log_message(f"{Path(p).name} cargada")
            except Exception as e:
                self.log_message(f"Error leyendo {Path(p).name}: {str(e)}")

        if len(loaded) == 0:
            messagebox.showwarning("Carga Fallida", "No se pudieron cargar las imágenes seleccionadas")
            return

        # Reemplazar la secuencia capturada actual por las imágenes cargadas
        self.captured_images = loaded
        # Indicar que esta secuencia NO viene de la cámara (para no aplicar flattening)
        self.last_sequence_from_camera = False
        self.progress_var.set(100)
        self.process_btn.config(state='normal')
        self.save_btn.config(state='disabled')

        # Mostrar la última imagen en el preview
        self.show_image_in_preview(self.captured_images[-1], f"Última: {Path(filepaths[-1]).name}")
        self.log_message(f"Secuencia cargada: {len(self.captured_images)} imágenes listas para procesar")
    
    # Procesa imagenes captuardas para crear el panorama
    def create_panorama(self):
        if len(self.captured_images) < 2:
            messagebox.showwarning(
                "Imágenes Insuficientes",
                "Se necesitan al menos 2 imágenes para crear un panorama"
            )
            return
        
        self.log_message("Creando panorama...")
        self.process_btn.config(state='disabled', text="⏳ PROCESANDO...")
        self.progress_var.set(0)
        
        # Procesar en thread separado
        thread = threading.Thread(target=self._create_panorama_thread)
        thread.daemon = True
        thread.start()
    
    # Crear el panorama sin bloquear UI
    def _create_panorama_thread(self):
        try:
            # Si la secuencia proviene de la cámara, aplicar técnicas de "aplanamiento"
            if self.last_sequence_from_camera:
                self.window.after(0, lambda: self.log_message("Aplicando aplanamiento fotométrico a las imágenes..."))
                # Ejecutar preprocesado (puede tardar un poco)
                try:
                    images_to_process = self._apply_photometric_flattening(self.captured_images)
                except Exception as e:
                    self.window.after(0, lambda: self.log_message(f"Error en aplanamiento: {e}"))
                    images_to_process = self.captured_images.copy()
            else:
                images_to_process = self.captured_images.copy()

            # Crear stitcher
            stitcher = PanoramaStitcher(
                output_dir=str(self.output_dir)
            )

            # Asignar imágenes (procesadas o originales según su origen)
            stitcher.images = images_to_process

            self.window.after(0, lambda: self.log_message("Detectando características..."))
            self.window.after(0, lambda: self.progress_var.set(25))

            # Crear panorama
            result = stitcher.create_panorama(mode='panorama')
            
            if result is None:
                raise Exception("No se pudo crear el panorama")
            
            self.window.after(0, lambda: self.progress_var.set(50))
            self.window.after(0, lambda: self.log_message("Recortando bordes..."))
            
            # Recortar bordes
            stitcher.crop_black_borders()
            
            self.window.after(0, lambda: self.progress_var.set(75))
            
            # Guardar resultado
            self.panorama = stitcher.panorama
            
            self.window.after(0, lambda: self.progress_var.set(100))
            self.window.after(0, self._finish_panorama_success)
            
        except Exception as e:
            self.window.after(0, lambda: self._finish_panorama_error(str(e)))
    
    # Finaliza procesamiento exitoso
    def _finish_panorama_success(self):
        self.process_btn.config(state='disabled', text="🔗 CREAR PANORAMA")
        self.save_btn.config(state='normal')
        
        h, w = self.panorama.shape[:2]
        megapixels = (w * h) / (1024 * 1024)
        
        self.log_message(f"¡Panorama creado exitosamente!")
        self.log_message(f"Dimensiones: {w}x{h} ({megapixels:.1f} MP)")
        
        # Mostrar panorama en preview
        self.show_image_in_preview(self.panorama, "Panorama Final")
        
        messagebox.showinfo(
            "¡Éxito!",
            f"Panorama creado exitosamente\n\n"
            f"Dimensiones: {w}x{h}\n"
            f"Tamaño: {megapixels:.1f} megapíxeles"
        )
    
    # Manejo de error en procesamiento
    def _finish_panorama_error(self, error_msg):
        """
        Maneja error en procesamiento.
        """
        self.process_btn.config(state='normal', text="🔗 CREAR PANORAMA")
        self.log_message(f"Error: {error_msg}")
        
        messagebox.showerror(
            "Error de Procesamiento",
            f"No se pudo crear el panorama.\n\n"
            f"Error: {error_msg}\n\n"
            f"Consejos:\n"
            f"• Asegúrate de tener 30-50% de solapamiento\n"
            f"• Toma las fotos desde el mismo punto\n"
            f"• Mueve solo la cámara, no te muevas"
        )
    
    # Muestra imagen en preview
    def show_image_in_preview(self, image, title=""):
        # Convertir de BGR a RGB si es necesario
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # Obtener dimensiones del canvas
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            h, w = image_rgb.shape[:2]
            scale = min(canvas_width / w, canvas_height / h) * 0.95
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            image_resized = cv2.resize(image_rgb, (new_w, new_h))
            
            # Convertir a ImageTk
            pil_image = Image.fromarray(image_resized)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Actualizar canvas
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=photo,
                anchor='center'
            )
            self.preview_canvas.image = photo
            
            # Añadir título si se proporciona
            if title:
                self.preview_canvas.create_text(
                    canvas_width // 2,
                    20,
                    text=title,
                    fill='#00ff88',
                    font=(self.base_font_family, 12, 'bold')
                )

    # Aplanar la apariencia de una secuencia tomada con la camara
    def _apply_photometric_flattening(self, images):
        processed = []

        # Calcular la luminancia media objetivo (mediana de medias)
        means = []
        for img in images:
            try:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                means.append(np.mean(gray))
            except Exception:
                means.append(0)

        if len(means) == 0:
            return images.copy()

        target = float(np.median(means)) if np.median(means) > 0 else 128.0

        for img in images:
            try:
                imgf = img.astype(np.float32)

                # Balance de blancos:
                b_mean, g_mean, r_mean = np.mean(imgf[:, :, 0]), np.mean(imgf[:, :, 1]), np.mean(imgf[:, :, 2])
                mean = (b_mean + g_mean + r_mean) / 3.0 + 1e-8
                imgf[:, :, 0] *= (mean / (b_mean + 1e-8))
                imgf[:, :, 1] *= (mean / (g_mean + 1e-8))
                imgf[:, :, 2] *= (mean / (r_mean + 1e-8))

                imgf = np.clip(imgf, 0, 255).astype(np.uint8)

                # Normalización de exposición (lineal)
                gray = cv2.cvtColor(imgf, cv2.COLOR_BGR2GRAY)
                current_mean = np.mean(gray) + 1e-8
                alpha = target / current_mean
                imgf = cv2.convertScaleAbs(imgf, alpha=float(alpha), beta=0)

                # Mejora de contraste local con CLAHE en L channel
                lab = cv2.cvtColor(imgf, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                lab = cv2.merge((l, a, b))
                imgf = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

                processed.append(imgf)
            except Exception:
                # Si ocurre cualquier error, devolver la copia original
                processed.append(img.copy())

        return processed
    
    # Guardar panorama
    def save_panorama(self):
        if self.panorama is None:
            return
        
        # Generar nombre con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"panorama_{timestamp}.png"
        
        # Diálogo de guardado
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=default_filename,
            initialdir=str(self.output_dir),
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            cv2.imwrite(filepath, self.panorama)
            self.log_message(f"Panorama guardado: {Path(filepath).name}")
            messagebox.showinfo("Guardado", f"Panorama guardado exitosamente en:\n{filepath}")
    
    # Limpiar secuencia actual para empezar de nuevo
    def clear_sequence(self):
        self.captured_images = []
        self.panorama = None
        self.progress_var.set(0)
        
        self.process_btn.config(state='disabled')
        self.save_btn.config(state='disabled')
        
        self.log_message("Secuencia limpiada - Lista para nueva captura")
        
        # Volver al preview en vivo
        if self.cap and self.cap.isOpened():
            self.preview_running = True
            self.update_preview()
    
    # Loop principal
    def run(self):
        # Manejar cierre de ventana
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar aplicación
        self.log_message("Aplicación lista")
        self.window.mainloop()
    
    def on_closing(self):
        self.preview_running = False
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        self.window.destroy()


def main():
    # Crear y ejecutar la aplicación
    app = PanoramaCreatorGUI()
    app.run()


if __name__ == "__main__":
    main()