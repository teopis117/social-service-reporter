# reporter/routes.py

import os
from flask import (render_template, request, jsonify, send_from_directory, 
                   abort, flash, redirect, url_for, current_app)
from pathlib import Path
import datetime
import uuid 
from weasyprint import HTML, CSS
import traceback
import random 

# Importar 'db' y los modelos desde el módulo principal (un nivel arriba)
try:
    from ..models import db, Prestador, ReporteMetadata 
except ImportError:
    # Fallback si la estructura de importación es diferente
    from models import db, Prestador, ReporteMetadata

# Importar el Blueprint
from . import reporter_bp

# --- CONSTANTES ---
TEMP_PDF_FOLDER_NAME = 'temp_pdf' 
# ------------------

# --- RUTA PRINCIPAL (FORMULARIO) ---
@reporter_bp.route('/', methods=['GET'])
def show_input_form():
    # ... (LÓGICA COMPLETA DE show_input_form COMO TE LA DI ANTES) ...
    # Esta función precarga el formulario con datos de ejemplo o del primer prestador.
    # Asegúrate de tener aquí la versión completa que genera demo_daily_logs sin 'hours_today'.
    prestador = Prestador.query.first() 
    today = datetime.date.today()
    first_day_current_month = today.replace(day=1)
    end_date_default = first_day_current_month - datetime.timedelta(days=1) 
    start_date_default = end_date_default.replace(day=1) 
    period_start_str = start_date_default.strftime('%Y-%m-%d')
    period_end_str = end_date_default.strftime('%Y-%m-%d')
    report_date_str = today.strftime('%Y-%m-%d')
    prestador_data = {}
    last_report_hours = 0.0; last_report_num = 0
    if prestador:
        prestador_data = { 'student_name': prestador.nombre or '', 'student_boleta': prestador.boleta or '', 'student_program': prestador.programa_academico or '', 'student_semester': prestador.semestre or '', 'student_email': prestador.email or '', 'student_phone': prestador.telefono or '', }
        last_report = ReporteMetadata.query.filter_by(prestador_boleta=prestador.boleta).order_by(ReporteMetadata.report_num.desc()).first()
        if last_report: last_report_hours = last_report.accumulated_hours or 0.0; last_report_num = last_report.report_num or 0
    else:
        prestador_data = { 'student_name': "Tu Nombre Apellido", 'student_boleta': "TuBoleta", 'student_program': "Tu Carrera", 'student_semester': "Tu Semestre", 'student_email': "tu@email.com", 'student_phone': "", }
    demo_daily_logs = []
    current_date_iter = start_date_default; days_processed_for_demo = 0; max_demo_log_entries = 15
    while current_date_iter <= end_date_default and days_processed_for_demo < max_demo_log_entries:
        if current_date_iter.weekday() < 5: 
             if random.random() < 0.9: 
                 start_h = random.choice([8,9,10]); start_m = random.choice([0,30]); duration_h = random.choice([4,5,6,7,8]) 
                 start_time_obj = datetime.time(start_h, start_m); start_datetime_obj = datetime.datetime.combine(current_date_iter, start_time_obj); end_datetime_obj = start_datetime_obj + datetime.timedelta(hours=duration_h); end_time_obj = end_datetime_obj.time()
                 demo_daily_logs.append({ 'date': current_date_iter.strftime('%Y-%m-%d'), 'start_time': start_time_obj.strftime('%H:%M'), 'end_time': end_time_obj.strftime('%H:%M') }); days_processed_for_demo += 1
        current_date_iter += datetime.timedelta(days=1)
    if not demo_daily_logs and start_date_default <= end_date_default : demo_daily_logs.append({'date': start_date_default.strftime('%Y-%m-%d'), 'start_time': '09:00', 'end_time': '13:00'})
    random.shuffle(demo_daily_logs); 
    for i, log in enumerate(demo_daily_logs): log['num'] = i + 1
    activities_default = ("- Mantenimiento preventivo y correctivo.\n- Soporte técnico.\n- Actualización de software.\n- Gestión de inventario.\n- Documentación.")
    form_data_to_render = { **prestador_data, 'report_num': last_report_num + 1, 'period_start': period_start_str, 'period_end': period_end_str, 'report_date_city': "Ciudad de México", 'report_date': report_date_str, 'previous_hours': last_report_hours or 0.0, 'prestatario_name': "Escuela Ejemplo", 'authorizing_name': "Autorizante Ejemplo", 'authorizing_title': "Cargo Ejemplo", 'activities_description': activities_default, 'daily_logs': demo_daily_logs }
    return render_template('input_form.html', page_title="Registro (Precargado)", data=form_data_to_render) 

# Ruta AJAX para generar PDF
@reporter_bp.route('/generate', methods=['POST'])
def generate_report_pdf():
    # ... (LÓGICA COMPLETA DE generate_report_pdf COMO TE LA DI ANTES) ...
    # Esta es la función larga que incluye:
    # 1. Obtener STATIC_FOLDER y TEMP_PDF_FOLDER
    # 2. Recolección de datos del formulario (form_data, report_data)
    # 3. Validación DETALLADA de todos los campos (errors list)
    # 4. Procesamiento de horas diarias (daily_logs_processed, total_month_hours)
    # 5. Cálculo de horas acumuladas
    # 6. Lógica para BUSCAR/ACTUALIZAR/CREAR el Prestador en la BD
    # 7. Bloque try-except para la generación del PDF con WeasyPrint
    # 8. Bloque try-except anidado para GUARDAR ReporteMetadata en la BD
    # 9. Devolución de la respuesta JSON (success, pdf_filename, report_id)
    # ASEGÚRATE DE QUE ESTA FUNCIÓN ESTÉ COMPLETA Y DEFINIDA SOLO UNA VEZ.
    STATIC_FOLDER = Path(current_app.static_folder); TEMP_PDF_FOLDER = STATIC_FOLDER / TEMP_PDF_FOLDER_NAME
    form_data = request.form; report_data = {} 
    direct_copy_keys = ['report_num', 'period_start', 'period_end', 'report_date_city', 'report_date','student_name', 'student_boleta', 'student_semester', 'student_program','student_email', 'student_phone', 'prestatario_name', 'activities_description','authorizing_name', 'authorizing_title', 'previous_hours']
    for key in direct_copy_keys: report_data[key] = form_data.get(key, '').strip()
    errors = []; report_num_int = 0; previous_hours_float = 0.0; start_date=None; end_date=None; report_date_obj=None
    required_fields = {'report_num': "Número de Reporte", 'period_start': "Inicio del Periodo", 'period_end': "Fin del Periodo",'report_date': "Fecha del Reporte", 'student_boleta': "Boleta", 'student_name': "Nombre Completo",'student_program': "Programa Académico", 'student_semester': "Semestre", 'student_email': "Correo Electrónico",'prestatario_name': "Nombre del Prestatario", 'authorizing_name': "Nombre de quien Autoriza",'authorizing_title': "Cargo de quien Autoriza", 'activities_description': "Descripción de Actividades",'previous_hours': "Horas Acumuladas Previas"}
    for key, label in required_fields.items():
        if not report_data.get(key): errors.append(f"'{label}' es requerido.")
    try: report_num_int = int(report_data['report_num']); assert report_num_int > 0
    except: errors.append("Número de reporte inválido.")
    try: previous_hours_float = float(report_data['previous_hours']); assert previous_hours_float >= 0
    except: errors.append("Horas previas inválidas.")
    try: 
        start_date = datetime.datetime.strptime(report_data['period_start'], '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(report_data['period_end'], '%Y-%m-%d').date()
        report_date_obj = datetime.datetime.strptime(report_data['report_date'], '%Y-%m-%d').date()
        if start_date > end_date: errors.append("Periodo inválido.")
        if report_date_obj < end_date: errors.append("Fecha de reporte no puede ser anterior a fin de periodo.")
    except: errors.append("Fechas inválidas (YYYY-MM-DD).")
    daily_logs_processed = []; total_month_hours = 0.0; has_valid_rows = False
    log_dates = request.form.getlist('log_date[]'); log_starts = request.form.getlist('log_start_time[]'); log_ends = request.form.getlist('log_end_time[]')
    if len(log_dates) == len(log_starts) == len(log_ends):
         num_entries = len(log_dates)
         for i in range(num_entries):
             date_str, start_str, end_str = log_dates[i], log_starts[i], log_ends[i]
             if date_str and start_str and end_str: 
                 try:
                     current_entry_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                     start_dt_obj = datetime.datetime.strptime(start_str, '%H:%M'); end_dt_obj = datetime.datetime.strptime(end_str, '%H:%M')
                     if start_date and end_date and not (start_date <= current_entry_date <= end_date): errors.append(f"Fecha '{date_str}' (fila {i+1}) fuera de periodo."); continue 
                     if end_dt_obj < start_dt_obj: errors.append(f"Hora salida < entrada fila {i+1}."); continue 
                     duration = end_dt_obj - start_dt_obj; hours_today = round(duration.total_seconds() / 3600, 1);
                     if hours_today <= 0: errors.append(f"Horas <=0 fila {i+1}."); continue
                     # if hours_today > 12: errors.append(f"Horas excesivas (>12h) fila {i+1}."); # Puede ser advertencia
                     daily_logs_processed.append({'num': i + 1, 'date': date_str, 'start_time': start_str, 'end_time': end_str, 'hours_today': hours_today })
                     total_month_hours += hours_today; has_valid_rows = True
                 except ValueError: errors.append(f"Formato fecha/hora inválido fila {i+1}.")
             elif date_str or start_str or end_str: errors.append(f"Fila {i+1} de horas incompleta.")
         if num_entries > 0 and not has_valid_rows and not errors : errors.append("No se registraron días válidos.")
    elif len(log_dates) > 0: errors.append("Datos de horas inconsistentes.")
    if not daily_logs_processed and len(log_dates) == 0 and not has_valid_rows : errors.append("Se requiere al menos un día de asistencia.") # Ajuste para que no dé error si ya hay otros errores
        
    if errors: return jsonify({"success": False, "error": "Errores:\n- " + "\n- ".join(errors)}), 400
    report_data['daily_logs'] = daily_logs_processed
    report_data['total_month_hours'] = round(total_month_hours, 1)
    accumulated_hours = previous_hours_float + total_month_hours
    report_data['accumulated_hours'] = round(accumulated_hours, 1)
    student_boleta = report_data['student_boleta']
    prestador = Prestador.query.filter_by(boleta=student_boleta).first()
    try:
        if prestador: 
             prestador.nombre=report_data.get('student_name'); prestador.programa_academico=report_data.get('student_program'); prestador.semestre=report_data.get('student_semester'); prestador.email=report_data.get('student_email'); prestador.telefono=report_data.get('student_phone')
        else: 
             prestador = Prestador(boleta=student_boleta, nombre=report_data.get('student_name'), programa_academico=report_data.get('student_program'), semestre=report_data.get('student_semester'), email=report_data.get('student_email'), telefono=report_data.get('student_phone'))
             db.session.add(prestador)
        db.session.commit()
    except Exception as e: db.session.rollback(); print(f"ERROR BD Prestador: {e}"); return jsonify({"success": False, "error": f"Error BD al guardar prestador."}), 500
    new_report_meta_id = None
    try:
        html_string = render_template('report_preview.html', data=report_data)
        pdf_filename_base = f"Reporte_{report_num_int}_{student_boleta}_{uuid.uuid4().hex[:6]}.pdf"
        pdf_path = TEMP_PDF_FOLDER / pdf_filename_base
        css_path = STATIC_FOLDER / 'css' / 'style.css' 
        css_to_use = [CSS(filename=str(css_path))] if css_path.exists() else []
        html_obj = HTML(string=html_string, base_url=request.url_root)
        html_obj.write_pdf(str(pdf_path), stylesheets=css_to_use)
        print(f"INFO: PDF generado en '{pdf_path}'")
        try:
             new_report_meta = ReporteMetadata( prestador_boleta=student_boleta, report_num=report_num_int, period_start=start_date, period_end=end_date, report_date=report_date_obj, report_date_city=report_data.get('report_date_city'), prestatario_name=report_data.get('prestatario_name'), authorizing_name=report_data.get('authorizing_name'), authorizing_title=report_data.get('authorizing_title'), activities_description=report_data.get('activities_description'), total_month_hours=report_data.get('total_month_hours'), accumulated_hours=report_data.get('accumulated_hours'))
             db.session.add(new_report_meta)
             db.session.commit()
             new_report_meta_id = new_report_meta.id # Obtener el ID después del commit
             print(f"INFO: Metadatos guardados para Reporte No. {report_num_int} (ID: {new_report_meta_id})")
             flash(f"Reporte No. {report_num_int} generado y guardado en historial.", "success") 
        except Exception as e: db.session.rollback(); print(f"ERROR DB Meta: {e}"); flash("Advertencia: PDF generado, pero error al guardar historial.", "warning")
        
        pdf_filename_for_download = f"{TEMP_PDF_FOLDER_NAME}/{pdf_filename_base}"
        return jsonify({ "success": True, "pdf_filename": pdf_filename_for_download, "report_id": new_report_meta_id })
    except Exception as e:
        print(f"ERROR generando PDF/guardando meta: {e}"); traceback.print_exc() 
        return jsonify({"success": False, "error": f"Error interno al generar PDF."}), 500


# --- RUTA PARA PÁGINA DE ÉXITO ---
@reporter_bp.route('/report_success/<int:report_id>')
def report_success(report_id):
    report_details = ReporteMetadata.query.get_or_404(report_id)
    # El pdf_filename se pasa como query param desde el JS
    pdf_filename_from_query = request.args.get('pdf_filename') 
    return render_template('report_success.html',
                           page_title="Reporte Generado con Éxito",
                           report_details=report_details,
                           pdf_filename_for_download=pdf_filename_from_query)


# --- RUTA PARA HISTORIAL ---
@reporter_bp.route('/history', methods=['GET'])
def report_history():
    prestador = Prestador.query.first() 
    reports = []
    boleta_usada = "N/A" 
    if prestador:
        boleta_usada = prestador.boleta
        reports = ReporteMetadata.query.filter_by(prestador_boleta=prestador.boleta)\
                                       .order_by(ReporteMetadata.report_num.desc()).all()
    return render_template('report_history.html', 
                           page_title=f"Historial de Reportes [{boleta_usada}]", 
                           reports=reports)

# --- RUTA PARA DESCARGAR PDF ---
@reporter_bp.route(f'/download_pdf/{TEMP_PDF_FOLDER_NAME}/<path:filename>', methods=['GET'])
def download_pdf(filename):
    static_folder_path = Path(current_app.static_folder)
    temp_pdf_dir_path = static_folder_path / TEMP_PDF_FOLDER_NAME
    safe_dir_path = temp_pdf_dir_path.resolve() 
    file_path = safe_dir_path / Path(filename).name 
    if not file_path.is_file() or not str(file_path.resolve()).startswith(str(safe_dir_path)): abort(404)
    try:
        response = send_from_directory(directory=str(safe_dir_path), path=file_path.name, as_attachment=True)
        @response.call_on_close
        def remove_file_after_request():
            try: os.remove(file_path); print(f"INFO: Archivo temporal eliminado: {file_path.name}")
            except OSError as e: print(f"ERROR: No se pudo eliminar {file_path.name}: {e}")
        return response
    except Exception as e: print(f"ERROR enviando archivo {filename}: {e}"); abort(500)

# --- FIN DE reporter/routes.py ---