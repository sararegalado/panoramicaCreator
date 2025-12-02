import sys
from pathlib import Path

# Asegurar que el directorio actual está en el path
sys.path.insert(0, str(Path(__file__).parent))

from GUI import PanoramaCreatorGUI


def main():
    print("Iniciando aplicación...")
    
    try:
        # Crear y ejecutar la aplicación
        app = PanoramaCreatorGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n\nAplicación cerrada por el usuario")
    except Exception as e:
        print(f"\nrror al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
