"""
============================================================================
CAPTURE CONTROLLER - Control de Captura
============================================================================
Gestiona la captura de secuencias de fotos desde la cámara
"""

import time
import threading


class CaptureController:
    """Controla la captura de secuencias de fotos."""
    
    def __init__(self, camera_manager):
        self.camera_manager = camera_manager
        self.captured_images = []
        self.is_capturing = False
        self.capture_callback = None
        self.progress_callback = None
    
    def set_callbacks(self, capture_callback=None, progress_callback=None):
        """
        Configura callbacks para notificar eventos.
        
        Args:
            capture_callback: Función llamada cuando se captura cada foto (image, index, total)
            progress_callback: Función llamada para reportar progreso (index, total)
        """
        self.capture_callback = capture_callback
        self.progress_callback = progress_callback
    
    def start_sequence(self, n_photos, interval, callback_done=None):
        """
        Inicia la captura de una secuencia de fotos.
        
        Args:
            n_photos (int): Número de fotos a capturar
            interval (float): Intervalo en segundos entre fotos
            callback_done: Función llamada al completar (success, images)
        """
        if self.is_capturing:
            return False
        
        self.is_capturing = True
        self.captured_images = []
        
        # Ejecutar en thread separado
        thread = threading.Thread(
            target=self._capture_thread,
            args=(n_photos, interval, callback_done)
        )
        thread.daemon = True
        thread.start()
        
        return True
    
    def _capture_thread(self, n_photos, interval, callback_done):
        """Thread interno para capturar fotos."""
        success = True
        
        for i in range(n_photos):
            if not self.is_capturing:
                success = False
                break
            
            # Capturar frame
            ret, frame = self.camera_manager.read_frame()
            
            if ret and frame is not None:
                self.captured_images.append(frame.copy())
                
                # Notificar captura
                if self.capture_callback:
                    self.capture_callback(frame, i + 1, n_photos)
                
                # Notificar progreso
                if self.progress_callback:
                    progress = ((i + 1) / n_photos) * 100
                    self.progress_callback(i + 1, n_photos, progress)
            else:
                success = False
                break
            
            # Esperar intervalo (excepto en la última foto)
            if i < n_photos - 1:
                time.sleep(interval)
        
        self.is_capturing = False
        
        # Notificar finalización
        if callback_done:
            callback_done(success, self.captured_images)
    
    def stop_sequence(self):
        """Detiene la captura en curso."""
        self.is_capturing = False
    
    def clear_images(self):
        """Limpia las imágenes capturadas."""
        self.captured_images = []
    
    def get_images(self):
        """Obtiene las imágenes capturadas."""
        return self.captured_images.copy()
    
    def load_images_from_files(self, file_paths):
        """
        Carga imágenes desde archivos.
        
        Args:
            file_paths (list): Lista de rutas de archivos
            
        Returns:
            int: Número de imágenes cargadas exitosamente
        """
        import cv2
        
        self.captured_images = []
        
        for path in file_paths:
            try:
                img = cv2.imread(path)
                if img is not None:
                    self.captured_images.append(img)
            except:
                pass
        
        return len(self.captured_images)
