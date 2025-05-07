from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from pathlib import Path
import datetime
from babel.dates import format_date as babel_format_date
import locale
import uuid # Para nombres de archivo únicos
from weasyprint import HTML, CSS # Importar WeasyPrint
import os # Para eliminar archivos temporales

# --- Configuración de Locale (igual que antes) ---
try:
    locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8') 
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        print("Advertencia: No se pudo establecer el locale a español. Los nombres de meses podrían aparecer en inglés.")

app = Flask(__name__)

# --- Configuración de Rutas (igual que antes, asegurando que BASE_DIR funcione) ---
BASE_DIR = Path(__file__).resolve().parent
STATIC_FOLDER = BASE_DIR / 'static'
TEMP_PDF_FOLDER_NAME = 'temp_pdf' # Carpeta para PDFs temporales
TEMP_PDF_FOLDER = STATIC_FOLDER / TEMP_PDF_FOLDER_NAME

# Crear carpeta de PDFs temporales si no existe
TEMP_PDF_FOLDER.mkdir(parents=True, exist_ok=True)

# --- Filtros Jinja2 (igual que antes) ---
def format_date_filter(value):
    if not value: return ""
    try:
        if isinstance(value, str): date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime.date): date_obj = value
        else: return value 
        return babel_format_date(date_obj, format='long', locale='es')
    except (ValueError, TypeError): return value

def format_date_short_filter(value):
     if not value: return ""
     try:
        if isinstance(value, str): date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime.date): date_obj = value
        else: return value
        month_name = babel_format_date(date_obj, format='MMMM', locale='es').lower()
        return f"{date_obj.day}/{month_name}/{date_obj.year}"
     except (ValueError, TypeError): return value

app.jinja_env.filters['format_date'] = format_date_filter
app.jinja_env.filters['format_date_short'] = format_date_short_filter

# --- Rutas ---

@app.route('/', methods=['GET'])
def show_input_form():
    today_date = datetime.date.today().strftime('%Y-%m-%d') 
    default_data = { 'report_date': today_date, 'report_date_city': "Ciudad de México" }
    # Datos del estudiante, etc., se cargarán con JS desde localStorage ahora
    return render_template('input_form.html', 
                           page_title="Registro de Horas de Servicio Social", 
                           data=default_data)

# --- RUTA MODIFICADA: Ahora genera PDF y devuelve info para descarga ---
@app.route('/generate', methods=['POST'])
def generate_report_pdf():
    form_data = request.form.to_dict(flat=False) 
    
    # --- Procesamiento de datos (igual que en /preview antes) ---
    preview_data = {} 
    direct_copy_keys = [
        'report_num', 'period_start', 'period_end', 'report_date_city', 'report_date',
        'student_name', 'student_boleta', 'student_semester', 'student_program',
        'student_email', 'student_phone', 'prestatario_name', 'activities_description',
        'authorizing_name', 'authorizing_title', 'previous_hours'
    ]
    for key in direct_copy_keys:
        preview_data[key] = form_data.get(key, [''])[0] 

    daily_logs = []
    total_month_hours = 0
    if 'log_date[]' in form_data:
        num_entries = len(form_data['log_date[]'])
        for i in range(num_entries):
            try:
                date = form_data.get('log_date[]', [])[i]
                start = form_data.get('log_start_time[]', [])[i]
                end = form_data.get('log_end_time[]', [])[i]
                
                if date and start and end:
                    start_dt = datetime.datetime.strptime(start, '%H:%M')
                    end_dt = datetime.datetime.strptime(end, '%H:%M')
                    if end_dt >= start_dt: duration = end_dt - start_dt
                    else: duration = (datetime.datetime.combine(datetime.date.min, end_dt.time()) + datetime.timedelta(days=1)) - datetime.datetime.combine(datetime.date.min, start_dt.time())
                    hours_today = round(duration.total_seconds() / 3600, 1)
                    daily_logs.append({'num': i + 1, 'date': date, 'start_time': start, 'end_time': end, 'hours_today': hours_today })
                    total_month_hours += hours_today
            except Exception as e: print(f"Advertencia: Error procesando fila de hora {i}: {e}")

    preview_data['daily_logs'] = daily_logs
    preview_data['total_month_hours'] = round(total_month_hours, 1)
    try: previous_hours_float = float(preview_data.get('previous_hours', 0))
    except ValueError: previous_hours_float = 0
    accumulated_hours = previous_hours_float + total_month_hours
    preview_data['accumulated_hours'] = round(accumulated_hours, 1)
    # --- Fin procesamiento de datos ---

    try:
        # 1. Renderizar la plantilla HTML con los datos
        # Usaremos 'report_preview.html' como plantilla para el PDF
        html_out = render_template('report_preview.html', data=preview_data)

        # 2. Generar el PDF usando WeasyPrint
        # Crear un nombre de archivo único para el PDF temporal
        pdf_filename = f"reporte_ss_{preview_data.get('student_boleta','temp')}_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = TEMP_PDF_FOLDER / pdf_filename
        
        # Añadir CSS para WeasyPrint (puede ser el mismo u otro específico)
        # WeasyPrint puede usar la etiqueta <link> en el HTML o puedes pasarle CSS
        css_path = STATIC_FOLDER / 'css' / 'style.css' # Usaremos el CSS principal
        css_string = CSS(filename=css_path) if css_path.exists() else None
        
        # Crear el objeto HTML de WeasyPrint
        # base_url es importante para que WeasyPrint encuentre archivos estáticos (como logos)
        html = HTML(string=html_out, base_url=str(BASE_DIR))
        
        # Escribir el PDF
        html.write_pdf(str(pdf_path), stylesheets=[css_string] if css_string else [])
        print(f"INFO (generate_report_pdf): PDF generado temporalmente en '{pdf_path}'")

        # 3. Devolver una respuesta JSON indicando éxito y el nombre del archivo
        return jsonify({
            "success": True,
            # Devolvemos una ruta relativa a 'static' para que el JS pueda construir la URL de descarga
            "pdf_filename": f"{TEMP_PDF_FOLDER_NAME}/{pdf_filename}" 
        })

    except Exception as e:
        print(f"ERROR (generate_report_pdf): Error generando PDF: {e}")
        import traceback
        traceback.print_exc() # Imprimir traza completa del error en el log del servidor
        return jsonify({"success": False, "error": f"Error interno al generar el PDF: {e}"}), 500

# --- NUEVA RUTA: Para descargar el PDF temporal generado ---
@app.route(f'/download_pdf/<path:filename>', methods=['GET'])
def download_pdf(filename):
    # Construir la ruta completa al archivo PDF temporal
    # ¡Importante! Validar 'filename' para evitar Path Traversal Attacks si fuera necesario
    # En este caso, confiamos en que viene de nuestra respuesta JSON anterior.
    # TEMP_PDF_FOLDER ya es una ruta absoluta segura.
    safe_path = TEMP_PDF_FOLDER.resolve() # Asegurar ruta absoluta
    file_path = safe_path / Path(filename).name # Tomar solo el nombre base del archivo
    
    # Verificar que el archivo solicitado esté dentro de nuestra carpeta segura
    if not file_path.is_file() or file_path.parent != safe_path:
         abort(404, description="Archivo no encontrado o acceso denegado.")

    try:
        # Enviar el archivo como descarga
        response = send_from_directory(directory=str(safe_path), 
                                       path=file_path.name, 
                                       as_attachment=True)
        
        # --- Opcional: Eliminar el archivo después de enviarlo ---
        # Esto requiere un poco más de cuidado, Flask lo envía en streaming.
        # Se puede usar un 'after_this_request' decorator.
        @response.call_on_close
        def remove_file_after_request():
            try:
                os.remove(file_path)
                print(f"INFO (download_pdf): Archivo temporal eliminado: {file_path.name}")
            except OSError as e:
                print(f"ERROR (download_pdf): No se pudo eliminar el archivo temporal {file_path.name}: {e}")
        # -----------------------------------------------------

        return response
        
    except FileNotFoundError:
        abort(404, description="Archivo PDF temporal no encontrado.")
    except Exception as e:
         print(f"ERROR (download_pdf): Error enviando archivo {filename}: {e}")
         abort(500, description="Error interno al enviar el archivo PDF.")

# Context processor para el año (igual que antes)
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow}

if __name__ == '__main__':
    print("Iniciando servidor Flask para el generador de reportes...")
    print(f"Directorio base: {BASE_DIR}")
    print(f"Carpeta de PDFs temporales: {TEMP_PDF_FOLDER}")
    print("Accede al formulario en http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)