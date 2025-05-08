// static/js/script.js (COMPLETO - Versión Final Sprint DB+History+UI+AJAX)
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
    const demoDataButton = document.getElementById('fill-demo-data'); // Botón Demo

    // Elementos para feedback
    const loadingProgressArea = document.getElementById('loading-progress-area');
    const progressBar = document.getElementById('progress-bar');
    const progressStageText = document.getElementById('progress-stage-text');
    const errorMessageDiv = document.getElementById('error-message'); 
    // Crear div de éxito dinámicamente y añadirlo al DOM
    let successMessageDiv = document.getElementById('success-message');
    if (!successMessageDiv) {
        successMessageDiv = document.createElement('div'); 
        successMessageDiv.id = 'success-message';
        successMessageDiv.style.display = 'none';
        // Intentar insertar antes del div de error o después del área de progreso
        const insertTarget = errorMessageDiv || loadingProgressArea;
        if (insertTarget && insertTarget.parentNode) {
            insertTarget.parentNode.insertBefore(successMessageDiv, insertTarget); 
        } else if (form && form.parentNode) {
            form.parentNode.insertBefore(successMessageDiv, form.nextSibling); // Fallback
        }
    }
    
    const hollywoodConsoleDiv = document.getElementById('hollywood-console');
    const consoleOutputPre = document.getElementById('console-output');
    
    let progressIntervalId = null; 
    let totalHoursDisplaySpan = document.getElementById('total-hours-display'); 

    // --- Crear Span para Total Horas si no existe ---
    if (!totalHoursDisplaySpan && addRowButton && addRowButton.parentNode) { 
        totalHoursDisplaySpan = document.createElement('span'); /* ... */ 
        totalHoursDisplaySpan.id = 'total-hours-display';
        totalHoursDisplaySpan.classList.add('ms-md-3', 'fw-bold', 'fs-5', 'align-self-center', 'text-primary');
        const totalHoursLabel = document.createElement('span'); /* ... */
        totalHoursLabel.textContent = 'Total Horas del Mes Calculadas: '; 
        totalHoursLabel.classList.add('align-self-center', 'me-1');
        const containerForTotals = document.createElement('div'); /* ... */
        containerForTotals.id = 'total-hours-live-container'; 
        containerForTotals.classList.add('mt-3', 'd-flex', 'justify-content-end', 'align-items-center'); 
        containerForTotals.appendChild(totalHoursLabel);
        containerForTotals.appendChild(totalHoursDisplaySpan);
        addRowButton.parentNode.insertBefore(containerForTotals, addRowButton);
    }
    
    // --- Funcionalidad 1: Horas Acumuladas ---
    function saveLastAccumulatedHours(hours) { /* ...código como antes... */ }
    if (previousHoursInput && (!previousHoursInput.value || previousHoursInput.value === '0')) { 
        previousHoursInput.value = localStorage.getItem('socialServiceLastAccumulatedHours') || '0';
    }

    // --- Funcionalidad 2: Añadir/Eliminar Filas ---
    function addRemoveListener(button) { /* ...código como antes... */ }
    function checkFirstRowRemoveButtonVisibility() { /* ...código como antes... */ }
    if (addRowButton && logEntriesContainer) { /* ...código como antes... */ }
    
    // --- Funcionalidad 3: Cálculo Horas Tiempo Real ---
    function calculateHoursForRow(row) { /* ...código como antes... */ }
    function updateTotalHours() { /* ...código como antes... */ }
    function addRealtimeCalculationListeners(row) { /* ...código como antes... */ }
    if (form) updateTotalHours(); 

    // --- Funcionalidad 4: Generar Descripción Sugerida ---
    if (generateDescButton && activitiesTextarea && activityTypesContainer) { /* ...código como antes... */ }
    function generateSuggestedDescription() { /* ...código como antes... */ }
    
    // --- Funcionalidad 5: Rellenar con Datos de Demo ---
    if (demoDataButton) { /* ...código como antes... */ }
    function fillWithDemoData() { /* ...código como antes... */ }
    function setInputValue(id, value) { /* ...código como antes... */ }
    function setInputValueIfEmpty(id, value) { /* ...código como antes... */ }
    function formatDate(date) { /* ...código como antes... */ }
    function formatTime(h, m) { /* ...código como antes... */ }
    function fillDemoHours(startDate, endDate) { /* ...código como antes... */ }

    // --- Funcionalidad 6: Envío Formulario AJAX ---
    if (form && submitButton) { 
        form.addEventListener('submit', async (event) => {
            event.preventDefault(); // <-- PRIMERA LÍNEA IMPORTANTE
            console.log("AJAX Form submit event triggered."); 
            
            resetFeedbackMessages(); 

            if (!validateForm()) { 
                console.error("Validación del formulario falló.");
                // showError ya muestra el mensaje en la UI
                return; 
            }
            console.log("Validación del formulario OK.");

            const cleanFormData = getCleanFormData(); 
            console.log("FormData limpio preparado.");

            startLoadingAnimationWithStages(); 
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Generando PDF...'; 

            try {
                console.log("Intentando fetch a /generate..."); 
                const response = await fetch('/generate', { 
                    method: 'POST',
                    body: cleanFormData, 
                });
                console.log("Respuesta de fetch recibida, status:", response.status); 

                if (!response.ok) {
                    let errorMsg = `Error del servidor: ${response.status}`;
                    try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } 
                    catch (e) { console.warn("No se pudo parsear error JSON del backend:", e); }
                    throw new Error(errorMsg);
                }

                const data = await response.json();
                console.log("Datos JSON recibidos:", data); // Log para ver la respuesta

                if (data.error || !data.success || !data.pdf_filename) {
                    throw new Error(data.error || "Respuesta inválida del servidor al generar PDF.");
                }
                
                // Si llegamos aquí, la respuesta fue exitosa y contiene el nombre del PDF
                await completeProgressAnimation("¡PDF Generado!");
                
                setTimeout(() => { 
                    if(loadingProgressArea) loadingProgressArea.style.display = 'none';
                    if (hollywoodConsoleDiv) {
                        hollywoodConsoleDiv.classList.remove('hollywood-console-visible');
                        hollywoodConsoleDiv.classList.add('hollywood-console-hidden');
                    }
                    
                    // Construir URL de descarga correctamente
                    // pdf_filename viene como "temp_pdf/nombre_archivo.pdf"
                    const downloadUrl = `/download_pdf/${data.pdf_filename}`; // La ruta Flask espera esto
                    console.log("Construyendo enlace de descarga para:", downloadUrl); // Log
                    
                    showSuccessMessage(
                        `Reporte PDF generado con éxito.`,
                        downloadUrl, 
                        `Descargar ${data.pdf_filename.split('/').pop()}` // Mostrar solo el nombre
                    );
                    console.log("showSuccessMessage llamado."); // Log

                    // Guardar horas acumuladas
                    const currentTotalHours = parseFloat(totalHoursDisplaySpan ? totalHoursDisplaySpan.textContent : 0);
                    const currentPreviousHours = parseFloat(previousHoursInput ? previousHoursInput.value : 0);
                    const newAccumulated = currentPreviousHours + currentTotalHours;
                    saveLastAccumulatedHours(newAccumulated);
                    console.log("Horas acumuladas guardadas:", newAccumulated); // Log

                }, 500); // Pequeña pausa antes de mostrar el éxito


            } catch (error) {
                console.error('Error en bloque try/catch del fetch:', error); // Log del error
                if (progressIntervalId) clearInterval(progressIntervalId);
                if(progressBar) updateProgressBar(100, `Error`, true); 
                showError(`Error al generar reporte: ${error.message}`);
            } finally {
                 if(submitButton) {
                      submitButton.disabled = false; 
                      submitButton.innerHTML = '<i class="bi bi-file-earmark-pdf me-2"></i>Generar Reporte PDF'; 
                 }
                 console.log("Bloque finally ejecutado."); // Log
            }
        });
    } else { console.error("Formulario #report-form o botón #submit-button no encontrado."); }
    
    // --- Funciones de Ayuda COMPLETAS ---
    const progressStages = [ { percent: 10, text: "Validando datos...", consoleMsg: "FORM DATA VALIDATION..." }, { percent: 25, text: "Enviando a servidor...", consoleMsg: "TRANSMITTING DATA TO FLASK BACKEND..." }, { percent: 50, text: "Generando estructura PDF...", consoleMsg: "RENDERING REPORT TEMPLATE (HTML/CSS)..." }, { percent: 80, text: "Convirtiendo a PDF (WeasyPrint)...", consoleMsg: "CONVERTING TO PDF DOCUMENT (WEASYPRINT ENGINE)..." }, { percent: 95, text: "Preparando descarga...", consoleMsg: "PREPARING DOWNLOAD LINK..." }, ];
    let currentStageIndex = 0; 
    function startLoadingAnimationWithStages() { resetFeedbackMessages(); if(loadingProgressArea) loadingProgressArea.style.display = 'block'; if (hollywoodConsoleDiv && consoleOutputPre) { hollywoodConsoleDiv.classList.remove('hollywood-console-hidden'); hollywoodConsoleDiv.classList.add('hollywood-console-visible'); consoleOutputPre.textContent = ''; } currentStageIndex = 0; updateProgressBar(0, "Iniciando generación..."); logToHollywoodConsole("> INITIATING REPORT GENERATION PIPELINE..."); if (progressIntervalId) clearInterval(progressIntervalId); const totalAnimationTime = 4000; const intervalTime = totalAnimationTime / progressStages.length; progressIntervalId = setInterval(() => { if (currentStageIndex < progressStages.length) { const stage = progressStages[currentStageIndex]; updateProgressBar(stage.percent, stage.text); logToHollywoodConsole(stage.consoleMsg); currentStageIndex++; } else { clearInterval(progressIntervalId); progressIntervalId = null; updateProgressBar(99, "Finalizando..."); } }, intervalTime); }
    function updateProgressBar(percent, text, isError = false) { if (!progressBar || !progressStageText) return; const p = Math.min(100, Math.max(0, percent)); progressBar.style.width = p + '%'; progressBar.setAttribute('aria-valuenow', p); let barText = `${p}%`; if (text && p < 100 && !isError) { progressStageText.textContent = text; } else if (text) { progressBar.textContent = text; progressStageText.textContent = text; } else { progressBar.textContent = barText; } progressBar.classList.remove('bg-success', 'bg-danger', 'bg-primary', 'progress-bar-animated', 'text-dark'); if (isError) { progressBar.classList.add('bg-danger'); progressBar.textContent = `Error`; } else if (p >= 100) { progressBar.classList.add('bg-success'); progressBar.textContent = `¡Completado!`; } else if (p > 0) { progressBar.classList.add('bg-primary', 'progress-bar-animated'); } else { progressBar.classList.add('bg-primary'); progressBar.textContent = '0%'; }}
    function logToHollywoodConsole(message) { if (hollywoodConsoleDiv && hollywoodConsoleDiv.classList.contains('hollywood-console-visible') && consoleOutputPre) { const timestamp = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }); consoleOutputPre.textContent += `[${timestamp}] ${message}\n`; hollywoodConsoleDiv.scrollTop = hollywoodConsoleDiv.scrollHeight; }}
    async function completeProgressAnimation(finalMessage) { if (progressIntervalId) { clearInterval(progressIntervalId); progressIntervalId = null; } let currentPercent = 0; if(progressBar) currentPercent = parseInt(progressBar.style.width.replace('%','')) || 0; while(currentStageIndex < progressStages.length) { const stage = progressStages[currentStageIndex]; if(stage.percent > currentPercent) { updateProgressBar(stage.percent, stage.text); logToHollywoodConsole(stage.consoleMsg); await new Promise(resolve => setTimeout(resolve, 200)); } currentStageIndex++; } if(currentPercent < 99) { updateProgressBar(99, "Compilando PDF final..."); logToHollywoodConsole("COMPILING FINAL PDF..."); await new Promise(resolve => setTimeout(resolve, 300)); } updateProgressBar(100, finalMessage, false); logToHollywoodConsole("PROCESS COMPLETE. PDF READY."); }
    function validateForm() { /* ... código de validación completo como antes ... */ }
    function resetFeedbackMessages() { if(errorMessageDiv) { errorMessageDiv.style.display = 'none'; errorMessageDiv.textContent = ''; errorMessageDiv.classList.remove('alert-danger', 'alert-success'); } if(successMessageDiv) { successMessageDiv.style.display = 'none'; successMessageDiv.textContent = ''; successMessageDiv.classList.remove('alert-danger', 'alert-success'); }}
    function showSuccessMessage(message, downloadUrl = null, downloadText = null) { resetFeedbackMessages(); if (!successMessageDiv) return; successMessageDiv.innerHTML = ''; successMessageDiv.classList.add('alert', 'alert-success'); const p = document.createElement('p'); p.classList.add('mb-0'); p.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>${message}`; successMessageDiv.appendChild(p); if(downloadUrl && downloadText) { const dl = document.createElement('a'); dl.href = downloadUrl; dl.setAttribute('download', downloadText); dl.innerText = downloadText; dl.classList.add('btn', 'btn-sm', 'btn-outline-success', 'ms-2', 'fw-bold'); p.appendChild(dl); } successMessageDiv.style.display = 'block'; }
    function showError(message) { resetFeedbackMessages(); if (!errorMessageDiv) return; if (progressIntervalId) clearInterval(progressIntervalId); if(loadingProgressArea) loadingProgressArea.style.display = 'none'; if (hollywoodConsoleDiv) { hollywoodConsoleDiv.classList.remove('hollywood-console-visible'); hollywoodConsoleDiv.classList.add('hollywood-console-hidden'); } errorMessageDiv.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i>${message}`; errorMessageDiv.classList.add('alert', 'alert-danger'); errorMessageDiv.style.display = 'block'; if(similarProductsDisplay) similarProductsDisplay.style.display = 'none'; }
    function getCleanFormData() { /* ... código completo como antes ... */ }

}); // Fin de DOMContentLoaded