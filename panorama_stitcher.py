import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# Clase principal para crear fotos panoramicas usando OpenCV Stitcher
class PanoramaStitcher:

    # Constructor de la clase
    def __init__(self, input_dir="input", output_dir="output"):

        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(exist_ok=True)
        
        # Lista de para guardar imagenes originales
        self.images = []  
        # Imagen panoramica resultante
        self.panorama = None

    # Funcion para cargar fotos    
    def load_images(self):
        print("Cargando imagenes...")
        
        # Buscar imagenes en todos los formatos
        image_files = (
            sorted(self.input_dir.glob("*.png")) +
            sorted(self.input_dir.glob("*.jpg")) +
            sorted(self.input_dir.glob("*.jpeg")) +
            sorted(self.input_dir.glob("*.HEIC")) +
            sorted(self.input_dir.glob("*.PNG")) +
            sorted(self.input_dir.glob("*.JPG")) +
            sorted(self.input_dir.glob("*.JPEG"))
        )
        
        if not image_files:
            raise ValueError(f"No se encontraron imágenes en '{self.input_dir}'")
        
        print(f"\nEncontradas {len(image_files)} imágenes...\n")
        
        # Cargar cada imagen
        for img_path in image_files:
            # Leer imagen (OpenCV usa formato BGR)
            img = cv2.imread(str(img_path))
            
            if img is not None:
                self.images.append(img)
                h, w = img.shape[:2]  # Obtener dimensiones
                print(f"{img_path.name:<30} → {w:4d}x{h:4d} píxeles")
            else:
                print(f"No se pudo cargar: {img_path.name}")
        
        # Verificar que tengamos al menos 2 imágenes
        if len(self.images) < 2:
            raise ValueError("Se necesitan al menos 2 imágenes para crear un panorama")
        
        print(f"\n{len(self.images)} imágenes cargadas correctamente")
        
        return len(self.images)
    
    # Funcion para crear panorama usando el Stitcher integrado de OpenCV
    def create_panorama(self, mode='panorama'):
        
        # Crear el objeto Stitcher según el modo seleccionado
        if mode == 'scans':
            stitcher = cv2.Stitcher_create(cv2.Stitcher_SCANS)
        else:
            stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
        
        # Ejecutar el algoritmo de stitching
        # status indica si fue exitoso, panorama contiene el resultado
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
        # Comprobar que existe imagen panorámica
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
        w_final, h_final = x1 - x0, y1 - y0
        
        print("\nRECORTE APLICADO:")
    
    # Funcion para calcular estadisticas del panorama creado
    def calculate_statistics(self):
        if self.panorama is None:
            return

        # Dimensiones del panorama
        h, w = self.panorama.shape[:2]
        total_pixels = h * w
        megapixels = total_pixels / (1024 * 1024)
        
        print(f"Dimensiones finales:")
        print(f"   Ancho:  {w:,} píxeles")
        print(f"   Alto:   {h:,} píxeles")
        print(f"   Total:  {total_pixels:,} píxeles ({megapixels:.2f} MP)")
        
        # Comparación con imágenes originales
        total_original = sum(img.shape[0] * img.shape[1] for img in self.images)
        megapixels_orig = total_original / (1024 * 1024)
        ratio = total_pixels / total_original
        
        print("\nComparación con originales:")
        print(f"   Píxeles originales (suma): {total_original:,} ({megapixels_orig:.2f} MP)")
        print(f"   Ratio panorama/originales: {ratio:.2%}")
        
        # Calcular nitidez usando el operador Laplaciano
        # Mayor varianza = bordes más definidos = mayor nitidez
        gray = cv2.cvtColor(self.panorama, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        print(f"\nCalidad:")
        print(f"   Nitidez (varianza Laplaciano): {sharpness:.2f}")
        
        # Interpretación de la nitidez
        if sharpness > 500:
            quality = "Excelente"
        elif sharpness > 100:
            quality = "Buena"
        elif sharpness > 50:
            quality = "Aceptable"
        else:
            quality = "Baja (puede estar desenfocada)"
        print(f"   Evaluación: {quality}")
    
    # Funcion para guardar resultados
    def save_results(self, prefix="panorama"):
        if self.panorama is None:
            print("No hay panorama para guardar")
            return
        
        # Guardar el panorama principal
        pano_path = self.output_dir / f"{prefix}.png"
        cv2.imwrite(str(pano_path), self.panorama)
        
        # Calcular tamaño del archivo
        file_size_mb = pano_path.stat().st_size / (1024 * 1024)
        print(f"Panorama guardado:")
        print(f"   {pano_path}")
        print(f"   Tamaño: {file_size_mb:.2f} MB")
        
        # Crear y guardar la comparación visual
        self._create_comparison(prefix)
        
        print(f"\nTodos los resultados guardados en '{self.output_dir}/'")
    
    # Crear comparación visual
    def _create_comparison(self, prefix="panorama"):
        n_images = len(self.images)
        
        # Decidir el layout según el número de imágenes
        if n_images <= 4:
            rows, cols = 1, n_images
        else:
            rows, cols = 2, (n_images + 1) // 2
        
        # Redimensionar imágenes originales para la comparación
        max_height = 300  # Altura fija para visualización
        resized_images = []
        
        for img in self.images:
            h, w = img.shape[:2]
            scale = max_height / h
            new_w = int(w * scale)
            resized = cv2.resize(img, (new_w, max_height))
            resized_images.append(resized)
        
        # Concatenar imágenes originales
        if rows == 1:
            # Una sola fila
            original_grid = np.hstack(resized_images)
        else:
            # Dos filas
            row1 = np.hstack(resized_images[:cols])
            row2_imgs = resized_images[cols:]
            
            # Rellenar segunda fila si es necesario
            if len(row2_imgs) < cols:
                for _ in range(cols - len(row2_imgs)):
                    row2_imgs.append(np.zeros_like(resized_images[0]))
            
            row2 = np.hstack(row2_imgs)
            original_grid = np.vstack([row1, row2])
        
        # Redimensionar panorama para que coincida con el ancho del grid
        pano_h, pano_w = self.panorama.shape[:2]
        grid_w = original_grid.shape[1]
        scale = grid_w / pano_w
        new_pano_h = int(pano_h * scale)
        panorama_resized = cv2.resize(self.panorama, (grid_w, new_pano_h))
        
        # Crear la comparación vertical con separador
        separator = np.ones((20, grid_w, 3), dtype=np.uint8) * 255
        comparison = np.vstack([
            original_grid,
            separator,
            panorama_resized
        ])
        
        # Añadir etiquetas de texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        font_thickness = 2
        color = (0, 255, 0)  # Verde en BGR
        
        cv2.putText(comparison, 'Imagenes Originales', (10, 30), 
                   font, font_scale, color, font_thickness, cv2.LINE_AA)
        cv2.putText(comparison, 'Panorama Final', 
                   (10, original_grid.shape[0] + 50),
                   font, font_scale, color, font_thickness, cv2.LINE_AA)
        
        # Guardar comparación
        comp_path = self.output_dir / f"{prefix}_comparison.png"
        cv2.imwrite(str(comp_path), comparison)
        
        file_size_mb = comp_path.stat().st_size / (1024 * 1024)
        print(f"\nComparación guardada:")
        print(f"   {comp_path}")
        print(f"   Tamaño: {file_size_mb:.2f} MB")
    
    # Muestra resultados usando matplotlib
    def visualize(self):
        if self.panorama is None:
            print("No hay panorama para visualizar")
            return
        
        # Crear figura
        fig = plt.figure(figsize=(18, 10))
        fig.suptitle('Resultado del Image Stitching', fontsize=16, fontweight='bold')
        
        # Mostrar hasta 4 imágenes originales en la primera fila
        for i, img in enumerate(self.images[:4]):
            ax = fig.add_subplot(2, 4, i + 1)
            # Convertir de BGR (OpenCV) a RGB (matplotlib)
            ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            ax.set_title(f'Imagen {i+1}', fontsize=12)
            ax.axis('off')
        
        # Panorama en la segunda fila ocupando todo el ancho
        ax = fig.add_subplot(2, 1, 2)
        ax.imshow(cv2.cvtColor(self.panorama, cv2.COLOR_BGR2RGB))
        ax.set_title('Panorama Final', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        plt.tight_layout()
        
        # Guardar la visualización
        viz_path = self.output_dir / 'visualization.png'
        plt.savefig(viz_path, dpi=150, bbox_inches='tight')
        print(f"\n✓ Visualización guardada en: {viz_path}")
        
        # Mostrar en pantalla
        print("Mostrando ventana de visualización...")
        plt.show()
    

    # Funcion para ejecutar todo el pipeline
    def run(self, crop_borders=True, show_visualization=True):
        try:
            # Paso 1: Cargar imágenes
            self.load_images()
            
            # Paso 2: Crear panorama
            result = self.create_panorama(mode='panorama')
            
            if result is None:
                print("\nNo se pudo completar el proceso")
                return None
            
            # Paso 3: Recortar bordes (opcional)
            if crop_borders:
                self.crop_black_borders()
            
            # Paso 4: Calcular estadísticas
            self.calculate_statistics()
            
            # Paso 5: Guardar resultados
            self.save_results()
            
            # Paso 6: Visualizar (opcional)
            if show_visualization:
                self.visualize()
            
            # ¡Éxito!
            print("PROCESO COMPLETADO EXITOSAMENTE")
            
            return self.panorama
            
        except Exception as e:
            print(f"\nError durante la ejecución del pipeline: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def main():
    # Crear el stitcher
    stitcher = PanoramaStitcher(
        input_dir="input",    # Carpeta con las imágenes de entrada
        output_dir="output"   # Carpeta donde se guardarán los resultados
    )
    
    # Ejecutar el pipeline completo
    panorama = stitcher.run(
        crop_borders=True,
        show_visualization=True
    )
    
    if panorama is not None:
        print("\n¡Panorama creado con éxito!")
    else:
        print("\nNo se pudo crear el panorama")


if __name__ == "__main__":
    main()
