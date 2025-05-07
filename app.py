from flask import Flask, render_template, request 
# Eliminado jsonify porque no lo usamos en esta fase
# Eliminado send_from_directory porque no servimos archivos individuales aún (solo via static)
from pathlib import Path
import datetime
# Importar Babel para formato de fechas
from babel.dates import format_date as babel_format_date
import locale # Para asegurar locale español si Babel no lo toma por defecto

# Intentar establecer locale en español (puede depender del sistema operativo)
try:
    locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8') 
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        print("Advertencia: No se pudo establecer el locale a español. Los nombres de meses podrían aparecer en inglés.")

app = Flask(__name__)

# Configuración básica
BASE_DIR = Path(__file__).resolve().parent

# --- Filtros Jinja2 para Formatear Fechas ---
def format_date_filter(value):
    """Formatea fecha a '10 de junio de 2024'."""
    if not value: return ""
    try:
        if isinstance(value, str):
            date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime.date):
            date_obj = value
        else:
            return value 
        return babel_format_date(date_obj, format='long', locale='es') # Usar 'es' general
    except (ValueError, TypeError):
        return value # Devolver sin cambios si hay error

def format_date_short_filter(value):
    """Formatea fecha a '13/mayo/2024'."""
    if not value: return ""
    try:
        if isinstance(value, str):
            date_obj = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime.date):
            date_obj = value
        else:
            return value
        # Formato día/mes(texto)/año
        month_name = babel_format_date(date_obj, format='MMMM', locale='es').lower()
        return f"{date_obj.day}/{month_name}/{date_obj.year}"
    except (ValueError, TypeError):
        return value

# Registrar los filtros con Jinja2
app.jinja_env.filters['format_date'] = format_date_filter
app.jinja_env.filters['format_date_short'] = format_date_short_filter

# --- Rutas de la Aplicación ---

# Ruta para mostrar el formulario de entrada de datos
@app.route('/', methods=['GET'])
def show_input_form():
    today_date = datetime.date.today().strftime('%Y-%m-%d') 
    # Datos por defecto para el formulario
    default_data = {
        'report_date': today_date,
        'report_date_city': "Ciudad de México",
        # Precargar datos del estudiante como ejemplo
        'student_name': "Peña Atanasio Alberto", 
        'student_boleta': "2020630367",
        'student_program': "Sistemas Computacionales",
        'student_semester': "Egresado",
        'student_email': "apenaa1600@alumno.ipn.mx",
        'student_phone': "5511353956",
        'prestatario_name': "Escuela Superior de Ingeniería Textil",
        'authorizing_name': "M. en A. Shamash Frias Osorio",
        'authorizing_title': "Jefe de la unidad de informática",
        'previous_hours': 0 # Empezar con 0 horas acumuladas previas
    }
    return render_template('input_form.html', 
                           page_title="Registro de Horas de Servicio Social", 
                           data=default_data)

# Ruta para manejar el envío del formulario y mostrar la vista previa
@app.route('/preview', methods=['POST'])
def generate_preview():
    # Recoger todos los datos del formulario
    form_data = request.form.to_dict(flat=False) 
    
    # Procesar los datos (limpiar, calcular totales)
    preview_data = {} # Diccionario para pasar a la plantilla
    
    # Copiar datos directos del formulario
    direct_copy_keys = [
        'report_num', 'period_start', 'period_end', 'report_date_city', 'report_date',
        'student_name', 'student_boleta', 'student_semester', 'student_program',
        'student_email', 'student_phone', 'prestatario_name', 'activities_description',
        'authorizing_name', 'authorizing_title', 'previous_hours'
    ]
    for key in direct_copy_keys:
        # .get(key, [''])[0] toma el primer valor de la lista o '' si no existe
        preview_data[key] = form_data.get(key, [''])[0] 

    # Procesar horas diarias
    daily_logs = []
    total_month_hours = 0
    if 'log_date[]' in form_data:
        num_entries = len(form_data['log_date[]'])
        for i in range(num_entries):
            try:
                date = form_data.get('log_date[]', [])[i]
                start = form_data.get('log_start_time[]', [])[i]
                end = form_data.get('log_end_time[]', [])[i]
                
                if date and start and end: # Solo procesar si todos los campos tienen valor
                    start_dt = datetime.datetime.strptime(start, '%H:%M')
                    end_dt = datetime.datetime.strptime(end, '%H:%M')
                    
                    # Cálculo de horas (manejo simple, podría necesitar ajuste para medianoche)
                    if end_dt >= start_dt:
                        duration = end_dt - start_dt
                    else: # Asumir que termina al día siguiente (poco probable para servicio social)
                        duration = (datetime.datetime.combine(datetime.date.min, end_dt.time()) + datetime.timedelta(days=1)) - datetime.datetime.combine(datetime.date.min, start_dt.time())
                    
                    hours_today = round(duration.total_seconds() / 3600, 1)
                    
                    daily_logs.append({
                        'num': i + 1,
                        'date': date,
                        'start_time': start,
                        'end_time': end,
                        'hours_today': hours_today 
                    })
                    total_month_hours += hours_today
            except Exception as e:
                print(f"Advertencia: Error procesando fila de hora {i} (Fecha: {date}, Inicio: {start}, Fin: {end}). Error: {e}")
                # Omitir fila con error

    preview_data['daily_logs'] = daily_logs
    preview_data['total_month_hours'] = round(total_month_hours, 1)

    # Calcular horas acumuladas
    try:
        previous_hours_float = float(preview_data.get('previous_hours', 0))
    except ValueError:
        previous_hours_float = 0 # Default a 0 si no es un número válido
        
    accumulated_hours = previous_hours_float + total_month_hours
    preview_data['accumulated_hours'] = round(accumulated_hours, 1)

    # Renderizar la plantilla de vista previa con los datos procesados
    return render_template('report_preview.html', 
                           page_title="Vista Previa del Reporte", 
                           data=preview_data)

# Función para obtener el año actual (para el footer)
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow}

if __name__ == '__main__':
    print("Iniciando servidor Flask para el generador de reportes...")
    print("Accede al formulario en http://localhost:5000")
    # host='0.0.0.0' permite acceso desde otras máquinas en la red
    # debug=True recarga automáticamente el servidor cuando cambias el código Python
    app.run(host='0.0.0.0', port=5000, debug=True)