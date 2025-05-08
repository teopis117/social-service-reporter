# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func 
from pathlib import Path
import datetime

# 1. Crear instancia de SQLAlchemy (se conecta a la app en app.py)
db = SQLAlchemy()

# 2. Definir la ruta de la base de datos
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / 'reporter_data.db' 

# 3. Definir el Modelo/Tabla para Prestador
class Prestador(db.Model):
    __tablename__ = 'prestador' 
    
    # Columnas (campos) de la tabla Prestador
    id = db.Column(db.Integer, primary_key=True) 
    boleta = db.Column(db.String(10), unique=True, nullable=False, index=True) 
    nombre = db.Column(db.String(150), nullable=False) 
    programa_academico = db.Column(db.String(100), nullable=True) 
    semestre = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True) 
    telefono = db.Column(db.String(20), nullable=True) 
    
    # Relación con la tabla ReporteMetadata
    # Un prestador puede tener muchos reportes. Si se borra el prestador, se borran sus reportes.
    reportes = db.relationship('ReporteMetadata', backref='prestador', lazy=True, cascade="all, delete-orphan")

    # Representación textual del objeto (útil para debugging)
    def __repr__(self):
        return f'<Prestador {self.boleta} - {self.nombre}>'

# 4. Definir el Modelo/Tabla para los Metadatos de los Reportes
class ReporteMetadata(db.Model):
    __tablename__ = 'reporte_metadata'
    
    # Columnas de la tabla ReporteMetadata
    id = db.Column(db.Integer, primary_key=True)
    # Clave foránea que conecta con la tabla 'prestador' usando la columna 'boleta'
    prestador_boleta = db.Column(db.String(10), db.ForeignKey('prestador.boleta', ondelete='CASCADE'), nullable=False, index=True) 
    
    # Datos del reporte en sí
    report_num = db.Column(db.Integer, nullable=False) 
    period_start = db.Column(db.Date, nullable=True) 
    period_end = db.Column(db.Date, nullable=True) 
    report_date = db.Column(db.Date, nullable=True) 
    report_date_city = db.Column(db.String(100), nullable=True) 
    
    # Datos relacionados (podrían normalizarse en otras tablas, pero aquí están bien para empezar)
    prestatario_name = db.Column(db.String(200), nullable=True)
    authorizing_name = db.Column(db.String(150), nullable=True)
    authorizing_title = db.Column(db.String(150), nullable=True)
    
    # Contenido y cálculos del reporte
    activities_description = db.Column(db.Text, nullable=True) 
    total_month_hours = db.Column(db.Float, nullable=True) 
    accumulated_hours = db.Column(db.Float, nullable=True) 
    
    # Fecha/hora en que se creó este registro en la base de datos
    generated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    # Representación textual del objeto
    def __repr__(self):
        # Definir un string para el periodo, manejando si las fechas son None
        periodo_str = "Periodo N/A"
        if self.period_start and self.period_end:
             try:
                 # Usar un formato simple aquí, el formateo complejo es para la vista
                 start_str = self.period_start.strftime('%Y-%m-%d')
                 end_str = self.period_end.strftime('%Y-%m-%d')
                 periodo_str = f"{start_str} a {end_str}"
             except AttributeError: # Por si acaso no son objetos date
                 periodo_str = f"{self.period_start} a {self.period_end}"
        
        # La línea final del método __repr__
        return f'<Reporte No.{self.report_num} ({periodo_str}) para {self.prestador_boleta}>'

# --- FIN DEL ARCHIVO models.py --- 
# (Asegúrate de que no haya absolutamente nada después de esta línea en tu archivo)