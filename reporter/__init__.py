# reporter/__init__.py

from flask import Blueprint

# Crear una instancia de Blueprint llamada 'reporter'.
# El primer argumento 'reporter' es el nombre del blueprint.
# __name__ ayuda a Flask a localizar recursos asociados con este blueprint.
# template_folder='templates': Opcional, le dice a Flask que busque plantillas 
#                              dentro de una subcarpeta 'templates' en este directorio 'reporter'.
#                              Si tus plantillas principales están en la carpeta 'templates' 
#                              general del proyecto, Flask las encontrará de todas formas.
# url_prefix='/': Significa que las rutas definidas aquí (ej. '/', '/history') 
#                 se montarán directamente en la raíz de la aplicación.
reporter_bp = Blueprint('reporter', __name__, template_folder='templates', url_prefix='/')

# Importamos las rutas (desde routes.py en este mismo directorio) DESPUÉS de crear el blueprint.
# Esto es importante para evitar errores de importación circular.
from . import routes