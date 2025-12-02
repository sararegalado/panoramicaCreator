import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# Clase principal para crear fotos panoramicas usando OpenCV Stitcher
class PanoramaStitcher:
    # Constructor de la clase
    def __init__(self, output_dir="output"):

        self.output_dir = Path(output_dir)
        
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(exist_ok=True)
        
        # Lista de para guardar imagenes originales
        self.images = []  
        # Imagen panoramica resultante
        self.panorama = None


    # Funcion para crear panorama
    def create_panorama(self):
        
        # Crear el objeto Stitcher
        stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
        
        # Ejecutar el algoritmo de stitching
        status, panorama = stitcher.stitch(self.images)
        
        # Verificar el resultado
        if status == cv2.Stitcher_OK:
            # Guardar el panorama
            self.panorama = panorama
            h, w = panorama.shape[:2]
            print(f"Panorama creado exitosamente")
            print(f"   Dimensiones: {w}x{h} píxeles")
            print(f"   Tamaño: {(w*h)/(1024*1024):.1f} megapíxeles")
            return panorama
        else:
            # Error en el proceso
            error_messages = {
                cv2.Stitcher_ERR_NEED_MORE_IMGS: 
                    "Se necesitan más imágenes o mayor solapamiento",
                cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL: 
                    "Fallo en estimación de homografía - verifica el solapamiento",
                cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL: 
                    "Fallo en ajuste de parámetros de cámara"
            }
            error_msg = error_messages.get(status, f"Error desconocido (código: {status})")
            
            print(f"\nError al crear el panorama:")
            print(f"   {error_msg}")
            return None
    
    # Funcion para eliminar automaticamente los bordes negros de una imagen panoramica
    def crop_black_borders(self, threshold=30):
        if self.panorama is None:
            return
        
        # Guardar dimensiones originales
        h_orig, w_orig = self.panorama.shape[:2]
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(self.panorama, cv2.COLOR_BGR2GRAY)
        
        # Crear máscara muy estricta
        mask = gray > threshold
        
        # Analisis por filas
        row_counts = np.sum(mask, axis=1)
        # Una fila es válida solo si tiene 85% o más de píxeles no-negros
        row_threshold = int(w_orig * 0.85)
        valid_rows = np.where(row_counts >= row_threshold)[0]
        
        # Si no hay filas validas bajamos el umbral a 70%
        if len(valid_rows) == 0:
            row_threshold = int(w_orig * 0.70)
            valid_rows = np.where(row_counts >= row_threshold)[0]
            
        if len(valid_rows) == 0:
            print("No se encontraron filas suficientemente válidas")
            return
        
        y0 = valid_rows[0]
        y1 = valid_rows[-1] + 1
        
        # Analisis por columnas: Umbral de 85%
        col_counts = np.sum(mask, axis=0)
        col_threshold = int(h_orig * 0.85)
        valid_cols = np.where(col_counts >= col_threshold)[0]
        
        if len(valid_cols) == 0:
            # Fallback a 70%
            col_threshold = int(h_orig * 0.70)
            valid_cols = np.where(col_counts >= col_threshold)[0]
        
        if len(valid_cols) == 0:
            print("No se encontraron columnas suficientemente válidas")
            return
        
        x0 = valid_cols[0]
        x1 = valid_cols[-1] + 1
        
        # Margenes de seguridad para asegurar limpieza completa
        margin_y = max(10, int(h_orig * 0.02))  # 2% de altura o mínimo 10px
        margin_x = max(10, int(w_orig * 0.01))  # 1% de ancho o mínimo 10px
        
        # Aplicar márgenes
        y0 = min(y0 + margin_y, h_orig - 1)
        y1 = max(y1 - margin_y, y0 + 1)
        x0 = min(x0 + margin_x, w_orig - 1)
        x1 = max(x1 - margin_x, x0 + 1)
        
        # Verificar validez
        if y0 >= y1 or x0 >= x1:
            print("El recorte resultaría en imagen vacía")
            return
        
        if y0 <= 2 and x0 <= 2 and y1 >= h_orig - 2 and x1 >= w_orig - 2:
            print("\nLa imagen no requiere recorte significativo")
            return
        
        # Aplicar el recorte
        self.panorama = self.panorama[y0:y1, x0:x1]        
        print("\nRECORTE APLICADO:")
    
    
    