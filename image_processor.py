"""
============================================================================
IMAGE PROCESSOR - Procesamiento de Imágenes
============================================================================
Maneja el procesamiento fotométrico y creación de panoramas
"""

import cv2
import numpy as np
from panorama_stitcher import PanoramaStitcher


class ImageProcessor:
    """Procesa imágenes para crear panoramas."""
    
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.stitcher = PanoramaStitcher(input_dir="temp", output_dir=output_dir)
    
    def apply_photometric_flattening(self, images):
        """
        Aplica aplanamiento fotométrico a una secuencia de imágenes.
        
        Args:
            images (list): Lista de imágenes BGR
            
        Returns:
            list: Imágenes procesadas
        """
        processed = []
        
        # Calcular luminancia media objetivo
        means = []
        for img in images:
            try:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                means.append(np.mean(gray))
            except:
                means.append(0)
        
        if len(means) == 0:
            return images.copy()
        
        target = float(np.median(means)) if np.median(means) > 0 else 128.0
        
        for img in images:
            try:
                # Trabajar en float32
                imgf = img.astype(np.float32)
                
                # Balance de blancos: Gray World
                b_mean, g_mean, r_mean = np.mean(imgf[:, :, 0]), np.mean(imgf[:, :, 1]), np.mean(imgf[:, :, 2])
                mean = (b_mean + g_mean + r_mean) / 3.0 + 1e-8
                imgf[:, :, 0] *= (mean / (b_mean + 1e-8))
                imgf[:, :, 1] *= (mean / (g_mean + 1e-8))
                imgf[:, :, 2] *= (mean / (r_mean + 1e-8))
                
                imgf = np.clip(imgf, 0, 255).astype(np.uint8)
                
                # Normalización de exposición
                gray = cv2.cvtColor(imgf, cv2.COLOR_BGR2GRAY)
                current_mean = np.mean(gray) + 1e-8
                alpha = target / current_mean
                imgf = cv2.convertScaleAbs(imgf, alpha=float(alpha), beta=0)
                
                # CLAHE en canal L
                lab = cv2.cvtColor(imgf, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                lab = cv2.merge((l, a, b))
                imgf = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                
                processed.append(imgf)
            except:
                processed.append(img.copy())
        
        return processed
    
    def create_panorama(self, images, apply_flattening=True, crop_borders=True):
        """
        Crea un panorama a partir de una lista de imágenes.
        
        Args:
            images (list): Lista de imágenes BGR
            apply_flattening (bool): Si aplicar aplanamiento fotométrico
            crop_borders (bool): Si recortar bordes negros
            
        Returns:
            numpy.ndarray: Imagen panorámica o None si falla
        """
        if len(images) < 2:
            return None
        
        # Aplicar aplanamiento si se solicita
        if apply_flattening:
            images_to_process = self.apply_photometric_flattening(images)
        else:
            images_to_process = images.copy()
        
        # Asignar imágenes al stitcher
        self.stitcher.images = images_to_process
        
        # Crear panorama
        result = self.stitcher.create_panorama(mode='panorama')
        
        if result is None:
            return None
        
        # Recortar bordes si se solicita
        if crop_borders:
            self.stitcher.crop_black_borders()
        
        return self.stitcher.panorama
    
    def save_panorama(self, panorama, prefix="panorama"):
        """
        Guarda un panorama en disco.
        
        Args:
            panorama (numpy.ndarray): Imagen panorámica
            prefix (str): Prefijo para el nombre del archivo
            
        Returns:
            str: Ruta del archivo guardado
        """
        if panorama is None:
            return None
        
        self.stitcher.panorama = panorama
        self.stitcher.save_results(prefix=prefix)
        
        from pathlib import Path
        return str(Path(self.output_dir) / f"{prefix}.png")
