document.addEventListener('DOMContentLoaded', function() {
    // --- Obtener Elementos del DOM ---
    const form = document.getElementById('report-form');
    const fileInput = document.getElementById('file-upload');
    const submitButton = document.getElementById('submit-button'); 
    
    const logEntriesContainer = document.getElementById('daily-log-entries');
    const addRowButton = document.getElementById('add-log-row');
    const previousHoursInput = document.getElementById('previous_hours'); 

    // Elementos para feedback (barra de progreso, errores, éxito)
    const loadingProgressArea = document.getElementById('loading-progress-area');
    const progressBar = document.getElementById('progress-bar');
    const progressStageText = document.getElementById('progress-stage-text');
    const errorMessageDiv = document.getElementById('error-message'); // Busca el ID
    
    // Crear dinámicamente el div de éxito para insertarlo antes del de error
    const successMessageDiv = document.createElement('div'); 
    successMessageDiv.id = 'success-message'; // Asignar ID por si acaso
    successMessageDiv.style.display = 'none'; // Oculto inicialmente
    // Insertar ANTES del div de error, SI el div de error existe
    if (errorMessageDiv && errorMessageDiv.parentNode) {
        errorMessageDiv.parentNode.insertBefore(successMessageDiv, errorMessageDiv); 
    } else if (form && form.parentNode) {
        // Si no hay div de error, insertar después del formulario como fallback
        form.parentNode.insertBefore(successMessageDiv, form.nextSibling);
    } else {
        console.error("No se pudo encontrar un lugar para insertar el div de mensajes de éxito.");
    }


    // Consola Hollywood (opcional)
    const hollywoodConsoleDiv = document.getElementById('hollywood-console');
    const consoleOutputPre = document.getElementById('console-output');
    
    let progressIntervalId = null; 

    // --- Funcionalidad 1: Guardar/Cargar Horas Acumuladas ---
    function saveLastAccumulatedHours(hours) {
         try { 
             // Convertir a número y luego a string con 1 decimal
             const hoursFloat = parseFloat(hours);
             if (!isNaN(hoursFloat)) {
                 localStorage.setItem('socialServiceLastAccumulatedHours', hoursFloat.toFixed(1)); 
             }
         }
         catch (e) { console.warn("No se pudo guardar horas acumuladas en localStorage:", e); }
    }
    // Cargar horas previas al inicio
    if (previousHoursInput && !previousHoursInput.value) { 
        previousHoursInput.value = localStorage.getItem('socialServiceLastAccumulatedHours') || '0';
    }
    // -----------------------------------------------------------------------

    // --- Funcionalidad 2: Añadir/Eliminar Filas de Horas ---
    function addRemoveListener(button) { /* ...código sin cambios... */ 
        button.addEventListener('click', function() {
            const currentRows = logEntriesContainer.querySelectorAll('.daily-log-row');
            if (currentRows.length > 1) {
                button.closest('.daily-log-row').remove();
                updateTotalHours(); checkFirstRowRemoveButtonVisibility(); 
            } else {
                button.closest('.daily-log-row').querySelectorAll('input[type="date"], input[type="time"]').forEach(input => input.value = '');
                updateTotalHours(); 
                alert("Debe haber al menos una fila para el registro de horas.");
            }
        });
    }
    function checkFirstRowRemoveButtonVisibility() { /* ...código sin cambios... */ 
        if (!logEntriesContainer) return;
        const firstRemoveButton = logEntriesContainer.querySelector('.daily-log-row:first-child .remove-log-row');
        if(firstRemoveButton) firstRemoveButton.style.display = logEntriesContainer.querySelectorAll('.daily-log-row').length > 1 ? 'inline-block' : 'none';
    }
    if (addRowButton && logEntriesContainer) {
        addRowButton.addEventListener('click', function() { /* ...código sin cambios... */ 
            const templateRow = logEntriesContainer.querySelector('.daily-log-row:first-child'); 
            if (!templateRow) return; 
            const newRow = templateRow.cloneNode(true);
            newRow.querySelectorAll('input').forEach(input => { input.value = ''; input.classList.remove('is-invalid'); }); // Limpiar y quitar validación
            const removeButton = newRow.querySelector('.remove-log-row');
            if (removeButton) { removeButton.style.display = 'inline-block'; addRemoveListener(removeButton); }
            logEntriesContainer.appendChild(newRow);
            addRealtimeCalculationListeners(newRow); 
            checkFirstRowRemoveButtonVisibility(); 
        });
        logEntriesContainer.querySelectorAll('.daily-log-row').forEach((row) => { /* ...código sin cambios... */ 
            const removeButton = row.querySelector('.remove-log-row');
            if (removeButton) addRemoveListener(removeButton);
            addRealtimeCalculationListeners(row);
        });
        checkFirstRowRemoveButtonVisibility(); 
    }
    // -----------------------------------------------------------------

    // --- Funcionalidad 3: Cálculo de Horas en Tiempo Real ---
    let totalHoursDisplaySpan = document.getElementById('total-hours-display'); 
    if (!totalHoursDisplaySpan && addRowButton) { /* ...código sin cambios para crear el span... */ 
        totalHoursDisplaySpan = document.createElement('span');
        totalHoursDisplaySpan.id = 'total-hours-display';
        totalHoursDisplaySpan.classList.add('ms-md-3', 'fw-bold', 'fs-5', 'align-self-center', 'text-primary');
        const totalHoursLabel = document.createElement('span');
        totalHoursLabel.textContent = 'Total Horas del Mes: ';
        totalHoursLabel.classList.add('align-self-center', 'me-1');
        const containerForTotals = document.createElement('div');
        containerForTotals.classList.add('mt-3', 'd-flex', 'justify-content-end', 'align-items-center'); 
        containerForTotals.appendChild(totalHoursLabel);
        containerForTotals.appendChild(totalHoursDisplaySpan);
        addRowButton.parentNode.insertBefore(containerForTotals, addRowButton);
    }
    function calculateHoursForRow(row) { /* ...código sin cambios... */ 
         const startTimeInput = row.querySelector('input[name="log_start_time[]"]');
         const endTimeInput = row.querySelector('input[name="log_end_time[]"]');
         let hoursToday = 0;
         if (startTimeInput && endTimeInput && startTimeInput.value && endTimeInput.value) {
             const start = startTimeInput.value; const end = endTimeInput.value;
             try {
                  const startDate = new Date(`1970-01-01T${start}:00Z`); 
                  const endDate = new Date(`1970-01-01T${end}:00Z`);
                  let duration = endDate.getTime() - startDate.getTime(); 
                  if (duration < 0) { duration += 24 * 60 * 60 * 1000; }
                  hoursToday = Math.round((duration / (60 * 60 * 1000)) * 10) / 10; 
             } catch(e) { console.error("Error calculando horas:", e); hoursToday = 0; }
         }
         return hoursToday >= 0 ? hoursToday : 0;
    }
    function updateTotalHours() { /* ...código sin cambios... */ 
        let totalMonthHours = 0;
        if(logEntriesContainer){
              logEntriesContainer.querySelectorAll('.daily-log-row').forEach(row => {
                 totalMonthHours += calculateHoursForRow(row);
             });
        }
        if(totalHoursDisplaySpan) { totalHoursDisplaySpan.textContent = totalMonthHours.toFixed(1); }
    }
    function addRealtimeCalculationListeners(row) { /* ...código sin cambios... */ 
        const inputs = row.querySelectorAll('input[name="log_start_time[]"], input[name="log_end_time[]"], input[name="log_date[]"]');
        inputs.forEach(input => {
            input.addEventListener('change', updateTotalHours); 
            input.addEventListener('input', updateTotalHours); 
        });
    }
    if(form) updateTotalHours(); // Calcular total inicial al cargar (si hay datos precargados)
    // -----------------------------------------------------------------------

    // --- Funcionalidad 4: Envío del Formulario con AJAX ---
    if (form) { // Asegurarse que el formulario existe antes de añadir listener
        form.addEventListener('submit', async (event) => {
            console.log("AJAX Form submit event triggered."); // LOG 1
            event.preventDefault(); 
            console.log("preventDefault() llamado."); // LOG 2
            
            resetFeedbackMessages(); // <-- Llamada donde ocurría el error

            if (!validateForm()) { 
                 console.error("Validación del formulario falló."); // LOG 3a
                showError("Por favor, completa todos los campos requeridos y asegúrate de que las horas sean válidas.");
                return;
            }
             console.log("Validación del formulario OK."); // LOG 3b


            const cleanFormData = getCleanFormData(); 
            console.log("FormData limpio preparado."); // LOG 4

            startLoadingAnimationWithStages(); // Iniciar animación
             if(submitButton) {
                 submitButton.disabled = true;
                 submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Generando PDF...'; 
             }


            try {
                console.log("Intentando fetch a /generate..."); // LOG 5
                const response = await fetch('/generate', { 
                    method: 'POST',
                    body: cleanFormData, 
                });
                console.log("Respuesta de fetch recibida, status:", response.status); // LOG 6

                if (!response.ok) {
                    let errorMsg = `Error del servidor: ${response.status}`;
                    try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } 
                    catch (e) { console.warn("No se pudo parsear error JSON del backend:", e); }
                    throw new Error(errorMsg);
                }

                const data = await response.json();
                if (data.error || !data.success || !data.pdf_filename) {
                    throw new Error(data.error || "Respuesta inválida del servidor al generar PDF.");
                }
                
                await completeProgressAnimation("¡PDF Generado!");
                
                setTimeout(() => { 
                    if(loadingProgressArea) loadingProgressArea.style.display = 'none';
                    if (hollywoodConsoleDiv) {
                         hollywoodConsoleDiv.classList.remove('hollywood-console-visible');
                         hollywoodConsoleDiv.classList.add('hollywood-console-hidden');
                    }
                    
                    const downloadUrl = `/download_pdf/${data.pdf_filename}`; // Ruta correcta ahora
                    showSuccessMessage(
                        `Reporte PDF generado con éxito.`,
                        downloadUrl, 
                        `Descargar ${data.pdf_filename.split('/').pop()}` // Solo el nombre
                    );

                     const currentTotalHours = parseFloat(totalHoursDisplaySpan ? totalHoursDisplaySpan.textContent : 0);
                     const currentPreviousHours = parseFloat(previousHoursInput ? previousHoursInput.value : 0);
                     const newAccumulated = currentPreviousHours + currentTotalHours;
                     saveLastAccumulatedHours(newAccumulated);
                     // Opcional: actualizar campo de horas previas para la siguiente vez
                     // if(previousHoursInput) previousHoursInput.value = newAccumulated.toFixed(1);

                }, 500);


            } catch (error) {
                if (progressIntervalId) clearInterval(progressIntervalId);
                // Asegurarse de llamar updateProgressBar solo si progressBar existe
                if(progressBar) updateProgressBar(100, `Error`, true); 
                showError(`Error al generar reporte: ${error.message}`);
                console.error('Error en la generación o subida:', error);
            } finally {
                 if(submitButton) {
                      submitButton.disabled = false; 
                      submitButton.innerHTML = '<i class="bi bi-file-earmark-pdf me-2"></i>Generar Reporte PDF'; 
                 }
            }
        });
    } else {
        console.error("Elemento del formulario 'report-form' no encontrado.");
    }

    // --- Funciones de Ayuda ---

    // Función para limpiar FormData
    function getCleanFormData() {
        const cleanFormData = new FormData();
        let entryIndex = 0;
        const logDates = form.querySelectorAll('input[name="log_date[]"]');
        const logStarts = form.querySelectorAll('input[name="log_start_time[]"]');
        const logEnds = form.querySelectorAll('input[name="log_end_time[]"]');

        logDates.forEach((dateInput, index) => {
            if (dateInput.value && logStarts[index] && logEnds[index] && logStarts[index].value && logEnds[index].value) { // Incluir solo filas COMPLETAS
                cleanFormData.append('log_date[]', dateInput.value);
                cleanFormData.append('log_start_time[]', logStarts[index].value);
                cleanFormData.append('log_end_time[]', logEnds[index].value);
                entryIndex++;
            }
        });
        for (let [key, value] of new FormData(form).entries()) {
            if (!key.startsWith('log_')) { 
                if (!cleanFormData.has(key)) { cleanFormData.append(key, value); }
            }
        }
        console.log("FormData limpiado para envío:", Object.fromEntries(cleanFormData)); // Log para ver qué se envía
        return cleanFormData;
    }
    
    // Función de validación (como antes, con verificación de horas)
    function validateForm() {
        let isValid = true;
        // Limpiar validación previa
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

        // Validar campos requeridos básicos
        form.querySelectorAll('input[required]:not([type="file"]), textarea[required]').forEach(input => {
            if (!input.value.trim()) {
                // Validar requeridos explícitos
                 input.classList.add('is-invalid'); 
                 isValid = false;
            }
        });

         // Validar filas de horas
         const dateInputs = logEntriesContainer ? logEntriesContainer.querySelectorAll('input[name="log_date[]"]') : [];
         let hasAtLeastOneCompleteRow = false;
         let firstIncompleteRow = null;

         dateInputs.forEach((dateInput, index) => {
             const row = dateInput.closest('.daily-log-row');
             if(!row) return;
             const startInput = row.querySelector('input[name="log_start_time[]"]');
             const endInput = row.querySelector('input[name="log_end_time[]"]');
             
             // Marcar error si una fila está parcialmente llena
             const dateFilled = dateInput.value;
             const startFilled = startInput && startInput.value;
             const endFilled = endInput && endInput.value;

             if(dateFilled || startFilled || endFilled) { // Si algo está lleno en la fila
                 if(!(dateFilled && startFilled && endFilled)) { // Pero no todo
                      isValid = false;
                      if (!firstIncompleteRow) firstIncompleteRow = row; // Marcar la primera incompleta
                      if(!dateFilled) dateInput.classList.add('is-invalid');
                      if(!startFilled && startInput) startInput.classList.add('is-invalid');
                      if(!endFilled && endInput) endInput.classList.add('is-invalid');
                 } else {
                      hasAtLeastOneCompleteRow = true; // Fila completa encontrada
                      // Podríamos validar aquí si start < end si quisiéramos
                 }
             }
         });

        // Si no hay ninguna fila completa (y hay filas en el form)
        if (!hasAtLeastOneCompleteRow && dateInputs.length > 0) {
             isValid = false;
             // Si no marcamos una fila incompleta antes, marcamos la primera
             if(!firstIncompleteRow && dateInputs[0]) {
                 dateInputs[0].classList.add('is-invalid');
                 const firstRow = dateInputs[0].closest('.daily-log-row');
                 if(firstRow) {
                     const si = firstRow.querySelector('input[name="log_start_time[]"]');
                     const ei = firstRow.querySelector('input[name="log_end_time[]"]');
                     if(si && !si.value) si.classList.add('is-invalid');
                     if(ei && !ei.value) ei.classList.add('is-invalid');
                 }
             }
             // Mostrar mensaje general si la validación falló y no se mostró antes
             if (!isValid && errorMessageDiv.style.display === 'none') {
                 showError("Debes registrar al menos un día completo (Fecha, Hora Entrada, Hora Salida) y completar todas las filas iniciadas.");
             }
        }
        
        if(!isValid && !firstIncompleteRow && !errorMessageDiv.textContent) {
             showError("Por favor, revisa los campos marcados en rojo.");
        }

        return isValid;
    }

    // Función para limpiar mensajes
    function resetFeedbackMessages() {
        // Añadir guardas: verificar si los elementos existen ANTES de usarlos
        if(errorMessageDiv) {
            errorMessageDiv.style.display = 'none';
            errorMessageDiv.textContent = '';
            errorMessageDiv.classList.remove('alert-danger', 'alert-success'); // Limpiar clases
        }
         if(successMessageDiv) {
            successMessageDiv.style.display = 'none';
            successMessageDiv.textContent = '';
             successMessageDiv.classList.remove('alert-danger', 'alert-success'); // Limpiar clases
        }
    }
     
    // Función para mostrar mensajes de éxito
    function showSuccessMessage(message, downloadUrl = null, downloadText = null) {
        resetFeedbackMessages(); 
        if (!successMessageDiv) return; // Salir si el div no existe

        successMessageDiv.innerHTML = ''; 
        successMessageDiv.classList.add('alert', 'alert-success'); 
        const p = document.createElement('p');
        p.classList.add('mb-0'); 
        p.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>${message}`; 
        successMessageDiv.appendChild(p);
        if(downloadUrl && downloadText) {
            const downloadLink = document.createElement('a');
            downloadLink.href = downloadUrl;
            downloadLink.setAttribute('download', downloadText); 
            downloadLink.innerText = downloadText;
            downloadLink.classList.add('btn', 'btn-sm', 'btn-outline-success', 'ms-2', 'fw-bold'); 
             p.appendChild(downloadLink); 
        }
        successMessageDiv.style.display = 'block';
    }

    // Función para mostrar errores
    function showError(message) {
        resetFeedbackMessages(); // Limpiar éxito primero
        if (!errorMessageDiv) return; // Salir si el div de error no existe

        if (progressIntervalId) clearInterval(progressIntervalId);
        // updateProgressBar(100, "Error", true); // La barra se ocultará ahora

        if(loadingProgressArea) loadingProgressArea.style.display = 'none'; 
        if (hollywoodConsoleDiv) {
            hollywoodConsoleDiv.classList.remove('hollywood-console-visible');
            hollywoodConsoleDiv.classList.add('hollywood-console-hidden');
        }

        errorMessageDiv.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i>${message}`;
        errorMessageDiv.classList.add('alert', 'alert-danger');
        errorMessageDiv.style.display = 'block';
        // No necesariamente ocultar resultsArea, puede ser útil ver la imagen subida
        if(similarProductsDisplay) similarProductsDisplay.style.display = 'none'; 
    }

    // --- Funciones para la Barra de Progreso y Logs (COMPLETAS) ---
    const progressStages = [
        { percent: 10, text: "Validando datos...", consoleMsg: "FORM DATA VALIDATION..." },
        { percent: 25, text: "Enviando a servidor...", consoleMsg: "TRANSMITTING DATA TO FLASK BACKEND..." },
        { percent: 50, text: "Generando estructura PDF...", consoleMsg: "RENDERING REPORT TEMPLATE (HTML/CSS)..." },
        { percent: 80, text: "Convirtiendo a PDF (WeasyPrint)...", consoleMsg: "CONVERTING TO PDF DOCUMENT (WEASYPRINT ENGINE)..." },
        { percent: 95, text: "Preparando descarga...", consoleMsg: "PREPARING DOWNLOAD LINK..." },
    ];
    currentStageIndex = 0; 

    function startLoadingAnimationWithStages() {
        resetFeedbackMessages();
        if(loadingProgressArea) loadingProgressArea.style.display = 'block';
        if (hollywoodConsoleDiv && consoleOutputPre) {
            hollywoodConsoleDiv.classList.remove('hollywood-console-hidden');
            hollywoodConsoleDiv.classList.add('hollywood-console-visible');
            consoleOutputPre.textContent = ''; 
        }
        
        currentStageIndex = 0;
        updateProgressBar(0, "Iniciando generación...");
        logToHollywoodConsole("> INITIATING REPORT GENERATION PIPELINE...");

        if (progressIntervalId) clearInterval(progressIntervalId);

        const totalAnimationTime = 4000; 
        const intervalTime = totalAnimationTime / progressStages.length;

        progressIntervalId = setInterval(() => {
            if (currentStageIndex < progressStages.length) {
                const stage = progressStages[currentStageIndex];
                updateProgressBar(stage.percent, stage.text);
                logToHollywoodConsole(stage.consoleMsg);
                currentStageIndex++;
            } else {
                clearInterval(progressIntervalId);
                progressIntervalId = null; 
                updateProgressBar(99, "Finalizando..."); 
            }
        }, intervalTime); 
    }

    function updateProgressBar(percent, text, isError = false) { 
        if (!progressBar || !progressStageText) return; 
        const p = Math.min(100, Math.max(0, percent)); 
        progressBar.style.width = p + '%';
        progressBar.setAttribute('aria-valuenow', p);
        progressBar.textContent = `${p}%`; 
        if (text) progressStageText.textContent = text; 
        progressBar.classList.remove('bg-success', 'bg-danger', 'bg-primary', 'progress-bar-animated', 'text-dark');
        if (isError) { progressBar.classList.add('bg-danger'); progressBar.textContent = `Error`; }
        else if (p >= 100) { progressBar.classList.add('bg-success'); progressBar.textContent = `¡Completado!`; }
        else if (p > 0) { progressBar.classList.add('bg-primary', 'progress-bar-animated'); } 
        else { progressBar.classList.add('bg-primary'); progressBar.textContent = '0%'; }
    }
    
    function logToHollywoodConsole(message) {
        if (hollywoodConsoleDiv && hollywoodConsoleDiv.classList.contains('hollywood-console-visible') && consoleOutputPre) {
            const timestamp = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
            consoleOutputPre.textContent += `[${timestamp}] ${message}\n`;
            hollywoodConsoleDiv.scrollTop = hollywoodConsoleDiv.scrollHeight;
        }
    }

    async function completeProgressAnimation(finalMessage) { 
         if (progressIntervalId) { clearInterval(progressIntervalId); progressIntervalId = null; }
         let currentPercent = 0;
         if(progressBar) currentPercent = parseInt(progressBar.style.width.replace('%','')) || 0;
         
         while(currentStageIndex < progressStages.length) {
             const stage = progressStages[currentStageIndex];
             if(stage.percent > currentPercent) {
                 updateProgressBar(stage.percent, stage.text); logToHollywoodConsole(stage.consoleMsg);
                 await new Promise(resolve => setTimeout(resolve, 200)); 
             }
             currentStageIndex++;
         }
         if(currentPercent < 99) {
              updateProgressBar(99, "Compilando PDF final..."); logToHollywoodConsole("COMPILING FINAL PDF...");
              await new Promise(resolve => setTimeout(resolve, 300)); 
         }
         updateProgressBar(100, finalMessage, false); 
         logToHollywoodConsole("PROCESS COMPLETE. PDF READY.");
    }

}); // Fin de DOMContentLoaded