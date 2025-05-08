# -*- coding: utf-8 -*- # Especificar codificación (buena práctica)
import os
import numpy as np # Necesario para algunos cálculos o dependencias futuras
from flask import Flask, render_template, request, jsonify, send_from_directory, abort, flash, redirect, url_for
from pathlib import Path
import datetime
from babel.dates import format_date as babel_format_date
import locale
import uuid 
from weasyprint import HTML, CSS # Para generar PDF
import traceback # Para imprimir errores detallados
import random
# Importar la instancia db y los modelos desde models.py
# Asegúrate de que models.py esté en la misma carpeta y sea correcto
try:
    from models import db, Prestador, ReporteMetadata, DATABASE_PATH 
except ImportError as e:
    print("ERROR CRÍTICO: No se pudo importar desde models.py.")
    print("Asegúrate de que 'models.py' exista en el mismo directorio que 'app.py' y no tenga errores.")
    print(f"Error específico: {e}")
    import sys
    sys.exit(1) # Detener la aplicación si no se pueden importar los modelos

# --- Configuración de Locale ---
# (Intentar establecer el locale en español para el formato de fecha)
# Esto puede variar dependiendo del sistema operativo
locales_to_try = ['es_MX.UTF-8', 'es_ES.UTF-8', 'es_MX', 'es_ES', 'Spanish_Mexico', 'Spanish']
locale_set = False
for loc in locales_to_try:
    try:
        locale.setlocale(locale.LC_TIME, loc)
        print(f"INFO (app.py): Locale establecido a '{loc}' para formato de fecha.")
        locale_set = True
        break
    except locale.Error:
        continue
if not locale_set:
    print("ADVERTENCIA (app.py): No se pudo establecer un locale a español válido ('es_MX' o 'es_ES'). Las fechas pueden usar formato inglés.")

# --- Creación de la Aplicación Flask ---
app = Flask(__name__)

# --- Configuración de Flask y SQLAlchemy ---
BASE_DIR = Path(__file__).resolve().parent
STATIC_FOLDER = BASE_DIR / 'static'
TEMP_PDF_FOLDER_NAME = 'temp_pdf' 
TEMP_PDF_FOLDER = STATIC_FOLDER / TEMP_PDF_FOLDER_NAME
TEMP_PDF_FOLDER.mkdir(parents=True, exist_ok=True) # Crear carpeta si no existe

# Configurar la URI de la base de datos SQLite
# Usará el archivo 'reporter_data.db' en la misma carpeta que app.py
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH.resolve()}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desactivar tracking (recomendado)
# Establecer una clave secreta para Flask (necesaria para flash messages)
# ¡En producción, usa una clave segura y no la pongas directamente en el código!
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'cambia-esta-clave-secreta-en-produccion') 

# Inicializar la extensión SQLAlchemy con la app Flask
# Esto conecta los modelos definidos en models.py con la app
db.init_app(app)

# --- Filtros Jinja2 para Formatear Fechas ---
# (Se registran automáticamente con app.template_filter)
@app.template_filter('format_date')
def format_date_filter(value):
    """Formatea fecha a '10 de junio de 2024'."""
    if not value: return ""
    try:
        # Asegurar que trabajamos con un objeto date
        if isinstance(value, str): date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime.date): date_obj = value
        elif isinstance(value, datetime.datetime): date_obj = value.date()
        else: return value # Devolver original si no es tipo reconocible
        # Usar 'es' como locale genérico, Babel debería manejarlo
        return babel_format_date(date_obj, format='long', locale='es') 
    except Exception as e: # Capturar cualquier error de formato o tipo
        print(f"WARN (format_date_filter): Error formateando '{value}': {type(e).__name__} - {e}")
        return value # Devolver valor original si falla el formato

@app.template_filter('format_date_short')
def format_date_short_filter(value):
    """Formatea fecha a '13/mayo/2024'."""
    if not value: return ""
    try:
        # Asegurar que trabajamos con un objeto date
        if isinstance(value, str): date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime.date): date_obj = value
        elif isinstance(value, datetime.datetime): date_obj = value.date()
        else: return value
        # Obtener nombre del mes en español
        month_name = babel_format_date(date_obj, format='MMMM', locale='es').lower()
        return f"{date_obj.day}/{month_name}/{date_obj.year}"
    except Exception as e: # Capturar cualquier error
        print(f"WARN (format_date_short_filter): Error formateando '{value}': {type(e).__name__} - {e}")
        return value

# --- Comando para Crear la Base de Datos ---
# Se ejecuta desde la terminal con: flask init-db
@app.cli.command('init-db')
def init_db_command():
    """Crea las tablas de la base de datos definidas en models.py y un prestador de ejemplo."""
    # Necesitamos el contexto de la aplicación para operaciones de BD
    with app.app_context(): 
        print("INFO (init-db): Creando tablas de la base de datos...")
        try:
            db.create_all() 
            print(f"INFO (init-db): Tablas creadas (o ya existían) en {DATABASE_PATH}")
            
            # Añadir prestador de ejemplo solo si la tabla está vacía
            if not Prestador.query.first():
                print("INFO (init-db): Creando prestador de ejemplo...")
                default_boleta = "2020000000" # Boleta de ejemplo inicial
                default_prestador = Prestador(
                    boleta=default_boleta, 
                    nombre="Prestador Apellido Ejemplo",
                    programa_academico="Ingeniería Ejemplo",
                    semestre="Ejemplo",
                    email="prestador.ejemplo@example.com",
                    telefono="5512345678"
                )
                db.session.add(default_prestador) # Añadir a la sesión
                db.session.commit() # Guardar en la BD
                print(f"INFO (init-db): Prestador de ejemplo creado con Boleta: {default_boleta}.")
            else:
                 print("INFO (init-db): La tabla 'prestador' ya contiene datos.")
        except Exception as e:
             print(f"ERROR (init-db): Error al inicializar la base de datos: {type(e).__name__} - {e}")
             db.session.rollback() # Deshacer cambios si hubo error

# --- Rutas de la Aplicación ---

# Ruta principal para mostrar el formulario de entrada (precargado)
@app.route('/', methods=['GET'])
def show_input_form():
    # Simplificación: Carga el PRIMER prestador encontrado. 
    # En una app real, se usaría el ID del usuario logueado.
    prestador = Prestador.query.first() 
    today = datetime.date.today()
    
    # --- Generación Completa de Datos por Defecto para el Formulario ---
    # Calcular periodo de ejemplo (mes anterior)
    first_day_current_month = today.replace(day=1)
    end_date_default = first_day_current_month - datetime.timedelta(days=1) 
    start_date_default = end_date_default.replace(day=1) 
    period_start_str = start_date_default.strftime('%Y-%m-%d')
    period_end_str = end_date_default.strftime('%Y-%m-%d')
    report_date_str = today.strftime('%Y-%m-%d')

    prestador_data = {}
    last_report_hours = 0.0 # Asegurar que sea float
    last_report_num = 0
    
    if prestador:
        # Usar datos del prestador encontrado en la BD
        prestador_data = { 
            'student_name': prestador.nombre or '', 'student_boleta': prestador.boleta or '', 
            'student_program': prestador.programa_academico or '', 'student_semester': prestador.semestre or '', 
            'student_email': prestador.email or '', 'student_phone': prestador.telefono or '', 
        }
        # Buscar el último reporte para obtener horas acumuladas y sugerir número de reporte
        last_report = ReporteMetadata.query.filter_by(prestador_boleta=prestador.boleta).order_by(ReporteMetadata.report_num.desc()).first()
        if last_report:
            last_report_hours = last_report.accumulated_hours if last_report.accumulated_hours is not None else 0.0
            last_report_num = last_report.report_num if last_report.report_num is not None else 0
    else:
        # Usar datos de ejemplo placeholder si la BD está vacía
        prestador_data = { 
            'student_name': "Tu Nombre Apellido", 'student_boleta': "TuBoleta", 
            'student_program': "Tu Carrera", 'student_semester': "Tu Semestre", 
            'student_email': "tu@email.com", 'student_phone': "", 
        }
        # Mostrar mensaje solo si la base de datos existe pero no tiene prestadores
        if DATABASE_PATH.is_file(): 
            flash("No hay datos de prestador guardados. Completa tu información para crear tu perfil.", "info")
        
    # Generar logs diarios de ejemplo para precargar
    demo_daily_logs = []
    current_date = start_date_default
    days_processed = 0
    max_demo_days = 20 # Limitar número de días de ejemplo
    while current_date <= end_date_default and days_processed < max_demo_days:
        # Solo días entre semana (Lunes=0, Viernes=4)
        if current_date.weekday() < 5: 
             # 90% de probabilidad de haber registrado horas ese día
             if random.random() < 0.9: 
                 start_h = random.choice([8, 9, 9, 10]); start_m = random.choice([0, 15, 30])
                 # Duración más variable, incluyendo medias horas
                 duration_total_minutes = random.choice([240, 270, 300, 330, 360, 390, 420, 450, 480]) # 4 a 8 horas en minutos
                 start_time_obj = datetime.time(start_h, start_m)
                 start_datetime = datetime.datetime.combine(current_date, start_time_obj)
                 end_datetime = start_datetime + datetime.timedelta(minutes=duration_total_minutes)
                 end_time_obj = end_datetime.time()
                 
                 demo_daily_logs.append({ 
                     'date': current_date.strftime('%Y-%m-%d'), 
                     'start_time': start_time_obj.strftime('%H:%M'), 
                     'end_time': end_time_obj.strftime('%H:%M') 
                 })
                 days_processed += 1
        current_date += datetime.timedelta(days=1)
    # Añadir número de fila (solo para referencia interna, no se usa en plantilla)
    for i, log in enumerate(demo_daily_logs): log['num'] = i + 1

    # Descripción de actividades de ejemplo
    activities_default = ("- Mantenimiento preventivo y correctivo a equipos de cómputo del laboratorio.\n"
                          "- Soporte técnico a usuarios (resolución de dudas, instalación de software).\n"
                          "- Actualización de sistemas operativos y aplicaciones institucionales.\n"
                          "- Apoyo en la gestión del inventario de T.I. del departamento.\n"
                          "- Colaboración en la documentación de procedimientos internos.")

    # Combinar todos los datos para pasar a la plantilla
    form_data_to_render = {
        **prestador_data, 
        'report_num': last_report_num + 1, # Sugerir siguiente número
        'period_start': period_start_str, 'period_end': period_end_str,
        'report_date_city': "Ciudad de México", 'report_date': report_date_str,
        'previous_hours': last_report_hours or 0.0, # Horas previas (asegurar float)
        'prestatario_name': "Escuela Superior de Ingeniería Textil", # Datos fijos o de BD/config
        'authorizing_name': "M. en A. Shamash Frias Osorio", 
        'authorizing_title': "Jefe de la unidad de informática",
        'activities_description': activities_default, 
        'daily_logs': demo_daily_logs # Pasamos los logs generados
    }

    # Renderizar la plantilla del formulario, pasando los datos precargados
    return render_template('input_form.html', 
                           page_title="Registro de Horas (Precargado)", 
                           data=form_data_to_render) 

# --- FIN de Parte 1 de app.py ---

# Ruta AJAX para generar PDF, guardar historial y devolver enlace de descarga
@app.route('/generate', methods=['POST'])
def generate_report_pdf():
    # Verificar si la base de datos está disponible (si no, el resto fallará)
    if not DATABASE_PATH.is_file():
         print("ERROR CRITICO (generate): Archivo de base de datos no encontrado. Ejecuta 'flask init-db'.")
         return jsonify({"success": False, "error": "La base de datos no ha sido inicializada. Contacta al administrador."}), 500

    # Usar request.form ya que el JS envía FormData limpio (sin [])
    form_data = request.form 
    report_data = {} 
    
    # --- Recolección de Datos del Formulario ---
    # Recolectar campos principales y limpiar espacios en blanco
    direct_copy_keys = [
        'report_num', 'period_start', 'period_end', 'report_date_city', 'report_date',
        'student_name', 'student_boleta', 'student_semester', 'student_program',
        'student_email', 'student_phone', 'prestatario_name', 'activities_description',
        'authorizing_name', 'authorizing_title', 'previous_hours'
    ]
    for key in direct_copy_keys:
        report_data[key] = form_data.get(key, '').strip()

    # --- Validación de Datos del Backend ---
    errors = []
    required_fields = { # Campos requeridos y sus nombres legibles
        'report_num': "Número de Reporte", 'period_start': "Inicio del Periodo", 
        'period_end': "Fin del Periodo", 'report_date': "Fecha del Reporte",
        'student_boleta': "Boleta", 'student_name': "Nombre Completo",
        'student_program': "Programa Académico", 'student_semester': "Semestre",
        'student_email': "Correo Electrónico", #'student_phone': "Teléfono", # Teléfono es opcional
        'prestatario_name': "Nombre del Prestatario",
        'authorizing_name': "Nombre de quien Autoriza", 'authorizing_title': "Cargo de quien Autoriza",
        'activities_description': "Descripción de Actividades", 'previous_hours': "Horas Acumuladas Previas"
    }
    for key, label in required_fields.items():
        if not report_data.get(key): # Verificar si está vacío después de strip()
            errors.append(f"El campo '{label}' es requerido.")
    
    # Validar tipos numéricos
    report_num_int = None
    previous_hours_float = None
    try:
        report_num_int = int(report_data['report_num'])
        if report_num_int <= 0: errors.append("El número de reporte debe ser positivo.")
    except (ValueError, TypeError, KeyError): # KeyError si 'report_num' no existe
         errors.append("Número de reporte debe ser un entero válido.")
    try:
        previous_hours_float = float(report_data['previous_hours'])
        if previous_hours_float < 0: errors.append("Horas acumuladas previas no pueden ser negativas.")
    except (ValueError, TypeError, KeyError):
         errors.append("Horas acumuladas previas deben ser un número válido.")
         
    # Validar fechas y periodo
    start_date, end_date, report_date_obj = None, None, None
    try:
        start_date = datetime.datetime.strptime(report_data['period_start'], '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(report_data['period_end'], '%Y-%m-%d').date()
        report_date_obj = datetime.datetime.strptime(report_data['report_date'], '%Y-%m-%d').date()
        if start_date > end_date:
            errors.append("La fecha de inicio del periodo no puede ser posterior a la fecha de fin.")
        # Podrías añadir más validaciones: ej. periodo no mayor a X días, fecha reporte posterior a fin periodo
    except (ValueError, TypeError, KeyError):
         errors.append("Fechas de periodo/reporte inválidas, faltantes o con formato incorrecto (YYYY-MM-DD).")

    # Procesar y validar horas diarias enviadas
    daily_logs_processed = []
    total_month_hours = 0
    # Obtener las listas de datos de horas del formulario
    log_dates = request.form.getlist('log_date[]') 
    log_starts = request.form.getlist('log_start_time[]')
    log_ends = request.form.getlist('log_end_time[]')
    has_valid_rows = False

    # Asegurarse de que todas las listas tengan la misma longitud
    if len(log_dates) == len(log_starts) == len(log_ends):
         num_entries = len(log_dates)
         for i in range(num_entries):
             date_str, start_str, end_str = log_dates[i], log_starts[i], log_ends[i]
             
             # Procesar solo si la fila está completa
             if date_str and start_str and end_str: 
                 try:
                     # Validar fecha y horas individualmente
                     current_entry_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                     start_dt = datetime.datetime.strptime(start_str, '%H:%M')
                     end_dt = datetime.datetime.strptime(end_str, '%H:%M')
                     
                     # Validar que la fecha esté dentro del periodo reportado (opcional pero recomendado)
                     if not (start_date <= current_entry_date <= end_date):
                          errors.append(f"La fecha '{date_str}' en la fila {i+1} está fuera del periodo del reporte ({report_data['period_start']} a {report_data['period_end']}).")
                          continue # Saltar esta fila

                     # Calcular duración
                     if end_dt < start_dt: 
                         # Asumir que no cruza medianoche para servicio social, es un error
                         errors.append(f"Hora de salida no puede ser menor a la de entrada en fila {i+1} (Fecha: {date_str}).")
                         continue # Saltar esta fila
                     
                     duration = end_dt - start_dt
                     hours_today = round(duration.total_seconds() / 3600, 1)
                     
                     # Validar horas razonables (ej. no más de 12 horas al día)
                     if hours_today <= 0:
                         errors.append(f"El cálculo de horas para el día {date_str} (fila {i+1}) resultó en cero o negativo. Revisa las horas.")
                         continue
                     if hours_today > 12: # Límite ejemplo
                          errors.append(f"El número de horas ({hours_today}) para el día {date_str} (fila {i+1}) parece excesivo (>12h).")
                          # No necesariamente detenemos el proceso, pero podría ser una advertencia

                     daily_logs_processed.append({'num': i + 1, 'date': date_str, 'start_time': start_str, 'end_time': end_str, 'hours_today': hours_today })
                     total_month_hours += hours_today
                     has_valid_rows = True
                 except ValueError:
                     errors.append(f"Formato de fecha u hora inválido en la fila {i+1} (Fecha: {date_str}). Use YYYY-MM-DD y HH:MM.")
             elif date_str or start_str or end_str: # Fila iniciada pero incompleta
                 errors.append(f"La fila {i+1} de horas está incompleta. Debe llenar Fecha, Hora Entrada y Hora Salida, o eliminarla.")
         
         # Error si se enviaron filas pero ninguna fue válida/completa
         if num_entries > 0 and not has_valid_rows and not errors: 
            errors.append("No se registraron días de asistencia válidos y completos.")

    else: # Si las listas no coinciden (error de envío del form?)
         errors.append("Error en los datos de horas enviados desde el formulario.")

    # Si hubo algún error de validación, detener y devolverlos
    if errors:
        return jsonify({"success": False, "error": "Por favor, corrige los siguientes errores:\n- " + "\n- ".join(errors)}), 400
    # --- Fin Validación ---

    # Si la validación pasa, continuar...

    # Actualizar datos calculados en report_data para la plantilla y DB
    report_data['daily_logs'] = daily_logs_processed
    report_data['total_month_hours'] = round(total_month_hours, 1)
    accumulated_hours = previous_hours_float + total_month_hours
    report_data['accumulated_hours'] = round(accumulated_hours, 1)

    # --- Buscar/Actualizar/Crear Prestador en DB ---
    student_boleta = report_data['student_boleta']
    prestador = Prestador.query.filter_by(boleta=student_boleta).first()
    try:
        if prestador:
            # Actualizar datos existentes
            print(f"INFO (generate): Actualizando Prestador {student_boleta}")
            prestador.nombre = report_data.get('student_name', prestador.nombre)
            prestador.programa_academico = report_data.get('student_program', prestador.programa_academico)
            prestador.semestre = report_data.get('student_semester', prestador.semestre)
            prestador.email = report_data.get('student_email', prestador.email)
            prestador.telefono = report_data.get('student_phone', prestador.telefono)
        else:
            # Crear nuevo prestador
            print(f"INFO (generate): Creando Prestador {student_boleta}")
            prestador = Prestador(
                boleta=student_boleta,
                nombre=report_data.get('student_name'),
                programa_academico=report_data.get('student_program'),
                semestre=report_data.get('student_semester'),
                email=report_data.get('student_email'),
                telefono=report_data.get('student_phone')
            )
            db.session.add(prestador)
        # Guardar cambios del prestador (sea nuevo o actualizado)
        db.session.commit() 
    except Exception as e:
         db.session.rollback() # Deshacer si falla
         print(f"ERROR (generate): BD - Error al guardar/actualizar prestador {student_boleta}: {e}")
         # Devolver error 500 Internal Server Error
         return jsonify({"success": False, "error": f"Error al procesar datos del prestador en la base de datos."}), 500
    # --- Fin manejo Prestador ---
    
    # --- Generación PDF y Guardado de Metadatos del Reporte ---
    try:
        # 1. Renderizar la plantilla HTML con los datos finales
        # Usamos 'report_preview.html' como base para el PDF
        html_string = render_template('report_preview.html', data=report_data)

        # 2. Generar nombre de archivo único para el PDF temporal
        pdf_filename_base = f"Reporte_{report_data.get('report_num','?')}_{student_boleta}_{uuid.uuid4().hex[:6]}.pdf"
        pdf_path = TEMP_PDF_FOLDER / pdf_filename_base
        
        # 3. Preparar CSS para WeasyPrint
        css_path = STATIC_FOLDER / 'css' / 'style.css' 
        # Pasar la ruta del CSS a WeasyPrint
        css_to_use = [CSS(filename=str(css_path))] if css_path.exists() else []
        
        # 4. Crear objeto HTML de WeasyPrint
        # base_url ayuda a encontrar archivos estáticos (ej. logos) referenciados en el HTML
        # Usamos la URL raíz del servidor Flask como base
        base_url = request.url_root 
        html_obj = HTML(string=html_string, base_url=base_url)
        
        # 5. Escribir/Generar el archivo PDF
        html_obj.write_pdf(str(pdf_path), stylesheets=css_to_use)
        print(f"INFO (generate): PDF generado temporalmente en '{pdf_path}'")

        # 6. GUARDAR METADATOS DEL REPORTE EN BASE DE DATOS ---
        try:
             # Convertir fechas string (del formulario/report_data) a objetos date
             period_start_date = datetime.datetime.strptime(report_data['period_start'], '%Y-%m-%d').date() if report_data.get('period_start') else None
             period_end_date = datetime.datetime.strptime(report_data['period_end'], '%Y-%m-%d').date() if report_data.get('period_end') else None
             report_date_date = datetime.datetime.strptime(report_data['report_date'], '%Y-%m-%d').date() if report_data.get('report_date') else None

             # Crear la nueva entrada para el historial
             new_report_meta = ReporteMetadata(
                 prestador_boleta = student_boleta, # Enlazar con el prestador
                 report_num = int(report_data['report_num']), # Usar el número validado
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
                 # generated_at se pone automáticamente por el default en el modelo
                 # pdf_stored_path = str(pdf_path) # Descomentar si guardas PDFs permanentemente
             )
             db.session.add(new_report_meta) # Añadir a sesión
             db.session.commit() # Guardar en BD
             print(f"INFO (generate): Metadatos del reporte guardados en DB (ID: {new_report_meta.id})")
        
        except Exception as e:
            db.session.rollback() # Deshacer si falla el guardado del reporte
            print(f"ERROR (generate): Guardando metadatos del reporte en DB: {type(e).__name__} - {e}")
            # Informar al usuario, aunque el PDF se generó
            flash("Advertencia: El PDF se generó correctamente, pero hubo un error al guardar el registro en el historial.", "warning")
            # Continuamos para permitir la descarga del PDF, pero sin garantía de que esté en el historial
        # -------------------------------------------

        # 7. Devolver éxito y nombre de archivo para descarga al frontend (AJAX)
        pdf_filename_for_download = f"{TEMP_PDF_FOLDER_NAME}/{pdf_filename_base}"
        return jsonify({ "success": True, "pdf_filename": pdf_filename_for_download })

    except Exception as e:
        # Capturar errores durante la generación del PDF 
        print(f"ERROR CRÍTICO (generate): Error generando PDF: {type(e).__name__} - {e}")
        traceback.print_exc() # Imprimir traza completa para depuración
        return jsonify({"success": False, "error": f"Error interno del servidor al generar el PDF."}), 500

# --- FIN de Parte 2 de app.py ---

# --- Ruta para Mostrar el Historial de Reportes ---
@app.route('/history', methods=['GET'])
def report_history():
    """Muestra una lista de los reportes generados y guardados en la base de datos."""
    # Simplificación: Asume el primer prestador. En una app real, filtrarías por el usuario logueado.
    prestador = Prestador.query.first() 
    reports = []
    if prestador:
        # Busca todos los reportes asociados a la boleta del prestador encontrado
        # Ordena por número de reporte descendente para mostrar los más recientes primero
        reports = ReporteMetadata.query.filter_by(prestador_boleta=prestador.boleta)\
                                       .order_by(ReporteMetadata.report_num.desc())\
                                       .all()
        print(f"INFO (report_history): Encontrados {len(reports)} reportes para Boleta {prestador.boleta}")
    else:
         # Si no hay prestador en la BD, mostrar un mensaje flash
         flash("No se encontró información del prestador para mostrar el historial. Genera tu primer reporte.", "warning")
    
    # Renderiza la plantilla HTML del historial, pasando la lista de reportes encontrados
    return render_template('report_history.html', 
                           page_title="Historial de Reportes Generados", 
                           reports=reports)
# -----------------------------------------

# --- Ruta para Descargar el PDF Temporal Generado ---
# El nombre de archivo viene de la respuesta JSON del frontend
@app.route(f'/download_pdf/{TEMP_PDF_FOLDER_NAME}/<path:filename>', methods=['GET'])
def download_pdf(filename):
    """Sirve un archivo PDF generado previamente desde la carpeta temporal como descarga."""
    # Construir la ruta absoluta segura a la carpeta temporal
    safe_dir_path = TEMP_PDF_FOLDER.resolve() 
    # Construir la ruta completa al archivo solicitado, usando Path.name para evitar manipulación de directorios
    file_path = safe_dir_path / Path(filename).name 
    
    print(f"INFO (download_pdf): Solicitud para descargar: {file_path}")

    # Medida de seguridad: Verificar que el archivo solicitado esté realmente dentro de la carpeta temporal esperada
    if not str(file_path.resolve()).startswith(str(safe_dir_path)) or not file_path.is_file():
         print(f"ERROR (download_pdf): Intento de acceso inválido o archivo no encontrado: {filename}")
         abort(404, description="Archivo PDF no encontrado o acceso denegado.")

    try:
        # Usar send_from_directory de Flask para enviar el archivo de forma segura
        # as_attachment=True fuerza la descarga en lugar de mostrarlo en el navegador
        response = send_from_directory(directory=str(safe_path), 
                                       path=file_path.name, # Enviar solo el nombre del archivo
                                       as_attachment=True)
        
        # Registrar un callback para eliminar el archivo DESPUÉS de que la respuesta se haya enviado
        @response.call_on_close
        def remove_file_after_request():
            try:
                os.remove(file_path)
                print(f"INFO (download_pdf): Archivo temporal eliminado con éxito: {file_path.name}")
            except OSError as e:
                # Loguear error si no se pudo eliminar, pero no detener la respuesta
                print(f"ERROR (download_pdf): No se pudo eliminar el archivo temporal '{file_path.name}': {e}")

        return response
        
    except FileNotFoundError:
        print(f"ERROR (download_pdf): Archivo no encontrado en el sistema de archivos: {filename}")
        abort(404, description="Archivo PDF temporal no encontrado en el servidor.")
    except Exception as e:
         # Capturar otros posibles errores al enviar el archivo
         print(f"ERROR (download_pdf): Error inesperado al enviar archivo '{filename}': {type(e).__name__} - {e}")
         abort(500, description="Error interno del servidor al intentar enviar el archivo PDF.")
# -----------------------------------------

# --- Context processor para el año actual ---
# Hace que la variable 'now' esté disponible en todas las plantillas Jinja2
@app.context_processor
def inject_now():
    # Devolver la función now para que se evalúe al renderizar la plantilla
    return {'now': datetime.datetime.now} 
# -------------------------------------------

# --- Bloque de Ejecución Principal ---
# Este código se ejecuta solo cuando corres el script directamente con 'python app.py'
if __name__ == '__main__':
    # Verificar si la base de datos existe al iniciar (opcional, pero útil)
    # El comando 'flask init-db' es la forma recomendada de crearla/inicializarla.
    with app.app_context(): 
        if not DATABASE_PATH.is_file():
            print(f"\nADVERTENCIA (app.py): Archivo de base de datos no encontrado en {DATABASE_PATH}.")
            print(f"                 Por favor, ejecuta 'flask init-db' en tu terminal (con el venv activado)")
            print(f"                 dentro de la carpeta '{BASE_DIR}' para crear la base de datos y las tablas.\n")
            # Considera si quieres detener la app aquí si la BD es esencial desde el principio
            # import sys
            # sys.exit("ERROR: Base de datos no inicializada.")
            
    # Mensajes informativos al iniciar el servidor
    print("-----------------------------------------------------")
    print("--- Generador de Reportes de Servicio Social (Flask+DB) ---")
    print(f"Directorio Base: {BASE_DIR}")
    print(f"Usando Base de Datos: sqlite:///{DATABASE_PATH.resolve()}")
    print(f"Carpeta de PDFs Temporales: {TEMP_PDF_FOLDER}")
    print(f"Accede al formulario en: http://localhost:5000 (o http://<TU_IP>:5000)")
    print(f"Accede al historial en: http://localhost:5000/history")
    print("Modo Debug: ACTIVADO (El servidor se reiniciará con cambios en el código Python)")
    print("Presiona CTRL+C para detener el servidor.")
    print("-----------------------------------------------------")
    
    # Ejecutar la aplicación Flask
    # host='0.0.0.0' permite conexiones desde cualquier IP en tu red local (útil para probar desde otro dispositivo)
    # port=5000 es el puerto estándar de desarrollo de Flask
    # debug=True activa el modo de depuración (útil para desarrollo, muestra errores detallados y recarga automáticamente)
    # ¡NUNCA uses debug=True en un entorno de producción real!
    app.run(host='0.0.0.0', port=5000, debug=True) 
# --- FIN DEL ARCHIVO app.py ---