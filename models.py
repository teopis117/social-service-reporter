from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func # Para funciones SQL como NOW() o CURRENT_TIMESTAMP
from pathlib import Path
import datetime

# Creamos una instancia de SQLAlchemy SIN asociarla a una app todavía.
# La asociación se hará en app.py usando db.init_app(app).
db = SQLAlchemy()

# Definimos la ruta base para el archivo de la base de datos SQLite.
# Estará en el mismo directorio que este archivo (y app.py).
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / 'reporter_data.db' # Nombre del archivo de la BD

# --- Modelo para el Prestador de Servicio Social ---
class Prestador(db.Model):
    # Nombre de la tabla en la base de datos (opcional, por defecto sería 'prestador')
    __tablename__ = 'prestador' 
    
    # Columnas de la tabla:
    id = db.Column(db.Integer, primary_key=True) # Clave primaria autoincremental
    boleta = db.Column(db.String(10), unique=True, nullable=False, index=True) # Boleta única, no nula, indexada para búsquedas rápidas
    nombre = db.Column(db.String(150), nullable=False) # Nombre no nulo
    programa_academico = db.Column(db.String(100), nullable=True) # Puede ser nulo si no se sabe
    semestre = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True) # Email único, puede ser nulo
    telefono = db.Column(db.String(20), nullable=True) # Teléfono opcional
    
    # Relación con los reportes: Un prestador puede tener múltiples reportes.
    # 'ReporteMetadata' es el nombre de la clase relacionada.
    # 'backref='prestador'' crea un atributo '.prestador' en los objetos ReporteMetadata para acceder al prestador fácilmente.
    # 'lazy=True' significa que los reportes no se cargan automáticamente al cargar un prestador (mejor rendimiento).
    # 'cascade="all, delete-orphan"' significa que si borras un prestador, todos sus reportes asociados se borran automáticamente.
    reportes = db.relationship('ReporteMetadata', backref='prestador', lazy=True, cascade="all, delete-orphan")

    # Método útil para representar el objeto Prestador como texto (ej. al imprimirlo)
    def __repr__(self):
        return f'<Prestador {self.boleta} - {self.nombre}>'

# --- Modelo para los Metadatos de cada Reporte Generado ---
class ReporteMetadata(db.Model):
    # Nombre de la tabla
    __tablename__ = 'reporte_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Clave Foránea: Enlaza este reporte con un prestador usando su boleta.
    # 'prestador.boleta' se refiere a la columna 'boleta' de la tabla 'prestador'.
    # 'nullable=False' significa que cada reporte DEBE estar asociado a un prestador.
    # 'index=True' para búsquedas rápidas por boleta.
    # 'ondelete='CASCADE'' asegura que si se borra el Prestador, sus reportes se borren también (consistencia).
    prestador_boleta = db.Column(db.String(10), db.ForeignKey('prestador.boleta', ondelete='CASCADE'), nullable=False, index=True) 
    
    # Datos específicos del reporte
    report_num = db.Column(db.Integer, nullable=False) # El número de reporte (1, 2, 3...)
    period_start = db.Column(db.Date, nullable=True) # Fecha de inicio del periodo
    period_end = db.Column(db.Date, nullable=True) # Fecha de fin del periodo
    report_date = db.Column(db.Date, nullable=True) # Fecha en que se generó/firmó el reporte
    report_date_city = db.Column(db.String(100), nullable=True) # Ciudad donde se generó
    
    # Datos del prestatario y autorizante (se guardan en cada reporte)
    # Alternativa: Crear tablas separadas para Prestatario y Authorizer si se reutilizan mucho.
    prestatario_name = db.Column(db.String(200), nullable=True)
    authorizing_name = db.Column(db.String(150), nullable=True)
    authorizing_title = db.Column(db.String(150), nullable=True)
    
    # Resumen del reporte
    activities_description = db.Column(db.Text, nullable=True) # Permite textos largos
    total_month_hours = db.Column(db.Float, nullable=True) # Horas de este reporte específico
    accumulated_hours = db.Column(db.Float, nullable=True) # Horas acumuladas *hasta el final* de este reporte
    
    # Información de auditoría/tracking
    # 'default=datetime.datetime.utcnow' guarda automáticamente la fecha/hora de creación del registro.
    # 'index=True' si planeas buscar/ordenar por fecha de generación.
    generated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    
    # Opcional: Si quisieras guardar los PDFs permanentemente, añadirías esto:
    # pdf_stored_path = db.Column(db.String(255), nullable=True) 

    # Método útil para representar el objeto ReporteMetadata como texto
    def __repr__(self):
        periodo = f"{self.period_start.strftime('%Y-%m-%d') if self.period_start else 'N/A'} a {self.period_end.strftime('%Y-%m-%d') if self.period_end else 'N/A'}"
        return f'<Reporte No.{self.report_num} ({periodo}) para {self.prestador_boleta}>'