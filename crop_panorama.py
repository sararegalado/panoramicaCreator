#!/usr/bin/env python3
"""Recorta las zonas negras de una imagen de panorámica.

Uso:
  python crop_panorama.py input.png [--replace] [--threshold N]

Guarda el resultado en `input_cropped.png` a menos que se use `--replace`.
"""
import sys
import os
from PIL import Image
import numpy as np


def crop_black_borders(image_path, out_path=None, threshold=30, replace=False):
    im = Image.open(image_path).convert('RGB')
    arr = np.array(im)

    # Convertir a gris para detectar píxeles no-negros
    gray = np.dot(arr[..., :3], [0.2989, 0.5870, 0.1140])
    h, w = gray.shape

    # Crear máscara MUY estricta
    mask = gray > threshold

    # ANÁLISIS POR FILAS - MUY ESTRICTO (85% de píxeles válidos)
    row_counts = np.sum(mask, axis=1)
    row_threshold = int(w * 0.85)
    valid_rows = np.where(row_counts >= row_threshold)[0]
    
    if len(valid_rows) == 0:
        # Fallback a 70%
        row_threshold = int(w * 0.70)
        valid_rows = np.where(row_counts >= row_threshold)[0]
    
    if len(valid_rows) == 0:
        print('No se encontraron filas válidas. No se recorta.')
        return None
    
    y0 = valid_rows[0]
    y1 = valid_rows[-1] + 1

    # ANÁLISIS POR COLUMNAS - MUY ESTRICTO (85% de píxeles válidos)
    col_counts = np.sum(mask, axis=0)
    col_threshold = int(h * 0.85)
    valid_cols = np.where(col_counts >= col_threshold)[0]
    
    if len(valid_cols) == 0:
        # Fallback a 70%
        col_threshold = int(h * 0.70)
        valid_cols = np.where(col_counts >= col_threshold)[0]
    
    if len(valid_cols) == 0:
        print('No se encontraron columnas válidas. No se recorta.')
        return None
    
    x0 = valid_cols[0]
    x1 = valid_cols[-1] + 1

    # Margen de seguridad GENEROSO
    margin_y = max(10, int(h * 0.02))  # 2% de altura
    margin_x = max(10, int(w * 0.01))  # 1% de ancho
    
    y0 = min(y0 + margin_y, h - 1)
    y1 = max(y1 - margin_y, y0 + 1)
    x0 = min(x0 + margin_x, w - 1)
    x1 = max(x1 - margin_x, x0 + 1)

    # Verificar validez
    if y0 >= y1 or x0 >= x1:
        print('El recorte resultaría en imagen vacía. No se recorta.')
        return None

    if y0 <= 2 and x0 <= 2 and y1 >= h - 2 and x1 >= w - 2:
        print('La imagen no requiere recorte significativo.')
        return None

    cropped = im.crop((x0, y0, x1, y1))

    if replace:
        save_path = image_path
    else:
        base, ext = os.path.splitext(image_path)
        save_path = base + '_cropped' + ext

    cropped.save(save_path)
    print(f'Guardado: {save_path} (recortado: x={x0}:{x1}, y={y0}:{y1})')
    return save_path


def main():
    if len(sys.argv) < 2:
        print('Uso: python crop_panorama.py input.png [--replace] [--threshold N]')
        sys.exit(1)

    image_path = sys.argv[1]
    replace = False
    threshold = 30  # Extremadamente agresivo por defecto
    for a in sys.argv[2:]:
        if a == '--replace':
            replace = True
        elif a.startswith('--threshold'):
            try:
                threshold = int(a.split('=')[1]) if '=' in a else int(sys.argv[sys.argv.index(a)+1])
            except Exception:
                pass

    if not os.path.isfile(image_path):
        print('Archivo no encontrado:', image_path)
        sys.exit(2)

    crop_black_borders(image_path, replace=replace, threshold=threshold)


if __name__ == '__main__':
    main()
