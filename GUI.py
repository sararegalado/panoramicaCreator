"""
============================================================================
PANORAMA CREATOR - Control de Cámara iPhone
============================================================================
GUI para capturar secuencias de fotos desde iPhone (vía Continuity Camera)
y crear panoramas automáticamente.

Proyecto de Visión por Computador - Universidad de Deusto 2025-2026

REQUISITOS:
- macOS Ventura o posterior
- iPhone con iOS 16+
- Mismo Apple ID en ambos dispositivos
- Bluetooth y WiFi activados

USO:
1. Conecta tu iPhone (aparecerá automáticamente como cámara)
2. Ajusta configuración (número de fotos, intervalo)
3. Click en "Iniciar Captura"
4. Mueve el iPhone horizontalmente para cubrir la escena
5. Espera el procesamiento automático
6. ¡Panorama listo!
============================================================================
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
from pathlib import Path
import time
from datetime import datetime

# Importar nuestro stitcher
from panorama_stitcher import PanoramaStitcher


class PanoramaCreatorGUI:
    """
    Interfaz gráfica para crear panoramas usando iPhone como cámara remota.
    """
    
    def __init__(self):
        """
        Inicializa la ventana principal y todos los componentes.
        """
        # Configuración de la ventana principal
        self.window = tk.Tk()
        self.window.title("🌅 Panorama Creator - iPhone Camera Control")
        self.window.geometry("1200x800")
        self.window.configure(bg='#2b2b2b')
        
        # Variables de estado
        self.cap = None                    # Captura de video (iPhone)
        self.is_capturing = False          # Estado de captura activa
        self.captured_images = []          # Imágenes capturadas
        self.panorama = None               # Panorama resultante
        self.preview_running = False       # Estado del preview en vivo
        
        # Variables de configuración (con valores por defecto)
        self.n_photos_var = tk.IntVar(value=5)        # Número de fotos
        self.interval_var = tk.DoubleVar(value=2.0)   # Intervalo entre fotos (segundos)
        self.camera_index_var = tk.IntVar(value=1)    # Índice de cámara (1=iPhone)
        
        # Directorios
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Construir la interfaz
        self.setup_ui()
        
        # Intentar conectar con el iPhone automáticamente
        self.connect_camera()
        
    def setup_ui(self):
        """
        Construye toda la interfaz de usuario.
        """
        # ==================== TÍTULO ====================
        title_frame = tk.Frame(self.window, bg='#1e1e1e', height=60)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text="🌅 PANORAMA CREATOR",
            font=('Helvetica', 24, 'bold'),
            bg='#1e1e1e',
            fg='#00ff88'
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Control de Cámara iPhone • Stitching Automático",
            font=('Helvetica', 11),
            bg='#1e1e1e',
            fg='#888888'
        )
        subtitle_label.pack()
        
        # ==================== CONTENEDOR PRINCIPAL ====================
        main_container = tk.Frame(self.window, bg='#2b2b2b')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Dividir en dos columnas: izquierda (controles) y derecha (preview)
        
        # ========== COLUMNA IZQUIERDA: CONTROLES ==========
        left_panel = tk.Frame(main_container, bg='#2b2b2b', width=400)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        
        # --- Panel de Estado de Conexión ---
        self.create_connection_panel(left_panel)
        
        # --- Panel de Configuración ---
        self.create_settings_panel(left_panel)
        
        # --- Panel de Controles de Captura ---
        self.create_capture_panel(left_panel)
        
        # --- Panel de Estado ---
        self.create_status_panel(left_panel)
        
        # ========== COLUMNA DERECHA: PREVIEW ==========
        right_panel = tk.Frame(main_container, bg='#1e1e1e')
        right_panel.pack(side='right', fill='both', expand=True)
        
        self.create_preview_panel(right_panel)
        
    def create_connection_panel(self, parent):
        """
        Panel de estado de conexión con el iPhone.
        """
        frame = tk.LabelFrame(
            parent,
            text="📱 Conexión iPhone",
            font=('Helvetica', 12, 'bold'),
            bg='#363636',
            fg='#ffffff',
            padx=15,
            pady=15
        )
        frame.pack(fill='x', pady=(0, 15))
        
        # Estado de conexión
        self.connection_label = tk.Label(
            frame,
            text="🔴 Desconectado",
            font=('Helvetica', 11),
            bg='#363636',
            fg='#ff4444'
        )
        self.connection_label.pack(pady=(0, 10))
        
        # Botones de conexión
        btn_frame = tk.Frame(frame, bg='#363636')
        btn_frame.pack()
        
        self.connect_btn = tk.Button(
            btn_frame,
            text="🔄 Conectar",
            command=self.connect_camera,
            font=('Helvetica', 10),
            bg='#4CAF50',
            fg='white',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        self.connect_btn.pack(side='left', padx=5)
        
        self.disconnect_btn = tk.Button(
            btn_frame,
            text="⏸️ Desconectar",
            command=self.disconnect_camera,
            font=('Helvetica', 10),
            bg='#f44336',
            fg='white',
            padx=15,
            pady=8,
            cursor='hand2',
            state='disabled'
        )
        self.disconnect_btn.pack(side='left', padx=5)
        
        # Selector de cámara
        camera_frame = tk.Frame(frame, bg='#363636')
        camera_frame.pack(pady=(10, 0))
        
        tk.Label(
            camera_frame,
            text="Índice de cámara:",
            bg='#363636',
            fg='#cccccc',
            font=('Helvetica', 9)
        ).pack(side='left', padx=(0, 5))
        
        camera_spinbox = tk.Spinbox(
            camera_frame,
            from_=0,
            to=5,
            textvariable=self.camera_index_var,
            width=5,
            font=('Helvetica', 9)
        )
        camera_spinbox.pack(side='left')
        
    def create_settings_panel(self, parent):
        """
        Panel de configuración de captura.
        """
        frame = tk.LabelFrame(
            parent,
            text="⚙️ Configuración de Captura",
            font=('Helvetica', 12, 'bold'),
            bg='#363636',
            fg='#ffffff',
            padx=15,
            pady=15
        )
        frame.pack(fill='x', pady=(0, 15))
        
        # Número de fotos
        photos_frame = tk.Frame(frame, bg='#363636')
        photos_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            photos_frame,
            text="📸 Número de fotos:",
            bg='#363636',
            fg='#cccccc',
            font=('Helvetica', 10)
        ).pack(anchor='w')
        
        photos_scale = tk.Scale(
            photos_frame,
            from_=2,
            to=20,
            orient='horizontal',
            variable=self.n_photos_var,
            bg='#363636',
            fg='#ffffff',
            highlightthickness=0,
            troughcolor='#555555',
            activebackground='#00ff88'
        )
        photos_scale.pack(fill='x', pady=(5, 0))
        
        # Intervalo entre fotos
        interval_frame = tk.Frame(frame, bg='#363636')
        interval_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            interval_frame,
            text="⏱️ Intervalo (segundos):",
            bg='#363636',
            fg='#cccccc',
            font=('Helvetica', 10)
        ).pack(anchor='w')
        
        interval_scale = tk.Scale(
            interval_frame,
            from_=0.5,
            to=5.0,
            resolution=0.5,
            orient='horizontal',
            variable=self.interval_var,
            bg='#363636',
            fg='#ffffff',
            highlightthickness=0,
            troughcolor='#555555',
            activebackground='#00ff88'
        )
        interval_scale.pack(fill='x', pady=(5, 0))
        
        # Resumen de configuración
        self.config_summary = tk.Label(
            frame,
            text=self.get_config_summary(),
            bg='#363636',
            fg='#00ff88',
            font=('Helvetica', 9, 'italic'),
            justify='left'
        )
        self.config_summary.pack(anchor='w', pady=(10, 0))
        
        # Actualizar resumen cuando cambian los valores
        self.n_photos_var.trace('w', lambda *args: self.update_config_summary())
        self.interval_var.trace('w', lambda *args: self.update_config_summary())
        
    def create_capture_panel(self, parent):
        """
        Panel de botones de control de captura.
        """
        frame = tk.LabelFrame(
            parent,
            text="🎬 Control de Captura",
            font=('Helvetica', 12, 'bold'),
            bg='#363636',
            fg='#ffffff',
            padx=15,
            pady=15
        )
        frame.pack(fill='x', pady=(0, 15))
        
        # Botón principal de captura
        self.capture_btn = tk.Button(
            frame,
            text="📸 INICIAR CAPTURA",
            command=self.start_capture_sequence,
            font=('Helvetica', 13, 'bold'),
            bg='#2196F3',
            fg='white',
            padx=20,
            pady=15,
            cursor='hand2',
            state='disabled'
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
            text="🔗 CREAR PANORAMA",
            command=self.create_panorama,
            font=('Helvetica', 12, 'bold'),
            bg='#FF9800',
            fg='white',
            padx=20,
            pady=12,
            cursor='hand2',
            state='disabled'
        )
        self.process_btn.pack(fill='x', pady=(0, 10))
        
        # Botón de guardar
        self.save_btn = tk.Button(
            frame,
            text="💾 Guardar Panorama",
            command=self.save_panorama,
            font=('Helvetica', 10),
            bg='#4CAF50',
            fg='white',
            padx=15,
            pady=10,
            cursor='hand2',
            state='disabled'
        )
        self.save_btn.pack(fill='x', pady=(0, 5))
        
        # Botón para subir una secuencia desde el file system (nueva opción)
        self.upload_btn = tk.Button(
            frame,
            text="📁 Subir Secuencia",
            command=self.import_sequence_from_files,
            font=('Helvetica', 10),
            bg='#607D8B',
            fg='white',
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.upload_btn.pack(fill='x', pady=(0, 8))

        # Botón de limpiar
        self.clear_btn = tk.Button(
            frame,
            text="🗑️ Nueva Secuencia",
            command=self.clear_sequence,
            font=('Helvetica', 10),
            bg='#757575',
            fg='white',
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.clear_btn.pack(fill='x')
        
    def create_status_panel(self, parent):
        """
        Panel de información de estado.
        """
        frame = tk.LabelFrame(
            parent,
            text="ℹ️ Estado",
            font=('Helvetica', 12, 'bold'),
            bg='#363636',
            fg='#ffffff',
            padx=15,
            pady=15
        )
        frame.pack(fill='both', expand=True)
        
        # Información de estado
        self.status_text = tk.Text(
            frame,
            height=10,
            bg='#1e1e1e',
            fg='#00ff88',
            font=('Courier', 9),
            wrap='word',
            state='disabled'
        )
        self.status_text.pack(fill='both', expand=True)
        
        # Mensaje inicial
        self.log_message("💡 Sistema iniciado")
        self.log_message("📱 Conecta tu iPhone para comenzar")
        
    def create_preview_panel(self, parent):
        """
        Panel de preview de cámara y resultados.
        """
        # Título del preview
        preview_title = tk.Label(
            parent,
            text="🎥 Preview en Vivo",
            font=('Helvetica', 14, 'bold'),
            bg='#1e1e1e',
            fg='#00ff88'
        )
        preview_title.pack(pady=(10, 10))
        
        # Canvas para mostrar video/imagen
        self.preview_canvas = tk.Canvas(
            parent,
            bg='#000000',
            highlightthickness=2,
            highlightbackground='#00ff88'
        )
        self.preview_canvas.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Mensaje cuando no hay preview
        self.preview_canvas.create_text(
            400, 300,
            text="📱 Esperando conexión con iPhone...",
            fill='#888888',
            font=('Helvetica', 14),
            tags='placeholder'
        )
        
    def get_config_summary(self):
        """Genera resumen de configuración."""
        n_photos = self.n_photos_var.get()
        interval = self.interval_var.get()
        total_time = n_photos * interval
        
        return (f"📋 Configuración:\n"
                f"   • {n_photos} fotos\n"
                f"   • {interval}s entre fotos\n"
                f"   • Tiempo total: ~{total_time}s")
    
    def update_config_summary(self):
        """Actualiza el resumen de configuración."""
        self.config_summary.config(text=self.get_config_summary())
    
    def log_message(self, message):
        """
        Añade un mensaje al log de estado.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.config(state='normal')
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')
        self.status_text.config(state='disabled')
    
    def connect_camera(self):
        """
        Conecta con la cámara del iPhone (vía Continuity Camera).
        """
        camera_index = self.camera_index_var.get()
        self.log_message(f"🔄 Intentando conectar con cámara {camera_index}...")
        
        try:
            self.cap = cv2.VideoCapture(camera_index)
            
            # Verificar si se conectó correctamente
            if not self.cap.isOpened():
                raise Exception("No se pudo abrir la cámara")
            
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
            self.log_message(f"❌ Error: {str(e)}")
            messagebox.showerror(
                "Error de Conexión",
                f"No se pudo conectar con el iPhone.\n\n"
                f"Verifica:\n"
                f"• Continuity Camera está activada\n"
                f"• iPhone desbloqueado\n"
                f"• Bluetooth y WiFi activados\n"
                f"• Mismo Apple ID en ambos dispositivos"
            )
    
    def disconnect_camera(self):
        """
        Desconecta la cámara.
        """
        self.preview_running = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.connection_label.config(text="🔴 Desconectado", fg='#ff4444')
        self.connect_btn.config(state='normal')
        self.disconnect_btn.config(state='disabled')
        self.capture_btn.config(state='disabled')
        
        self.log_message("📱 iPhone desconectado")
        
        # Limpiar preview
        self.preview_canvas.delete('all')
        self.preview_canvas.create_text(
            400, 300,
            text="📱 Desconectado",
            fill='#888888',
            font=('Helvetica', 14),
            tags='placeholder'
        )
    
    def update_preview(self):
        """
        Actualiza el preview en vivo de la cámara.
        """
        if not self.preview_running or self.cap is None:
            return
        
        ret, frame = self.cap.read()
        
        if ret:
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
        
        # Programar siguiente actualización
        self.window.after(30, self.update_preview)
    
    def start_capture_sequence(self):
        """
        Inicia la captura de secuencia de fotos.
        """
        self.is_capturing = True
        self.captured_images = []
        self.capture_btn.config(state='disabled', text="⏸️ CAPTURANDO...")
        self.process_btn.config(state='disabled')
        self.progress_var.set(0)
        
        n_photos = self.n_photos_var.get()
        interval = self.interval_var.get()
        
        self.log_message(f"📸 Iniciando captura de {n_photos} fotos...")
        self.log_message(f"⏱️ Intervalo: {interval}s entre fotos")
        self.log_message("💡 Mueve el iPhone lentamente →")
        
        # Ejecutar captura en thread separado para no bloquear UI
        thread = threading.Thread(
            target=self._capture_sequence_thread,
            args=(n_photos, interval)
        )
        thread.daemon = True
        thread.start()
    
    def _capture_sequence_thread(self, n_photos, interval):
        """
        Thread para capturar secuencia sin bloquear la UI.
        """
        for i in range(n_photos):
            if not self.is_capturing:
                break
            
            # Capturar frame
            ret, frame = self.cap.read()
            
            if ret:
                self.captured_images.append(frame)
                progress = ((i + 1) / n_photos) * 100
                self.progress_var.set(progress)
                self.log_message(f"  ✓ Foto {i+1}/{n_photos} capturada")
                
                # Sonido de captura (opcional)
                # print('\a')  # Beep del sistema
                
            else:
                self.log_message(f"  ⚠️ Error capturando foto {i+1}")
            
            # Esperar intervalo (excepto en la última foto)
            if i < n_photos - 1:
                time.sleep(interval)
        
        # Finalizar captura
        self.is_capturing = False
        self.window.after(0, self._finish_capture)
    
    def _finish_capture(self):
        """
        Finaliza el proceso de captura y actualiza UI.
        """
        self.capture_btn.config(state='normal', text="📸 INICIAR CAPTURA")
        
        if len(self.captured_images) > 0:
            self.log_message(f"✅ Captura completada: {len(self.captured_images)} fotos")
            self.process_btn.config(state='normal')
            
            # Mostrar preview de la última imagen capturada
            self.show_image_in_preview(self.captured_images[-1], "Última foto capturada")
        else:
            self.log_message("⚠️ No se capturaron imágenes")
            messagebox.showwarning("Captura Fallida", "No se pudieron capturar imágenes")

    def import_sequence_from_files(self):
        """
        Permite al usuario seleccionar una secuencia de imágenes desde el file system
        y las carga en memoria como si hubieran sido capturadas desde la cámara.
        """
        # Abrir diálogo para seleccionar múltiples archivos de imagen
        # Nota: en macOS tkinter espera que los patrones de filetypes sean
        # una tupla de patrones (no separados por ';'). Usar una tupla evita
        # errores nulos internos del binding con Tk.
        filepaths = filedialog.askopenfilenames(
            title="Selecciona imágenes (múltiples)",
            initialdir='.',
            filetypes=[
                ("Imagenes", ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff")),
                ("Todos los archivos", "*")
            ]
        )

        if not filepaths:
            self.log_message("⚠️ No se seleccionaron archivos")
            return

        self.log_message(f"📁 Cargando {len(filepaths)} archivos desde disco...")

        loaded = []
        for p in filepaths:
            try:
                img = cv2.imread(p)
                if img is None:
                    self.log_message(f"  ⚠️ No se pudo leer: {Path(p).name}")
                else:
                    loaded.append(img)
                    self.log_message(f"  ✓ {Path(p).name} cargada")
            except Exception as e:
                self.log_message(f"  ❌ Error leyendo {Path(p).name}: {str(e)}")

        if len(loaded) == 0:
            messagebox.showwarning("Carga Fallida", "No se pudieron cargar las imágenes seleccionadas")
            return

        # Reemplazar la secuencia capturada actual por las imágenes cargadas
        self.captured_images = loaded
        self.progress_var.set(100)
        self.process_btn.config(state='normal')
        self.save_btn.config(state='disabled')

        # Mostrar la última imagen en el preview
        self.show_image_in_preview(self.captured_images[-1], f"Última: {Path(filepaths[-1]).name}")
        self.log_message(f"✅ Secuencia cargada: {len(self.captured_images)} imágenes listas para procesar")
    
    def create_panorama(self):
        """
        Procesa las imágenes capturadas para crear el panorama.
        """
        if len(self.captured_images) < 2:
            messagebox.showwarning(
                "Imágenes Insuficientes",
                "Se necesitan al menos 2 imágenes para crear un panorama"
            )
            return
        
        self.log_message("🔗 Creando panorama...")
        self.process_btn.config(state='disabled', text="⏳ PROCESANDO...")
        self.progress_var.set(0)
        
        # Procesar en thread separado
        thread = threading.Thread(target=self._create_panorama_thread)
        thread.daemon = True
        thread.start()
    
    def _create_panorama_thread(self):
        """
        Thread para crear panorama sin bloquear UI.
        """
        try:
            # Crear stitcher
            stitcher = PanoramaStitcher(
                input_dir="temp",
                output_dir=str(self.output_dir)
            )
            
            # Asignar imágenes directamente
            stitcher.images = self.captured_images.copy()
            
            self.window.after(0, lambda: self.log_message("  🔍 Detectando características..."))
            self.window.after(0, lambda: self.progress_var.set(25))
            
            # Crear panorama
            result = stitcher.create_panorama(mode='panorama')
            
            if result is None:
                raise Exception("No se pudo crear el panorama")
            
            self.window.after(0, lambda: self.progress_var.set(50))
            self.window.after(0, lambda: self.log_message("  ✂️ Recortando bordes..."))
            
            # Recortar bordes
            stitcher.crop_black_borders()
            
            self.window.after(0, lambda: self.progress_var.set(75))
            
            # Guardar resultado
            self.panorama = stitcher.panorama
            
            self.window.after(0, lambda: self.progress_var.set(100))
            self.window.after(0, self._finish_panorama_success)
            
        except Exception as e:
            self.window.after(0, lambda: self._finish_panorama_error(str(e)))
    
    def _finish_panorama_success(self):
        """
        Finaliza procesamiento exitoso.
        """
        self.process_btn.config(state='disabled', text="🔗 CREAR PANORAMA")
        self.save_btn.config(state='normal')
        
        h, w = self.panorama.shape[:2]
        megapixels = (w * h) / (1024 * 1024)
        
        self.log_message(f"✅ ¡Panorama creado exitosamente!")
        self.log_message(f"📐 Dimensiones: {w}x{h} ({megapixels:.1f} MP)")
        
        # Mostrar panorama en preview
        self.show_image_in_preview(self.panorama, "Panorama Final")
        
        messagebox.showinfo(
            "¡Éxito!",
            f"Panorama creado exitosamente\n\n"
            f"Dimensiones: {w}x{h}\n"
            f"Tamaño: {megapixels:.1f} megapíxeles"
        )
    
    def _finish_panorama_error(self, error_msg):
        """
        Maneja error en procesamiento.
        """
        self.process_btn.config(state='normal', text="🔗 CREAR PANORAMA")
        self.log_message(f"❌ Error: {error_msg}")
        
        messagebox.showerror(
            "Error de Procesamiento",
            f"No se pudo crear el panorama.\n\n"
            f"Error: {error_msg}\n\n"
            f"Consejos:\n"
            f"• Asegúrate de tener 30-50% de solapamiento\n"
            f"• Toma las fotos desde el mismo punto\n"
            f"• Mueve solo la cámara, no te muevas"
        )
    
    def show_image_in_preview(self, image, title=""):
        """
        Muestra una imagen en el preview.
        """
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
                    font=('Helvetica', 12, 'bold')
                )
    
    def save_panorama(self):
        """
        Guarda el panorama en disco.
        """
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
            self.log_message(f"💾 Panorama guardado: {Path(filepath).name}")
            messagebox.showinfo("Guardado", f"Panorama guardado exitosamente en:\n{filepath}")
    
    def clear_sequence(self):
        """
        Limpia la secuencia actual para empezar de nuevo.
        """
        self.captured_images = []
        self.panorama = None
        self.progress_var.set(0)
        
        self.process_btn.config(state='disabled')
        self.save_btn.config(state='disabled')
        
        self.log_message("🗑️ Secuencia limpiada - Lista para nueva captura")
        
        # Volver al preview en vivo
        if self.cap and self.cap.isOpened():
            self.preview_running = True
            self.update_preview()
    
    def run(self):
        """
        Inicia el loop principal de la aplicación.
        """
        # Manejar cierre de ventana
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar aplicación
        self.log_message("🚀 Aplicación lista")
        self.window.mainloop()
    
    def on_closing(self):
        """
        Maneja el cierre de la aplicación.
        """
        self.preview_running = False
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        self.window.destroy()


def main():
    """
    Función principal - Punto de entrada.
    """
    print("\n" + "="*70)
    print("🌅 PANORAMA CREATOR - iPhone Camera Control")
    print("="*70)
    print("Iniciando GUI...\n")
    
    # Crear y ejecutar la aplicación
    app = PanoramaCreatorGUI()
    app.run()


if __name__ == "__main__":
    main()