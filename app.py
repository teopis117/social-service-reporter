import os
import pickle # Aunque ya no lo usamos para características, lo dejamos por si acaso
import numpy as np # Podría ser útil para cálculos futuros
# from sklearn.metrics.pairwise import cosine_similarity # Ya no es necesario para este proyecto
# from feature_extractor import extract_features # Ya no es necesario para este proyecto
from flask import Flask, render_template, request, jsonify, send_from_directory, abort, flash, redirect, url_for
from pathlib import Path
import datetime
from babel.dates import format_date as babel_format_date
import locale
import uuid
from weasyprint import HTML, CSS
# Importar la instancia db y los modelos desde models.py
from models import db, Prestador, ReporteMetadata, DATABASE_PATH

# --- Configuración de Locale ---
# (Intenta establecer el locale en español para el formato de fecha)
try:
    locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')
except locale.Error:
    try: locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        try: locale.setlocale(locale.LC_TIME, 'Spanish_Mexico') # Windows
        except locale.Error:
            try: locale.setlocale(locale.LC_TIME, 'Spanish') # Windows genérico
            except locale.Error: print("ADVERTENCIA (app.py): No se pudo establecer el locale a español.")

app = Flask(__name__)

# --- Configuración de Flask y SQLAlchemy ---
BASE_DIR = Path(__file__).resolve().parent
STATIC_FOLDER = BASE_DIR / 'static'
TEMP_PDF_FOLDER_NAME = 'temp_pdf'
TEMP_PDF_FOLDER = STATIC_FOLDER / TEMP_PDF_FOLDER_NAME
TEMP_PDF_FOLDER.mkdir(parents=True, exist_ok=True) # Crear carpeta si no existe

# Configurar la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH.resolve()}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24) # Necesario para mensajes flash (flash())

# Inicializar la extensión SQLAlchemy con la app Flask
# Esto conecta los modelos definidos en models.py con la app Flask
db.init_app(app)

# --- Filtros Jinja2 para Formatear Fechas (Sin cambios) ---
def format_date_filter(value):
    """Formatea fecha a '10 de junio de 2024'."""
    if not value: return ""
    try:
        if isinstance(value, str): date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime.date): date_obj = value
        else: return value
        return babel_format_date(date_obj, format='long', locale='es')
    except (ValueError, TypeError) as e:
        print(f"WARN (format_date_filter): Error formateando '{value}': {e}")
        return value

def format_date_short_filter(value):
    """Formatea fecha a '13/mayo/2024'."""
    if not value: return ""
    try:
        if isinstance(value, str): date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime.date): date_obj = value
        else: return value
        month_name = babel_format_date(date_obj, format='MMMM', locale='es').lower()
        return f"{date_obj.day}/{month_name}/{date_obj.year}"
    except (ValueError, TypeError) as e:
        print(f"WARN (format_date_short_filter): Error formateando '{value}': {e}")
        return value

app.jinja_env.filters['format_date'] = format_date_filter
app.jinja_env.filters['format_date_short'] = format_date_short_filter

# --- Comandos para Crear la Base de Datos ---
# Este comando se ejecuta desde la terminal: flask init-db
@app.cli.command('init-db')
def init_db_command():
    """Crea las tablas de la base de datos y un usuario de ejemplo."""
    with app.app_context():
        print("Creando tablas de la base de datos...")
        try:
            db.create_all() # Crea las tablas definidas en models.py
            print(f"Tablas creadas (si no existían) en {DATABASE_PATH}")
            
            # Crear un usuario prestador por defecto si la tabla está vacía
            if not Prestador.query.first():
                print("Creando prestador de ejemplo...")
                default_prestador = Prestador(
                    boleta="2020000000", # ¡CAMBIA ESTA BOLETA POR UNA REAL!
                    nombre="Nombre Apellido Ejemplo",
                    programa_academico="Ingeniería Ejemplo",
                    semestre="Ejemplo",
                    email="prestador.ejemplo@example.com",
                    telefono="5512345678"
                )
                db.session.add(default_prestador)
                db.session.commit() # Guardar cambios en la BD
                print("Prestador de ejemplo creado con Boleta: 2020000000.")
            else:
                 print("Ya existen prestadores en la base de datos.")
        except Exception as e:
             print(f"ERROR al inicializar la base de datos: {e}")
             db.session.rollback() # Deshacer cambios si hubo error

# --- Rutas de la Aplicación ---

@app.route('/', methods=['GET', 'POST']) # Permitir POST para actualizar perfil
def show_input_form():
    # Simplificado: Asumimos un solo usuario/prestador por ahora.
    # En una app real, buscaríamos por ID de usuario logueado.
    prestador = Prestador.query.first() 
    
    if request.method == 'POST':
        # Lógica para actualizar los datos del prestador si se envía el formulario (opcional)
        if prestador:
            try:
                prestador.nombre = request.form.get('student_name', prestador.nombre)
                prestador.boleta = request.form.get('student_boleta', prestador.boleta) # Cuidado al cambiar boleta si es clave
                prestador.programa_academico = request.form.get('student_program', prestador.programa_academico)
                prestador.semestre = request.form.get('student_semester', prestador.semestre)
                prestador.email = request.form.get('student_email', prestador.email)
                prestador.telefono = request.form.get('student_phone', prestador.telefono)
                db.session.commit()
                flash('Datos del prestador actualizados.', 'success')
            except Exception as e:
                 db.session.rollback()
                 flash(f'Error al actualizar datos del prestador: {e}', 'danger')
        else:
             flash('No se encontró el prestador para actualizar.', 'warning')
        # Redirigir a GET para evitar reenvío del formulario al recargar
        return redirect(url_for('show_input_form'))

    # --- Lógica para GET ---
    today_date = datetime.date.today().strftime('%Y-%m-%d') 
    
    if not prestador:
        # Si no hay ningún prestador en la BD (después de init-db), mostrar error o valores vacíos
        prestador_data = {'boleta': '', 'nombre': '', 'programa_academico': '', 'semestre': '', 'email': '', 'telefono': ''}
        last_report_hours = 0
        flash("No se encontró información del prestador en la base de datos. Ejecuta 'flask init-db' o completa los datos.", "warning")
    else:
        prestador_data = {
            'student_name': prestador.nombre,
            'student_boleta': prestador.boleta,
            'student_program': prestador.programa_academico,
            'student_semester': prestador.semestre,
            'student_email': prestador.email,
            'student_phone': prestador.telefono,
        }
        # Cargar horas acumuladas del último reporte de este prestador
        last_report = ReporteMetadata.query.filter_by(prestador_boleta=prestador.boleta).order_by(ReporteMetadata.report_num.desc()).first()
        last_report_hours = last_report.accumulated_hours if last_report else 0

    default_form_data = { 
        'report_date': today_date, 
        'report_date_city': "Ciudad de México",
        'prestatario_name': "Escuela Superior de Ingeniería Textil", # Podría venir de DB también
        'authorizing_name': "M. en A. Shamash Frias Osorio", # Podría venir de DB también
        'authorizing_title': "Jefe de la unidad de informática", # Podría venir de DB también
        'previous_hours': last_report_hours or 0 # Usar 0 si no hay reporte previo
    }
    # Combinar datos del prestador (cargados de DB) con los defaults del formulario
    form_data_to_render = {**prestador_data, **default_form_data}

    return render_template('input_form.html', 
                           page_title="Registro de Horas de Servicio Social", 
                           data=form_data_to_render)


# Ruta AJAX para generar PDF
@app.route('/generate', methods=['POST'])
def generate_report_pdf():
    form_data = request.form.to_dict(flat=False) 
    report_data = {} 
    # ... (resto del procesamiento de datos y cálculos como en la versión anterior) ...
    # Asegúrate de copiar aquí toda la lógica de procesamiento de datos 
    # y cálculo de horas que tenías en la ruta /preview de la versión anterior.
    # --- Inicio Copia/Adaptación Procesamiento ---
    direct_copy_keys = [
        'report_num', 'period_start', 'period_end', 'report_date_city', 'report_date',
        'student_name', 'student_boleta', 'student_semester', 'student_program',
        'student_email', 'student_phone', 'prestatario_name', 'activities_description',
        'authorizing_name', 'authorizing_title', 'previous_hours'
    ]
    for key in direct_copy_keys:
        report_data[key] = form_data.get(key, [''])[0] 

    if not all(report_data.get(k) for k in ['report_num', 'period_start', 'period_end', 'report_date', 'student_boleta']):
         return jsonify({"success": False, "error": "Faltan datos básicos del reporte."}), 400
    
    student_boleta = report_data['student_boleta']
    prestador = Prestador.query.filter_by(boleta=student_boleta).first()
    if not prestador:
         return jsonify({"success": False, "error": f"No se encontró un prestador con la boleta {student_boleta}."}), 400
    # (Aquí podrías validar si los datos del prestador enviados coinciden con la BD)

    daily_logs = []
    total_month_hours = 0
    if 'log_date[]' in form_data:
        num_entries = len(form_data['log_date[]'])
        for i in range(num_entries):
            try:
                date_str = form_data.get('log_date[]', [])[i]; start_str = form_data.get('log_start_time[]', [])[i]; end_str = form_data.get('log_end_time[]', [])[i]
                if date_str and start_str and end_str:
                    start_dt = datetime.datetime.strptime(start_str, '%H:%M'); end_dt = datetime.datetime.strptime(end_str, '%H:%M')
                    if end_dt >= start_dt: duration = end_dt - start_dt
                    else: duration = (datetime.datetime.combine(datetime.date.min, end_dt.time()) + datetime.timedelta(days=1)) - datetime.datetime.combine(datetime.date.min, start_dt.time())
                    hours_today = round(duration.total_seconds() / 3600, 1)
                    if hours_today < 0: hours_today = 0 
                    daily_logs.append({'num': i + 1, 'date': date_str, 'start_time': start_str, 'end_time': end_str, 'hours_today': hours_today })
                    total_month_hours += hours_today
            except Exception as e: print(f"WARN (generate_report_pdf): Error procesando fila de hora {i}: {e}")

    report_data['daily_logs'] = daily_logs
    report_data['total_month_hours'] = round(total_month_hours, 1)
    try: previous_hours_float = float(report_data.get('previous_hours', 0))
    except (ValueError, TypeError): previous_hours_float = 0
    accumulated_hours = previous_hours_float + total_month_hours
    report_data['accumulated_hours'] = round(accumulated_hours, 1)
    # --- Fin Copia/Adaptación Procesamiento ---

    try:
        # Renderizar HTML
        html_string = render_template('report_preview.html', data=report_data)

        # Generar PDF
        pdf_filename_base = f"Reporte_{report_data.get('report_num','N')}_{student_boleta}_{uuid.uuid4().hex[:6]}.pdf"
        pdf_path = TEMP_PDF_FOLDER / pdf_filename_base
        css_path = STATIC_FOLDER / 'css' / 'style.css' 
        css_to_use = [CSS(filename=css_path)] if css_path.exists() else []
        base_url = request.url_root 
        html_obj = HTML(string=html_string, base_url=base_url)
        html_obj.write_pdf(str(pdf_path), stylesheets=css_to_use)
        print(f"INFO (generate_report_pdf): PDF generado temporalmente en '{pdf_path}'")

        # --- GUARDAR METADATOS EN BASE DE DATOS ---
        try:
             # Convertir fechas string a objetos date ANTES de guardar
             period_start_date = datetime.datetime.strptime(report_data['period_start'], '%Y-%m-%d').date() if report_data.get('period_start') else None
             period_end_date = datetime.datetime.strptime(report_data['period_end'], '%Y-%m-%d').date() if report_data.get('period_end') else None
             report_date_date = datetime.datetime.strptime(report_data['report_date'], '%Y-%m-%d').date() if report_data.get('report_date') else None

             new_report_meta = ReporteMetadata(
                 prestador_boleta = student_boleta,
                 report_num = int(report_data.get('report_num', 0)),
                 period_start = period_start_date,
                 period_end = period_end_date,
                 report_date = report_date_date,
                 report_date_city = report_data.get('report_date_city'),
                 prestatario_name = report_data.get('prestatario_name'),
                 authorizing_name = report_data.get('authorizing_name'),
                 authorizing_title = report_data.get('authorizing_title'),
                 activities_description = report_data.get('activities_description'),
                 total_month_hours = report_data.get('total_month_hours'),
                 accumulated_hours = report_data.get('accumulated_hours')
             )
             db.session.add(new_report_meta)
             db.session.commit()
             print(f"INFO (generate_report_pdf): Metadatos del reporte guardados en DB para Boleta {student_boleta}, Reporte No. {report_data.get('report_num','N')}")
             # Guardar las horas acumuladas actuales para la próxima vez
             # Esto se hace ahora consultando el último reporte en la ruta '/'
        except Exception as e:
            db.session.rollback()
            print(f"ERROR (generate_report_pdf): Guardando metadatos en DB: {e}")
            # Decidimos continuar y generar el PDF, pero el historial no se guardó
            flash("Advertencia: El PDF se generó, pero hubo un error al guardar el registro en el historial.", "warning")
        # -------------------------------------------

        pdf_filename_for_download = f"{TEMP_PDF_FOLDER_NAME}/{pdf_filename_base}"
        return jsonify({ "success": True, "pdf_filename": pdf_filename_for_download })

    except Exception as e:
        print(f"ERROR (generate_report_pdf): Error generando PDF: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc() 
        return jsonify({"success": False, "error": f"Error interno al generar el PDF. Revisa los logs del servidor."}), 500


# Ruta para Historial
@app.route('/history', methods=['GET'])
def report_history():
    # Simplificado: Asumir primer prestador. En app real, filtrar por usuario logueado.
    prestador = Prestador.query.first() 
    reports = []
    if prestador:
        reports = ReporteMetadata.query.filter_by(prestador_boleta=prestador.boleta)\
                                       .order_by(ReporteMetadata.report_num.desc())\
                                       .all()
    else:
         flash("No se encontró información del prestador para mostrar historial.", "warning")
    
    return render_template('report_history.html', 
                           page_title="Historial de Reportes", 
                           reports=reports)

# Ruta para Descargar PDF
@app.route(f'/download_pdf/{TEMP_PDF_FOLDER_NAME}/<path:filename>', methods=['GET'])
def download_pdf(filename):
    safe_path = TEMP_PDF_FOLDER.resolve() 
    file_path = safe_path / Path(filename).name 
    
    if not file_path.is_file() or file_path.parent != safe_path:
         print(f"ERROR (download_pdf): Acceso denegado o archivo no encontrado: {filename}")
         abort(404, description="Archivo no encontrado.")

    try:
        response = send_from_directory(directory=str(safe_path), path=file_path.name, as_attachment=True)
        @response.call_on_close
        def remove_file_after_request():
            try: os.remove(file_path)
            except OSError as e: print(f"ERROR (download_pdf): No se pudo eliminar {file_path.name}: {e}")
        return response
    except FileNotFoundError: abort(404, description="Archivo PDF temporal no encontrado.")
    except Exception as e:
         print(f"ERROR (download_pdf): Enviando archivo {filename}: {e}")
         abort(500, description="Error interno al enviar el archivo PDF.")

# Context processor para el año (igual que antes)
@app.context_processor
def inject_now():
    # return {'now': datetime.datetime.utcnow} # UTC
    return {'now': datetime.datetime.now} # Hora local del servidor


if __name__ == '__main__':
    with app.app_context(): 
        # Verificar si la base de datos existe, si no, crearla
        if not DATABASE_PATH.is_file():
            print(f"INFO (app.py): Archivo de base de datos no encontrado en {DATABASE_PATH}.")
            print("                 Creando base de datos y tablas...")
            try:
                 db.create_all()
                 print("INFO (app.py): Tablas creadas.")
                 # Intentar añadir prestador por defecto
                 if not Prestador.query.first():
                    print("INFO (app.py): Creando prestador de ejemplo...")
                    default_prestador = Prestador(boleta="2020000000", nombre="Prestador Ejemplo", programa_academico="Ejemplo", semestre="Ejemplo", email="ejemplo@example.com", telefono="0000000000")
                    db.session.add(default_prestador)
                    db.session.commit()
                    print("INFO (app.py): Prestador de ejemplo creado.")
            except Exception as e:
                 print(f"ERROR (app.py): Creando tablas/prestador inicial: {e}")
                 db.session.rollback()

    print("-----------------------------------------------------")
    print("--- Generador de Reportes de Servicio Social (Flask+DB) ---")
    print(f"Usando base de datos: sqlite:///{DATABASE_PATH.resolve()}")
    print(f"Accede al formulario en: http://localhost:5000 (o http://<IP>:5000)")
    print("Accede al historial en: http://localhost:5000/history")
    print("Presiona CTRL+C para detener el servidor.")
    print("-----------------------------------------------------")
    # debug=True es bueno para desarrollo, False para "producción" o demos estables
    # use_reloader=False puede ser útil si tienes problemas con doble ejecución de código al inicio
    app.run(host='0.0.0.0', port=5000, debug=True)