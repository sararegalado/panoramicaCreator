"""
============================================================================
CAMERA MANAGER - Gestión de Cámaras
============================================================================
Maneja detección y conexión de cámaras (iPhone Continuity Camera, webcam, etc.)
"""

import cv2


class CameraManager:
    """Gestiona la detección y conexión de cámaras."""
    
    def __init__(self):
        self.cap = None
        self.camera_index = 0
    
    def find_cameras(self, max_index=5):
        """
        Busca todas las cámaras disponibles.
        
        Args:
            max_index (int): Máximo índice a buscar
            
        Returns:
            list: Lista de índices de cámaras disponibles
        """
        found = []
        for i in range(max_index + 1):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        found.append(i)
                    cap.release()
            except:
                pass
        return found
    
    def get_camera_info(self, index):
        """
        Obtiene información de una cámara específica.
        
        Args:
            index (int): Índice de la cámara
            
        Returns:
            dict: Información de la cámara o None si no está disponible
        """
        try:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                    return {'index': index, 'width': w, 'height': h}
            cap.release()
        except:
            pass
        return None
    
    def connect(self, index):
        """
        Conecta a una cámara específica.
        
        Args:
            index (int): Índice de la cámara
            
        Returns:
            bool: True si conectó exitosamente, False en caso contrario
        """
        # Liberar cámara anterior si existe
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        try:
            self.cap = cv2.VideoCapture(index)
            
            if not self.cap.isOpened():
                self.cap = None
                return False
            
            # Verificar que funciona leyendo un frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.cap.release()
                self.cap = None
                return False
            
            # Configurar resolución alta
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
            self.camera_index = index
            return True
            
        except Exception as e:
            if self.cap:
                self.cap.release()
            self.cap = None
            return False
    
    def disconnect(self):
        """Desconecta la cámara actual."""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def read_frame(self):
        """
        Lee un frame de la cámara.
        
        Returns:
            tuple: (success, frame) o (False, None) si falla
        """
        if self.cap is None:
            return False, None
        
        try:
            ret, frame = self.cap.read()
            return ret, frame
        except:
            return False, None
    
    def is_connected(self):
        """Verifica si hay una cámara conectada."""
        return self.cap is not None and self.cap.isOpened()
    
    def get_resolution(self):
        """
        Obtiene la resolución actual de la cámara.
        
        Returns:
            tuple: (width, height) o None si no hay cámara
        """
        if not self.is_connected():
            return None
        
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return w, h
    
    def find_iphone(self):
        """
        Busca el iPhone (Continuity Camera).
        Típicamente está en índice 1 con resolución alta.
        
        Returns:
            int: Índice del iPhone o None si no se encuentra
        """
        cameras = self.find_cameras(max_index=3)
        
        # Preferir índice 1 si existe (típicamente iPhone)
        if 1 in cameras:
            info = self.get_camera_info(1)
            # iPhone suele tener resolución >= 1920x1080
            if info and info['width'] >= 1920:
                return 1
        
        # Buscar cualquier cámara con alta resolución
        for idx in cameras:
            info = self.get_camera_info(idx)
            if info and info['width'] >= 1920:
                return idx
        
        return None
