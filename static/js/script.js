document.addEventListener('DOMContentLoaded', function() {
    const addRowButton = document.getElementById('add-log-row');
    const logEntriesContainer = document.getElementById('daily-log-entries');

    // Función para añadir listeners a los botones de eliminar
    function addRemoveListener(button) {
        button.addEventListener('click', function() {
            // No eliminar si es la única fila que queda
            if (logEntriesContainer.querySelectorAll('.daily-log-row').length > 1) {
                 button.closest('.daily-log-row').remove();
            } else {
                 // Opcional: Limpiar los campos de la primera fila si se intenta eliminar
                 button.closest('.daily-log-row').querySelectorAll('input').forEach(input => input.value = '');
                 alert("Debe haber al menos una fila para el registro de horas.");
            }
        });
    }

    if (addRowButton && logEntriesContainer) {
        addRowButton.addEventListener('click', function() {
            // Clonar la primera fila como plantilla
            const templateRow = logEntriesContainer.querySelector('.daily-log-row');
            if (!templateRow) return; // Salir si no hay plantilla
            
            const newRow = templateRow.cloneNode(true);
            
            // Limpiar los valores de los inputs en la nueva fila clonada
            newRow.querySelectorAll('input').forEach(input => {
                 input.value = '';
                 // Requerido solo en la primera fila o basado en lógica? Por ahora clonamos el estado
                 // Si no quieres que las nuevas filas sean 'required', quita el atributo:
                 // input.removeAttribute('required'); 
            });
            
            // Asegurarse de que el botón de eliminar sea visible en la nueva fila
            const removeButton = newRow.querySelector('.remove-log-row');
            if (removeButton) {
                removeButton.style.display = 'inline-block'; 
                addRemoveListener(removeButton); // Añadir listener al nuevo botón
            }
            
            logEntriesContainer.appendChild(newRow);

            // Asegurarse que el botón de la primera fila sea visible si ahora hay más de una
            const firstRemoveButton = logEntriesContainer.querySelector('.daily-log-row:first-child .remove-log-row');
             if (firstRemoveButton && logEntriesContainer.querySelectorAll('.daily-log-row').length > 1) {
                 firstRemoveButton.style.display = 'inline-block';
             }
        });

        // Añadir listeners a los botones de eliminar existentes (incluido el primero)
        logEntriesContainer.querySelectorAll('.remove-log-row').forEach(button => {
             addRemoveListener(button);
        });

        // Ocultar el botón de eliminar de la primera fila si es la única inicialmente
        const firstRemoveButton = logEntriesContainer.querySelector('.daily-log-row:first-child .remove-log-row');
        if (firstRemoveButton && logEntriesContainer.querySelectorAll('.daily-log-row').length === 1) {
            firstRemoveButton.style.display = 'none';
        }
    }
});