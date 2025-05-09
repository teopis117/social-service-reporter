// static/js/script.js (Sprint: Corregir JS y Flujo de Éxito)
document.addEventListener('DOMContentLoaded', function() {
    // --- Obtener Elementos del DOM ---
    const form = document.getElementById('report-form');
    const submitButton = document.getElementById('submit-button'); 
    const logEntriesContainer = document.getElementById('daily-log-entries');
    const addRowButton = document.getElementById('add-log-row');
    const previousHoursInput = document.getElementById('previous_hours'); 
    const activitiesTextarea = document.getElementById('activities_description');
    const activityTypesContainer = document.getElementById('activity-types-selection');
    const generateDescButton = document.getElementById('generate-description');
    const demoDataButton = document.getElementById('fill-demo-data');

    const loadingProgressArea = document.getElementById('loading-progress-area');
    const progressBar = document.getElementById('progress-bar');
    const progressStageText = document.getElementById('progress-stage-text');
    
    const toastPlacementContainer = document.querySelector('.toast-container'); 
    
    const hollywoodConsoleDiv = document.getElementById('hollywood-console');
    const consoleOutputPre = document.getElementById('console-output');
    
    let progressIntervalId = null; 
    let totalHoursDisplaySpan = document.getElementById('total-hours-display'); 

    // --- Crear Span para Total Horas si no existe ---
    if (!totalHoursDisplaySpan && addRowButton && addRowButton.parentNode) { 
        const containerForTotals = document.createElement('div');
        containerForTotals.id = 'total-hours-live-container'; 
        containerForTotals.classList.add('mt-3', 'd-flex', 'justify-content-end', 'align-items-center'); 
        const totalHoursLabel = document.createElement('span'); 
        totalHoursLabel.textContent = 'Total Horas del Mes Calculadas: '; 
        totalHoursLabel.classList.add('align-self-center', 'me-1', 'fw-medium');
        totalHoursDisplaySpan = document.createElement('span');
        totalHoursDisplaySpan.id = 'total-hours-display';
        totalHoursDisplaySpan.classList.add('fw-bold', 'fs-5', 'text-primary');
        containerForTotals.appendChild(totalHoursLabel);
        containerForTotals.appendChild(totalHoursDisplaySpan);
        addRowButton.parentNode.insertBefore(containerForTotals, addRowButton);
    }
    
    // --- Declaración de Funciones Principales (antes de su uso extensivo) ---

    function calculateHoursForRow(row) { 
        const startTimeInput = row.querySelector('input[name="log_start_time[]"]');
        const endTimeInput = row.querySelector('input[name="log_end_time[]"]');
        const calculatedHoursInput = row.querySelector('.daily-hours-calculated'); // Para feedback visual
        
        // Limpiar errores visuales previos de esta fila
        if(startTimeInput) startTimeInput.classList.remove('time-input-error', 'is-invalid');
        if(endTimeInput) endTimeInput.classList.remove('time-input-error', 'is-invalid');
        if(calculatedHoursInput) calculatedHoursInput.value = ''; 

        let hoursToday = 0;
        if (startTimeInput && endTimeInput && startTimeInput.value && endTimeInput.value) {
            const start = startTimeInput.value; const end = endTimeInput.value;
            try {
                 const startDate = new Date(`1970-01-01T${start}:00Z`); 
                 const endDate = new Date(`1970-01-01T${end}:00Z`);
                 let duration = endDate.getTime() - startDate.getTime(); 

                 if (duration < 0) { 
                     if(calculatedHoursInput) calculatedHoursInput.value = "Error";
                     if(startTimeInput) startTimeInput.classList.add('time-input-error');
                     if(endTimeInput) endTimeInput.classList.add('time-input-error');
                     return 0; // Devolver 0 para no sumar al total
                 }
                 hoursToday = Math.round((duration / (1000 * 60 * 60)) * 10) / 10; 
                 if (hoursToday <= 0) {
                     if(calculatedHoursInput) calculatedHoursInput.value = "Inválido";
                     if(startTimeInput) startTimeInput.classList.add('time-input-error');
                     if(endTimeInput) endTimeInput.classList.add('time-input-error');
                 } else {
                    if(calculatedHoursInput) calculatedHoursInput.value = hoursToday.toFixed(1);
                 }
            } catch(e) { 
                console.error("Error parseando horas para la fila:", e); 
                if(calculatedHoursInput) calculatedHoursInput.value = "Inválido";
                hoursToday = 0;
            }
        }
        return hoursToday >= 0 ? hoursToday : 0;
    }

    function updateTotalHours() { 
        let totalMonthHours = 0;
        if(logEntriesContainer){
             logEntriesContainer.querySelectorAll('.daily-log-row:not(#log-row-template)').forEach(row => {
                // Usar el valor ya calculado y mostrado si está disponible y es válido
                const calculatedInput = row.querySelector('.daily-hours-calculated');
                if(calculatedInput && calculatedInput.value && !isNaN(parseFloat(calculatedInput.value)) && parseFloat(calculatedInput.value) > 0 ) {
                    totalMonthHours += parseFloat(calculatedInput.value);
                } else if (!calculatedInput || !calculatedInput.value) { // Si no hay input o está vacío, recalcular
                    totalMonthHours += calculateHoursForRow(row); // Esta función ya actualiza el display individual
                }
                // Si calculatedInput.value es "Error" o "Inválido", no suma (calculateHoursForRow devuelve 0)
            });
        }
        if(totalHoursDisplaySpan) { totalHoursDisplaySpan.textContent = totalMonthHours.toFixed(1); }
    }

    function addRealtimeCalculationListeners(row) { 
        const inputs = row.querySelectorAll('input[name="log_start_time[]"], input[name="log_end_time[]"]');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                calculateHoursForRow(row); // Primero calcula y muestra para la fila
                updateTotalHours(); // Luego actualiza el total general
            }); 
            input.addEventListener('input', () => { // También al escribir para más reactividad
                calculateHoursForRow(row);
                updateTotalHours();
            }); 
        });
        // También al cambiar la fecha, por si afecta alguna lógica de validación futura
        const dateInput = row.querySelector('input[name="log_date[]"]');
        if (dateInput) {
            dateInput.addEventListener('change', () => {
                calculateHoursForRow(row);
                updateTotalHours();
            });
        }
    }

    function addRemoveListener(button) { /* ...código como antes... */ }
    function checkFirstRowRemoveButtonVisibility() { /* ...código como antes... */ }

    // Inicialización de Filas de Horas (Asegurar que esto esté después de definir las funciones que usa)
    if (addRowButton && logEntriesContainer) {
        addRowButton.addEventListener('click', function() { /* ... (código como antes, llama a addRealtimeCalculationListeners) ... */ });
        // Listeners iniciales para filas precargadas
        logEntriesContainer.querySelectorAll('.daily-log-row:not(#log-row-template)').forEach((row) => { 
            const removeButton = row.querySelector('.remove-log-row');
            if (removeButton) addRemoveListener(removeButton);
            addRealtimeCalculationListeners(row); // <- Llama a listeners
            calculateHoursForRow(row); // <- Calcula y muestra para la fila
        });
        checkFirstRowRemoveButtonVisibility(); 
        updateTotalHours(); // Calcular total inicial DESPUÉS de procesar todas las filas
    }
        // --- REFINADA: Función de Validación ---
    function validateForm() {
        console.log("DEBUG (validateForm): Iniciando validación...");
        let isValid = true;
        let firstErrorField = null; 
        const errorMessagesList = [];

        // Limpiar validación previa
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('.field-error-text').forEach(el => el.remove()); 

        function invalidateField(inputElement, message) {
            if (inputElement) {
                inputElement.classList.add('is-invalid');
                if (!firstErrorField) firstErrorField = inputElement;
            }
            if (message && !errorMessagesList.includes(message)) {
                errorMessagesList.push(message);
            }
            isValid = false;
        }

        // Validar campos requeridos explícitos
        form.querySelectorAll('input[required]:not([name^="log_"]):not([type="file"]), textarea[required]').forEach(input => {
            if (!input.value.trim()) {
                const label = form.querySelector(`label[for="${input.id}"]`);
                const fieldName = label ? label.textContent.replace(':', '').trim() : (input.name || input.id);
                const msg = `El campo "${fieldName}" es requerido.`;
                console.log(`DEBUG (validateForm): ${msg}`);
                invalidateField(input, msg);
            }
        });

        // Validar filas de horas
        let hasAtLeastOneCompleteRow = false;
        const hourRows = logEntriesContainer ? logEntriesContainer.querySelectorAll('.daily-log-row:not(#log-row-template)') : [];
        
        if (hourRows.length === 0) {
            const msg = "Debes registrar al menos un día de asistencia.";
            console.log(`DEBUG (validateForm): ${msg}`);
            errorMessagesList.push(msg);
            isValid = false; 
        }

        hourRows.forEach((row, index) => {
            const dateInput = row.querySelector('input[name="log_date[]"]');
            const startInput = row.querySelector('input[name="log_start_time[]"]');
            const endInput = row.querySelector('input[name="log_end_time[]"]');

            const dateFilled = dateInput && dateInput.value.trim();
            const startFilled = startInput && startInput.value.trim();
            const endFilled = endInput && endInput.value.trim();

            let rowHasData = dateFilled || startFilled || endFilled;

            if (rowHasData) {
                let rowIsValid = true;
                if (!dateFilled) { invalidateField(dateInput, `Fila ${index + 1}: Fecha es requerida.`); rowIsValid = false; }
                if (!startFilled) { invalidateField(startInput, `Fila ${index + 1}: Hora de entrada es requerida.`); rowIsValid = false; }
                if (!endFilled) { invalidateField(endInput, `Fila ${index + 1}: Hora de salida es requerida.`); rowIsValid = false; }

                if (rowIsValid) {
                    try {
                        const baseDate = '1970-01-01T';
                        const startTime = new Date(baseDate + startFilled + ':00Z').getTime();
                        const endTime = new Date(baseDate + endFilled + ':00Z').getTime();

                        if (endTime < startTime) {
                            invalidateField(endInput, `Fila ${index + 1}: Hora de salida no puede ser anterior a la entrada.`);
                            if(startInput) startInput.classList.add('is-invalid'); 
                            rowIsValid = false;
                        } else if (endTime === startTime){
                            invalidateField(endInput, `Fila ${index + 1}: Horas de entrada y salida no pueden ser iguales.`);
                            if(startInput) startInput.classList.add('is-invalid');
                            rowIsValid = false;
                        }
                    } catch (e) {
                        invalidateField(startInput, `Fila ${index + 1}: Formato de hora inválido.`);
                        invalidateField(endInput, null); 
                        rowIsValid = false;
                    }
                }
                if (rowIsValid) {
                    hasAtLeastOneCompleteRow = true;
                } else {
                     isValid = false; 
                }
            } else if (hourRows.length === 1 && !dateFilled && !startFilled && !endFilled && dateInput.required) {
                invalidateField(dateInput, `Fila ${index + 1}: Debes completar esta fila de horas o eliminarla si no aplica.`);
                if(startInput) invalidateField(startInput, null);
                if(endInput) invalidateField(endInput, null);
                isValid = false;
            }
        });

        if (hourRows.length > 0 && !hasAtLeastOneCompleteRow && isValid) {
            const msg = "Debes tener al menos una fila de horas completa y válida.";
            console.log(`DEBUG (validateForm): ${msg}`);
            errorMessagesList.push(msg);
            isValid = false; 
            if (!firstErrorField && hourRows[0]) {
                const firstRowInputs = hourRows[0].querySelectorAll('input');
                firstRowInputs.forEach(inp => inp.classList.add('is-invalid'));
                if(firstRowInputs[0]) firstErrorField = firstRowInputs[0];
            }
        }
        
        if (!isValid) {
            let finalErrorMessage = "Por favor, corrige los errores indicados.";
            if (errorMessagesList.length > 0) {
                finalErrorMessage = "Por favor, corrige los siguientes errores:\n- " + errorMessagesList.join("\n- ");
            }
            showError(finalErrorMessage, errorMessagesList); // showError ahora usará toasts
            if (firstErrorField) {
                firstErrorField.focus(); 
                firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
        console.log("DEBUG: Resultado final de validateForm():", isValid);
        return isValid;
    }
    function resetFeedbackMessages() {
        // Si usas toasts de Bootstrap, normalmente no necesitas limpiar nada aquí.
    }
    // Modificar showError para usar Toasts y mostrar detalles
    function showError(message, errorMessagesList = []) { 
        resetFeedbackMessages(); 
        if (progressIntervalId) clearInterval(progressIntervalId);
        if(loadingProgressArea) loadingProgressArea.style.display = 'none'; 
        if (hollywoodConsoleDiv && consoleOutputPre) { 
            hollywoodConsoleDiv.classList.remove('hollywood-console-visible');
            hollywoodConsoleDiv.classList.add('hollywood-console-hidden');
        }
        let mainMessage = "Error de Validación";
        let detailMessages = message;
        if (message.startsWith("Por favor, corrige los siguientes errores:\n- ")) {
            mainMessage = "Errores de Validación Detectados";
            detailMessages = message.substring("Por favor, corrige los siguientes errores:\n- ".length).replace(/\n- /g, '<br>- ');
        } else if (message.startsWith("Error al generar reporte:")){
             mainMessage = "Error en el Servidor";
             detailMessages = message;
        }
        showToast(
            mainMessage + 
            (errorMessagesList.length > 0 
                ? "<br><small>Detalles:</small><ul class='text-start small ps-4 mb-0'><li>" + errorMessagesList.join("</li><li>") + "</li></ul>" 
                : `<br><small>${detailMessages}</small>`), 
            'danger'
        ); 
    }
    function getCleanFormData() {
        // Puedes personalizar aquí si necesitas limpiar o transformar datos antes de enviar
        return new FormData(form);
    }
    // --- Envío del Formulario con AJAX (MODIFICADO para usar la nueva página de éxito) ---
    if (form && submitButton) { 
        form.addEventListener('submit', async (event) => {
            event.preventDefault(); 
            console.log("AJAX Form submit event triggered.");
            resetFeedbackMessages(); 
            if (!validateForm()) { console.error("Validación del formulario falló."); return; }
            
            const cleanFormData = getCleanFormData(); 
            // Aquí podrías agregar animación de progreso si lo deseas
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando...'; 
            try {
                const response = await fetch(form.action, { method: 'POST', body: cleanFormData });
                if (!response.ok) { showError("Error del servidor al generar el PDF."); return; }
                const data = await response.json();
                if (data.error || !data.success || !data.pdf_filename ) { showError(data.error || "Error inesperado al generar el PDF."); return; }
                
                // --- REDIRIGIR A PÁGINA DE ÉXITO ---
                if (data.report_id) {
                    window.location.href = `/report_success/${data.report_id}?pdf_filename=${encodeURIComponent(data.pdf_filename)}`;
                } else {
                    const downloadUrl = `/download_pdf/${data.pdf_filename}`; 
                    showToast(`PDF: ${data.pdf_filename.split('/').pop()}`, 'success', downloadUrl, `Descargar`);
                }
            } catch (error) { 
                showError("Error de red o del servidor: " + error.message);
            } 
            finally { 
                // No rehabilitar el botón aquí si vamos a redirigir
                // Se habilitará al volver a la página del formulario
                // Si no hay redirección (ej. error), SÍ rehabilitar:
                // if (submitButton && !window.location.pathname.includes('/report_success/')) {
                //     submitButton.disabled = false; 
                //     submitButton.innerHTML = '<i class="bi bi-file-earmark-pdf me-2"></i>Generar Reporte PDF'; 
                // }
                console.log("Bloque finally del submit ejecutado."); 
            }
        });
    } else { 
        console.error("Formulario #report-form o botón #submit-button no encontrado."); 
    }

}); // Fin de DOMContentLoaded
// --- FIN DEL ARCHIVO script.js ---