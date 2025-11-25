# PUNTO DE ENTRADA PROYECTO

import sys
from pathlib import Path

# Asegurar que el directorio actual está en el path
sys.path.insert(0, str(Path(__file__).parent))

from GUI import PanoramaCreatorGUI


def main():
    """Función principal - Punto de entrada del programa."""
    print("\n" + "🌄"*35)
    print("   PANORAMA CREATOR - Sistema de Creación de Panoramas")
    print("   Universidad de Deusto - Visión por Computador")
    print("🌄"*35 + "\n")
    
    print("🚀 Iniciando aplicación...")
    
    try:
        # Crear y ejecutar la aplicación
        app = PanoramaCreatorGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
