# run.py - Punto de entrada principal de la aplicación Flask

import os
from flask import Flask
from pathlib import Path
import datetime
import locale

# Importar la instancia db y modelos (necesario para el comando init-db)
from models import db, Prestador, ReporteMetadata, DATABASE_PATH
# Importar filtros (o definirlos aquí si se prefiere)
from babel.dates import format_date as babel_format_date

# --- Configuración de Locale ---
# (Es bueno tenerlo aquí también si se ejecutan comandos CLI que usen fechas)
try: locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8') 
except locale.Error:
    try: locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
         try: locale.setlocale(locale.LC_TIME, 'Spanish_Mexico') 
         except locale.Error:
              try: locale.setlocale(locale.LC_TIME, 'Spanish') 
              except locale.Error: print("ADVERTENCIA (run.py): No se pudo establecer locale a español.")


# --- Función Fábrica para Crear la App Flask ---
def create_app(config_object=None):
    """Crea y configura una instancia de la aplicación Flask."""
    
    app = Flask(__name__, instance_relative_config=False) 
    
    # Configuración de la aplicación
    # Es mejor usar configuraciones más seguras en producción
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH.resolve()}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-change-this-in-prod')

    # Aplicar configuraciones adicionales si se pasan
    if config_object:
        app.config.from_object(config_object)

    # Inicializar extensiones con la app
    db.init_app(app)

    # Registrar el Blueprint que contiene las rutas
    # Importar aquí para evitar importación circular si reporter importa 'app'
    from reporter import reporter_bp 
    app.register_blueprint(reporter_bp)
    print("INFO (run.py): Blueprint 'reporter' registrado.")

    # Registrar filtros Jinja2 y context processors
    register_template_filters(app)
    register_context_processors(app)

    # Registrar comandos CLI
    register_cli_commands(app)

    return app

# --- Funciones Auxiliares para Registro (Separadas para claridad) ---
def register_template_filters(app):
    # Filtro para fecha larga
    @app.template_filter('format_date')
    def format_date_filter_local(value):
        if not value: return ""
        try:
            if isinstance(value, str): date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
            elif isinstance(value, datetime.date): date_obj = value
            elif isinstance(value, datetime.datetime): date_obj = value.date()
            else: return value 
            return babel_format_date(date_obj, format='long', locale='es') 
        except Exception as e: print(f"WARN (format_date_filter): {e}"); return value 
    
    # Filtro para fecha corta
    @app.template_filter('format_date_short')
    def format_date_short_filter_local(value):
         if not value: return ""
         try:
            if isinstance(value, str): date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
            elif isinstance(value, datetime.date): date_obj = value
            elif isinstance(value, datetime.datetime): date_obj = value.date()
            else: return value
            month_name = babel_format_date(date_obj, format='MMMM', locale='es').lower()
            return f"{date_obj.day}/{month_name}/{date_obj.year}"
         except Exception as e: print(f"WARN (format_date_short_filter): {e}"); return value
    print("INFO (run.py): Filtros Jinja2 registrados.")

def register_context_processors(app):
    # Poner el año actual disponible en todas las plantillas
    @app.context_processor
    def inject_now(): return {'now': datetime.datetime.now}
    print("INFO (run.py): Context processors registrados.")

def register_cli_commands(app):
    # Comando para inicializar la base de datos desde la terminal: flask init-db
    @app.cli.command('init-db')
    def init_db_command_in_factory(): 
        """Crea las tablas de la BD y un usuario de ejemplo."""
        # El contexto de la aplicación ya está activo aquí por app.cli
        print("INFO (init-db): Creando tablas...")
        try:
            db.create_all() 
            print(f"INFO (init-db): Tablas creadas en {DATABASE_PATH}")
            if not Prestador.query.first():
                print("INFO (init-db): Creando prestador ejemplo...")
                default_boleta = "2020000000" 
                default_prestador = Prestador(boleta=default_boleta, nombre="Prestador Ejemplo Inicial", programa_academico="Ing Ejemplo", semestre="Inicial", email="inicial@example.com", telefono="000")
                db.session.add(default_prestador)
                db.session.commit() 
                print(f"INFO (init-db): Prestador ejemplo creado: {default_boleta}.")
            else: print("INFO (init-db): Tabla 'prestador' ya contiene datos.")
        except Exception as e: print(f"ERROR (init-db): {e}"); db.session.rollback() 
    print("INFO (run.py): Comandos CLI registrados.")

# --- Bloque de Ejecución Principal ---
if __name__ == '__main__':
    app = create_app() # Crear la instancia de la aplicación usando la fábrica
    
    # Verificar si la BD existe antes de correr (opcional)
    with app.app_context(): 
        if not DATABASE_PATH.is_file():
            print(f"\nADVERTENCIA (run.py): DB no encontrada en {DATABASE_PATH}.")
            print(f"                 Ejecuta 'flask init-db' para crearla.\n")

    # Imprimir información de inicio
    print("--- Generador de Reportes SS (Flask+DB+Blueprint) ---"); 
    print(f"DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Accede al formulario en: http://localhost:5000 (o http://<TU_IP>:5000)")
    print(f"Accede al historial en: http://localhost:5000/history")
    print("Presiona CTRL+C para detener el servidor.")
    print("-----------------------------------------------------")
    
    # Ejecutar la aplicación con el servidor de desarrollo de Flask
    # debug=True es útil para desarrollo (recarga automática, depurador interactivo)
    # ¡NUNCA usar debug=True en producción!
    app.run(host='0.0.0.0', port=5000, debug=True) 

# --- FIN DEL ARCHIVO run.py ---