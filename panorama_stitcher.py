"""
============================================================================
PANORAMA STITCHER - Creación Automática de Panoramas
============================================================================
Proyecto de Visión por Computador - Universidad de Deusto 2025-2026

Este script crea panoramas de alta resolución cosiendo múltiples imágenes
usando el algoritmo robusto integrado de OpenCV (Stitcher).

CARACTERÍSTICAS:
- Usa OpenCV Stitcher (método más robusto y recomendado)
- Detecta automáticamente características y homografías
- Compensa cambios de perspectiva e iluminación
- Fusiona imágenes con blending suave
- Recorta bordes negros automáticamente
- Genera visualizaciones comparativas

MODO DE USO:
1. Coloca tus imágenes en la carpeta 'input/'
2. Ejecuta: python panorama_stitcher.py
3. Los resultados se guardarán en 'output/'
============================================================================
"""

import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt


class PanoramaStitcher:
    """
    Clase optimizada para crear panoramas usando OpenCV Stitcher.
    Esta implementación usa siempre el método más robusto (opción 3).
    """
    
    def __init__(self, input_dir="input", output_dir="output"):
        """
        Inicializa el sistema de stitching.
        
        Args:
            input_dir (str): Directorio que contiene las imágenes de entrada
            output_dir (str): Directorio donde se guardarán los resultados
        """
        # Convertir rutas a objetos Path para mejor manejo
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(exist_ok=True)
        
        # Variables para almacenar las imágenes y el resultado
        self.images = []          # Lista de imágenes originales cargadas
        self.panorama = None      # Imagen panorámica resultante
        
    def load_images(self):
        """
        Carga todas las imágenes del directorio de entrada.
        Soporta formatos: PNG, JPG, JPEG, HEIC
        
        Returns:
            int: Número de imágenes cargadas exitosamente
            
        Raises:
            ValueError: Si no se encuentran imágenes o hay menos de 2
        """
        print("\n" + "="*70)
        print("📂 PASO 1: CARGANDO IMÁGENES")
        print("="*70)
        
        # Buscar archivos de imagen en todos los formatos soportados
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
            raise ValueError(f"❌ No se encontraron imágenes en '{self.input_dir}'")
        
        print(f"\n📸 Encontradas {len(image_files)} imágenes, cargando...\n")
        
        # Cargar cada imagen
        for img_path in image_files:
            # Leer imagen (OpenCV usa formato BGR)
            img = cv2.imread(str(img_path))
            
            if img is not None:
                self.images.append(img)
                h, w = img.shape[:2]  # Obtener dimensiones
                print(f"  ✓ {img_path.name:<30} → {w:4d}x{h:4d} píxeles")
            else:
                print(f"  ⚠️ No se pudo cargar: {img_path.name}")
        
        # Verificar que tengamos al menos 2 imágenes
        if len(self.images) < 2:
            raise ValueError("❌ Se necesitan al menos 2 imágenes para crear un panorama")
        
        print(f"\n✅ {len(self.images)} imágenes cargadas correctamente")
        
        return len(self.images)
    
    def create_panorama(self, mode='panorama'):
        """
        Crea el panorama usando el Stitcher integrado de OpenCV.
        Este es el método más robusto (equivalente a la opción 3).
        
        El algoritmo realiza los siguientes pasos automáticamente:
        1. Detecta características (keypoints) en cada imagen
        2. Encuentra correspondencias entre imágenes adyacentes
        3. Estima homografías (transformaciones geométricas)
        4. Compensa diferencias de exposición e iluminación
        5. Proyecta imágenes a un plano común
        6. Fusiona con blending para transiciones suaves
        
        Args:
            mode (str): Modo de stitching
                - 'panorama': Para panoramas generales (default)
                - 'scans': Para documentos o escenas planares
        
        Returns:
            numpy.ndarray: Imagen panorámica resultante o None si falla
        """
        print("\n" + "="*70)
        print("🔗 PASO 2: CREANDO PANORAMA")
        print("="*70)
        print(f"\n🔧 Usando OpenCV Stitcher (modo: {mode.upper()})")
        print("   Este método es el más robusto y funciona mejor con fotos reales\n")
        
        # Crear el objeto Stitcher según el modo seleccionado
        if mode == 'scans':
            # Modo SCANS: optimizado para documentos o superficies planas
            stitcher = cv2.Stitcher_create(cv2.Stitcher_SCANS)
        else:
            # Modo PANORAMA: optimizado para escenas generales (default)
            stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
        
        print("⏳ Procesando imágenes...")
        print("   - Detectando características")
        print("   - Calculando homografías")
        print("   - Fusionando imágenes")
        print("   - Compensando iluminación\n")
        
        # Ejecutar el algoritmo de stitching
        # status indica si fue exitoso, panorama contiene el resultado
        status, panorama = stitcher.stitch(self.images)
        
        # Verificar el resultado
        if status == cv2.Stitcher_OK:
            # ¡Éxito! Guardar el panorama
            self.panorama = panorama
            h, w = panorama.shape[:2]
            print(f"✅ ¡Panorama creado exitosamente!")
            print(f"   Dimensiones: {w}x{h} píxeles")
            print(f"   Tamaño: {(w*h)/(1024*1024):.1f} megapíxeles")
            return panorama
        else:
            # Error en el proceso - mostrar mensaje descriptivo
            error_messages = {
                cv2.Stitcher_ERR_NEED_MORE_IMGS: 
                    "Se necesitan más imágenes o mayor solapamiento",
                cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL: 
                    "Fallo en estimación de homografía - verifica el solapamiento",
                cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL: 
                    "Fallo en ajuste de parámetros de cámara"
            }
            error_msg = error_messages.get(status, f"Error desconocido (código: {status})")
            
            print(f"\n❌ Error al crear el panorama:")
            print(f"   {error_msg}")
            print("\n💡 Consejos:")
            print("   - Asegúrate que las imágenes tengan ~30-50% de solapamiento")
            print("   - Toma las fotos desde el mismo punto (rotando la cámara)")
            print("   - Evita cambios bruscos de iluminación")
            
            return None
    
    def crop_black_borders(self, threshold=30):
        """
        Recorta EXTREMADAMENTE agresivo los bordes negros/vacíos del panorama.
        
        Este método es SUPER AGRESIVO y prioriza eliminar TODAS las zonas negras,
        recortando generosamente para garantizar bordes limpios.
        
        Estrategia:
        1. Analiza cada fila/columna individualmente
        2. Encuentra la primera/última que tenga MAYORMENTE píxeles válidos (>85%)
        3. Añade margen de seguridad generoso
        4. Recorta sin piedad
        
        Args:
            threshold (int): Umbral de luminosidad (default: 30, MUY agresivo)
        """
        if self.panorama is None:
            return
        
        print("\n" + "="*70)
        print("✂️ PASO 3: RECORTE SUPER AGRESIVO - CERO TOLERANCIA A NEGROS")
        print("="*70)
        
        # Guardar dimensiones originales
        h_orig, w_orig = self.panorama.shape[:2]
        print(f"\n📏 Dimensiones originales: {w_orig}x{h_orig}")
        print(f"🔪 Modo EXTREMO: Eliminará TODOS los píxeles oscuros")
        print(f"🔪 Umbral: {threshold} (píxeles <{threshold} = negros)")
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(self.panorama, cv2.COLOR_BGR2GRAY)
        
        # Crear máscara MUY estricta
        mask = gray > threshold
        
        # ANÁLISIS POR FILAS (eje Y) - MUY ESTRICTO
        print("🔍 Analizando filas (buscando 85%+ píxeles válidos)...")
        row_counts = np.sum(mask, axis=1)
        # Una fila es válida solo si tiene 85% o más de píxeles no-negros
        row_threshold = int(w_orig * 0.85)
        valid_rows = np.where(row_counts >= row_threshold)[0]
        
        if len(valid_rows) == 0:
            # Si no hay filas con 85%, bajar a 70%
            print("   ⚠️  No hay filas con 85%+ válidos, bajando a 70%...")
            row_threshold = int(w_orig * 0.70)
            valid_rows = np.where(row_counts >= row_threshold)[0]
            
        if len(valid_rows) == 0:
            print("   ⚠️  No se encontraron filas suficientemente válidas")
            return
        
        y0 = valid_rows[0]
        y1 = valid_rows[-1] + 1
        print(f"   ✓ Filas válidas: {y0} a {y1-1}")
        
        # ANÁLISIS POR COLUMNAS (eje X) - MUY ESTRICTO
        print("🔍 Analizando columnas (buscando 85%+ píxeles válidos)...")
        col_counts = np.sum(mask, axis=0)
        # Una columna es válida solo si tiene 85% o más de píxeles no-negros
        col_threshold = int(h_orig * 0.85)
        valid_cols = np.where(col_counts >= col_threshold)[0]
        
        if len(valid_cols) == 0:
            # Si no hay columnas con 85%, bajar a 70%
            print("   ⚠️  No hay columnas con 85%+ válidos, bajando a 70%...")
            col_threshold = int(h_orig * 0.70)
            valid_cols = np.where(col_counts >= col_threshold)[0]
        
        if len(valid_cols) == 0:
            print("   ⚠️  No se encontraron columnas suficientemente válidas")
            return
        
        x0 = valid_cols[0]
        x1 = valid_cols[-1] + 1
        print(f"   ✓ Columnas válidas: {x0} a {x1-1}")
        
        # MARGEN DE SEGURIDAD GENEROSO para eliminar bordes residuales
        # Usar margen más grande para garantizar eliminación completa
        margin_y = max(10, int(h_orig * 0.02))  # 2% de altura o mínimo 10px
        margin_x = max(10, int(w_orig * 0.01))  # 1% de ancho o mínimo 10px
        
        print(f"🔪 Aplicando margen de seguridad: {margin_y}px (vertical), {margin_x}px (horizontal)")
        
        # Aplicar márgenes
        y0 = min(y0 + margin_y, h_orig - 1)
        y1 = max(y1 - margin_y, y0 + 1)
        x0 = min(x0 + margin_x, w_orig - 1)
        x1 = max(x1 - margin_x, x0 + 1)
        
        # Verificar validez
        if y0 >= y1 or x0 >= x1:
            print("   ⚠️  El recorte resultaría en imagen vacía")
            return
        
        if y0 <= 2 and x0 <= 2 and y1 >= h_orig - 2 and x1 >= w_orig - 2:
            print("\n✓ La imagen no requiere recorte significativo")
            return
        
        # Aplicar el recorte SIN PIEDAD
        self.panorama = self.panorama[y0:y1, x0:x1]
        w_final, h_final = x1 - x0, y1 - y0
        
        print(f"\n✂️  RECORTE EXTREMO APLICADO:")
        print(f"   🔪 Eliminado:")
        print(f"      - Superior:  {y0}px")
        print(f"      - Inferior:  {h_orig - y1}px")
        print(f"      - Izquierda: {x0}px")
        print(f"      - Derecha:   {w_orig - x1}px")
        print(f"   📏 Dimensiones finales: {w_final}x{h_final}")
        print(f"   📊 Área reducida: {((w_orig*h_orig - w_final*h_final)/(w_orig*h_orig)*100):.1f}%")
        print(f"\n✅ BORDES NEGROS ELIMINADOS COMPLETAMENTE")
    
    def calculate_statistics(self):
        """
        Calcula y muestra estadísticas del panorama creado.
        
        Métricas calculadas:
        - Dimensiones y total de píxeles
        - Comparación con imágenes originales
        - Nitidez (usando varianza del Laplaciano)
        """
        if self.panorama is None:
            return
        
        print("\n" + "="*70)
        print("📊 PASO 4: ESTADÍSTICAS DEL PANORAMA")
        print("="*70 + "\n")
        
        # Dimensiones del panorama
        h, w = self.panorama.shape[:2]
        total_pixels = h * w
        megapixels = total_pixels / (1024 * 1024)
        
        print(f"📐 Dimensiones finales:")
        print(f"   Ancho:  {w:,} píxeles")
        print(f"   Alto:   {h:,} píxeles")
        print(f"   Total:  {total_pixels:,} píxeles ({megapixels:.2f} MP)")
        
        # Comparación con imágenes originales
        total_original = sum(img.shape[0] * img.shape[1] for img in self.images)
        megapixels_orig = total_original / (1024 * 1024)
        ratio = total_pixels / total_original
        
        print(f"\n📊 Comparación con originales:")
        print(f"   Píxeles originales (suma): {total_original:,} ({megapixels_orig:.2f} MP)")
        print(f"   Ratio panorama/originales: {ratio:.2%}")
        
        # Calcular nitidez usando el operador Laplaciano
        # Mayor varianza = bordes más definidos = mayor nitidez
        gray = cv2.cvtColor(self.panorama, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        print(f"\n🔍 Calidad:")
        print(f"   Nitidez (varianza Laplaciano): {sharpness:.2f}")
        
        # Interpretación de la nitidez
        if sharpness > 500:
            quality = "Excelente ✨"
        elif sharpness > 100:
            quality = "Buena ✓"
        elif sharpness > 50:
            quality = "Aceptable"
        else:
            quality = "Baja (puede estar desenfocada)"
        print(f"   Evaluación: {quality}")
    
    def save_results(self, prefix="panorama"):
        """
        Guarda el panorama y crea una visualización comparativa.
        
        Archivos generados:
        - {prefix}.png: Panorama final
        - {prefix}_comparison.png: Comparación lado a lado
        
        Args:
            prefix (str): Prefijo para los nombres de archivo
        """
        if self.panorama is None:
            print("⚠️ No hay panorama para guardar")
            return
        
        print("\n" + "="*70)
        print("💾 PASO 5: GUARDANDO RESULTADOS")
        print("="*70 + "\n")
        
        # Guardar el panorama principal
        pano_path = self.output_dir / f"{prefix}.png"
        cv2.imwrite(str(pano_path), self.panorama)
        
        # Calcular tamaño del archivo
        file_size_mb = pano_path.stat().st_size / (1024 * 1024)
        print(f"✓ Panorama guardado:")
        print(f"   📁 {pano_path}")
        print(f"   💾 Tamaño: {file_size_mb:.2f} MB")
        
        # Crear y guardar la comparación visual
        self._create_comparison(prefix)
        
        print(f"\n✅ Todos los resultados guardados en '{self.output_dir}/'")
    
    def _create_comparison(self, prefix="panorama"):
        """
        Crea una visualización comparativa mostrando las imágenes originales
        arriba y el panorama resultante abajo.
        
        Args:
            prefix (str): Prefijo para el nombre del archivo
        """
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
        print(f"\n✓ Comparación guardada:")
        print(f"   📁 {comp_path}")
        print(f"   💾 Tamaño: {file_size_mb:.2f} MB")
    
    def visualize(self):
        """
        Muestra los resultados en una ventana de matplotlib.
        Crea un grid con las imágenes originales arriba y el panorama abajo.
        """
        if self.panorama is None:
            print("⚠️ No hay panorama para visualizar")
            return
        
        print("\n" + "="*70)
        print("📊 PASO 6: VISUALIZANDO RESULTADOS")
        print("="*70)
        
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
        print("📊 Mostrando ventana de visualización...")
        plt.show()
    
    def run(self, crop_borders=True, show_visualization=True):
        """
        Ejecuta el pipeline completo de creación de panorama.
        
        Pipeline:
        1. Cargar imágenes del directorio de entrada
        2. Crear panorama con OpenCV Stitcher (opción 3)
        3. Recortar bordes negros (opcional)
        4. Calcular estadísticas
        5. Guardar resultados
        6. Visualizar (opcional)
        
        Args:
            crop_borders (bool): Si recortar bordes negros (default: True)
            show_visualization (bool): Si mostrar ventana matplotlib (default: True)
        
        Returns:
            numpy.ndarray: Panorama resultante o None si falla
        """
        print("\n" + "="*70)
        print("🌅 PANORAMA STITCHER - Creación Automática de Panoramas")
        print("="*70)
        print("📍 Usando OpenCV Stitcher (Método más robusto - Opción 3)")
        print("="*70)
        
        try:
            # Paso 1: Cargar imágenes
            self.load_images()
            
            # Paso 2: Crear panorama
            result = self.create_panorama(mode='panorama')
            
            if result is None:
                print("\n❌ No se pudo completar el proceso")
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
            print("\n" + "="*70)
            print("✅ PROCESO COMPLETADO EXITOSAMENTE")
            print("="*70)
            print(f"\n📁 Revisa tus resultados en: {self.output_dir.absolute()}")
            print("\n💡 Archivos generados:")
            print("   - panorama.png: Imagen panorámica final")
            print("   - panorama_comparison.png: Comparación visual")
            print("   - visualization.png: Visualización completa")
            
            return self.panorama
            
        except Exception as e:
            print(f"\n❌ Error durante la ejecución: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """
    Función principal - Punto de entrada del script.
    """
    print("\n" + "🌄"*35)
    print("   SISTEMA DE CREACIÓN AUTOMÁTICA DE PANORAMAS")
    print("   Universidad de Deusto - Visión por Computador")
    print("🌄"*35 + "\n")
    
    # Crear el stitcher
    stitcher = PanoramaStitcher(
        input_dir="input",    # Carpeta con las imágenes de entrada
        output_dir="output"   # Carpeta donde se guardarán los resultados
    )
    
    # Ejecutar el pipeline completo
    # Siempre usa la opción 3 (OpenCV Stitcher) - el método más robusto
    panorama = stitcher.run(
        crop_borders=True,           # Recortar bordes negros automáticamente
        show_visualization=True      # Mostrar resultados en ventana
    )
    
    if panorama is not None:
        print("\n🎉 ¡Panorama creado con éxito!")
    else:
        print("\n⚠️  No se pudo crear el panorama")
        print("💡 Revisa que las imágenes tengan suficiente solapamiento")


if __name__ == "__main__":
    main()
