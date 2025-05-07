document.addEventListener('DOMContentLoaded', function() {
    // --- Obtener Elementos del DOM ---
    const form = document.getElementById('report-form');
    // const fileInput = document.getElementById('file-upload'); // No relevante para este proyecto
    const submitButton = document.getElementById('submit-button'); // Asumiendo ID del botón de submit final
    
    const logEntriesContainer = document.getElementById('daily-log-entries');
    const addRowButton = document.getElementById('add-log-row');

    // Elementos de datos de usuario/prestatario/autorizante 
    const studentNameInput = document.getElementById('student_name');
    const studentBoletaInput = document.getElementById('student_boleta');
    const studentProgramInput = document.getElementById('student_program');
    const studentSemesterInput = document.getElementById('student_semester');
    const studentEmailInput = document.getElementById('student_email');
    const studentPhoneInput = document.getElementById('student_phone');
    const prestatarioNameInput = document.getElementById('prestatario_name');
    const authorizingNameInput = document.getElementById('authorizing_name');
    const authorizingTitleInput = document.getElementById('authorizing_title');
    const previousHoursInput = document.getElementById('previous_hours'); 

    // Elementos para feedback (barra de progreso, errores)
    const loadingProgressArea = document.getElementById('loading-progress-area');
    const progressBar = document.getElementById('progress-bar');
    const progressStageText = document.getElementById('progress-stage-text');
    const errorMessageDiv = document.getElementById('error-message');
    
    // Consola Hollywood (opcional) - Asegúrate de que existan los IDs si la usas
    const hollywoodConsoleDiv = document.getElementById('hollywood-console');
    const consoleOutputPre = document.getElementById('console-output');
    
    let progressIntervalId = null; // ID para el intervalo de la animación

    // --- Funcionalidad 1: Guardar/Cargar Datos del Perfil en localStorage ---
    const profileKeys = [
        'student_name', 'student_boleta', 'student_program', 'student_semester', 
        'student_email', 'student_phone', 'prestatario_name', 
        'authorizing_name', 'authorizing_title'
        // 'previous_hours' // No guardar horas previas aquí, debe ser más dinámico
    ];

    function saveProfileData() {
        const profileData = {};
        profileKeys.forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                profileData[key] = element.value;
            }
        });
        localStorage.setItem('socialServiceProfile', JSON.stringify(profileData));
        console.log("Perfil guardado en localStorage.");
    }

    function loadProfileData() {
        const savedProfile = localStorage.getItem('socialServiceProfile');
        if (savedProfile) {
            console.log("Cargando perfil desde localStorage.");
            const profileData = JSON.parse(savedProfile);
            profileKeys.forEach(key => {
                const element = document.getElementById(key);
                 // Cargar solo si el elemento existe y hay dato guardado Y el campo está vacío (para no sobrescribir defaults del backend si es la primera vez)
                if (element && profileData[key] && !element.value) { 
                    element.value = profileData[key];
                } else if (element && !profileData[key] && element.defaultValue) {
                     // Si no hay dato guardado pero sí un valor por defecto del HTML, usar ese
                     element.value = element.defaultValue;
                }
            });
        } else {
            console.log("No se encontró perfil en localStorage. Usando valores por defecto si existen.");
             // Asegurar que los valores por defecto del HTML se usen si no hay nada guardado
             profileKeys.forEach(key => {
                const element = document.getElementById(key);
                 if (element && element.defaultValue) {
                     element.value = element.defaultValue;
                 }
             });
        }
        // Cargar horas previas podría venir de otro lado o dejarse en 0
        if (previousHoursInput && !previousHoursInput.value) {
             previousHoursInput.value = localStorage.getItem('socialServiceLastAccumulatedHours') || '0';
        }
    }

    // Cargar datos al iniciar la página
    loadProfileData();

    // Guardar datos cuando se modifican campos del perfil
    profileKeys.forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            element.addEventListener('change', saveProfileData);
            element.addEventListener('blur', saveProfileData); // Guardar también al perder foco
        }
    });
    
    // --- Funcionalidad 2: Añadir/Eliminar Filas de Horas Dinámicamente ---
    function addRemoveListener(button) {
        button.addEventListener('click', function() {
            const currentRows = logEntriesContainer.querySelectorAll('.daily-log-row');
            if (currentRows.length > 1) {
                button.closest('.daily-log-row').remove();
                updateTotalHours(); 
                checkFirstRowRemoveButtonVisibility(); // Re-evaluar visibilidad
            } else {
                button.closest('.daily-log-row').querySelectorAll('input[type="date"], input[type="time"]').forEach(input => input.value = '');
                updateTotalHours(); 
                alert("Debe haber al menos una fila para el registro de horas.");
            }
        });
    }

    function checkFirstRowRemoveButtonVisibility() {
         const firstRemoveButton = logEntriesContainer.querySelector('.daily-log-row:first-child .remove-log-row');
         if (firstRemoveButton) {
             firstRemoveButton.style.display = logEntriesContainer.querySelectorAll('.daily-log-row').length > 1 ? 'inline-block' : 'none';
         }
    }

    if (addRowButton && logEntriesContainer) {
        addRowButton.addEventListener('click', function() {
            const templateRow = logEntriesContainer.querySelector('.daily-log-row:first-child'); // Siempre clonar la primera
            if (!templateRow) return; 
            
            const newRow = templateRow.cloneNode(true);
            newRow.querySelectorAll('input').forEach(input => { input.value = ''; });
            
            const removeButton = newRow.querySelector('.remove-log-row');
            if (removeButton) {
                removeButton.style.display = 'inline-block'; // Siempre visible en filas nuevas
                addRemoveListener(removeButton); 
            }
            logEntriesContainer.appendChild(newRow);
            addRealtimeCalculationListeners(newRow); // Añadir listeners de cálculo a la nueva fila
            checkFirstRowRemoveButtonVisibility(); // Asegurarse que el botón de la primera fila aparezca si es necesario
        });

        logEntriesContainer.querySelectorAll('.daily-log-row').forEach((row) => {
            const removeButton = row.querySelector('.remove-log-row');
            if (removeButton) {
                addRemoveListener(removeButton);
            }
            addRealtimeCalculationListeners(row);
        });
        checkFirstRowRemoveButtonVisibility(); // Ajustar visibilidad inicial del botón de la primera fila
    }

    // --- Funcionalidad 3: Cálculo de Horas en Tiempo Real en el Formulario ---
    const totalHoursDisplaySpan = document.createElement('span');
    totalHoursDisplaySpan.id = 'total-hours-display';
    totalHoursDisplaySpan.classList.add('ms-md-3', 'fw-bold', 'fs-5', 'align-self-center'); // Estilos Bootstrap y alineación
    
    const totalHoursLabel = document.createElement('span');
    totalHoursLabel.textContent = 'Total Horas del Mes: ';
    totalHoursLabel.classList.add('align-self-center');

    if (addRowButton) {
        // Insertar después del contenedor de filas, antes del botón de añadir
        const parentDiv = addRowButton.parentNode;
        const containerForTotals = document.createElement('div');
        containerForTotals.classList.add('mt-3', 'd-flex', 'justify-content-end', 'align-items-center'); // Contenedor flex para alinear a la derecha
        containerForTotals.appendChild(totalHoursLabel);
        containerForTotals.appendChild(totalHoursDisplaySpan);
        parentDiv.insertBefore(containerForTotals, addRowButton);
        // addRowButton.parentNode.insertBefore(totalHoursDisplaySpan, addRowButton.nextSibling.nextSibling);
        // addRowButton.parentNode.insertBefore(totalHoursLabel, totalHoursDisplaySpan);
    }

    function calculateHoursForRow(row) {
        const startTimeInput = row.querySelector('input[name="log_start_time[]"]');
        const endTimeInput = row.querySelector('input[name="log_end_time[]"]');
        let hoursToday = 0;

        if (startTimeInput && endTimeInput && startTimeInput.value && endTimeInput.value) {
            const start = startTimeInput.value;
            const end = endTimeInput.value;
            try {
                 const startDate = new Date(`1970-01-01T${start}:00`);
                 const endDate = new Date(`1970-01-01T${end}:00`);
                 let duration = endDate - startDate; 

                 if (duration < 0) { 
                     duration += 24 * 60 * 60 * 1000; 
                 }
                 hoursToday = Math.round((duration / (60 * 60 * 1000)) * 10) / 10; 
            } catch(e) {
                console.error("Error calculando horas:", e);
                hoursToday = 0;
            }
        }
        return hoursToday >= 0 ? hoursToday : 0;
    }

    function updateTotalHours() {
        let totalMonthHours = 0;
        if(logEntriesContainer){
             logEntriesContainer.querySelectorAll('.daily-log-row').forEach(row => {
                totalMonthHours += calculateHoursForRow(row);
            });
        }
        if(totalHoursDisplaySpan) {
             totalHoursDisplaySpan.textContent = totalMonthHours.toFixed(1); 
        }
    }

    function addRealtimeCalculationListeners(row) {
        const inputs = row.querySelectorAll('input[name="log_start_time[]"], input[name="log_end_time[]"], input[name="log_date[]"]');
        inputs.forEach(input => {
            // Recalcular al cambiar hora o incluso fecha (por si acaso)
            input.addEventListener('change', updateTotalHours); 
            input.addEventListener('input', updateTotalHours); // También al escribir
        });
    }
    updateTotalHours(); // Calcular total inicial

    // --- Funcionalidad 4: Envío del Formulario con AJAX y Descarga de PDF ---
    
    form.addEventListener('submit', async (event) => {
        console.log("AJAX Form submit event triggered.");
        event.preventDefault(); 
        
        errorMessageDiv.style.display = 'none'; 
        
        saveProfileData(); // Guardar datos del perfil antes de enviar

        if (!validateForm()) { 
            showError("Por favor, completa todos los campos requeridos y asegúrate de que las horas sean válidas.");
            return;
        }

        const formData = new FormData(form); 
        
        // Limpiar filas vacías antes de enviar (donde no se llenó la fecha)
         const cleanFormData = new FormData();
         let entryIndex = 0;
         const logDates = form.querySelectorAll('input[name="log_date[]"]');
         const logStarts = form.querySelectorAll('input[name="log_start_time[]"]');
         const logEnds = form.querySelectorAll('input[name="log_end_time[]"]');

         logDates.forEach((dateInput, index) => {
             if (dateInput.value) { // Solo incluir si la fecha está llena
                 cleanFormData.append('log_date[]', dateInput.value);
                 if (logStarts[index]) cleanFormData.append('log_start_time[]', logStarts[index].value);
                 if (logEnds[index]) cleanFormData.append('log_end_time[]', logEnds[index].value);
                 entryIndex++;
             }
         });

         // Añadir el resto de los datos del formulario
         for (let [key, value] of new FormData(form).entries()) {
             if (!key.startsWith('log_')) { // Evitar duplicar los logs
                 // Si el campo permite múltiples valores (poco probable aquí), usar getAll
                 // Para campos simples, esto funciona.
                 if (!cleanFormData.has(key)) { // Añadir solo si no existe
                    cleanFormData.append(key, value);
                 }
             }
         }

        startLoadingAnimationWithStages(); 
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Generando...'; // Feedback en botón

        try {
            console.log("Intentando fetch a /generate..."); 
            const response = await fetch('/generate', { 
                method: 'POST',
                body: cleanFormData, // Usar los datos limpios
            });
            console.log("Respuesta de fetch recibida, status:", response.status);

            if (!response.ok) {
                let errorMsg = `Error del servidor: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.error || errorMsg;
                } catch (e) { console.warn("No se pudo parsear error JSON del backend:", e); }
                throw new Error(errorMsg);
            }

            const data = await response.json();
            if (data.error || !data.success || !data.pdf_filename) {
                throw new Error(data.error || "El servidor no devolvió un nombre de archivo PDF válido.");
            }
            
            await completeProgressAnimation("¡PDF Generado con éxito!");
            
            setTimeout(() => { 
                loadingProgressArea.style.display = 'none';
                if (hollywoodConsoleDiv) {
                     hollywoodConsoleDiv.classList.remove('hollywood-console-visible');
                     hollywoodConsoleDiv.classList.add('hollywood-console-hidden');
                }
                
                // Crear enlace de descarga dinámicamente
                const downloadUrl = `/download_pdf/${data.pdf_filename.split('/').pop()}`;
                showSuccessMessage(
                    `Reporte PDF generado con éxito.`,
                    downloadUrl, // Pasamos la URL al mensaje
                    `Descargar ${data.pdf_filename.split('/').pop()}` // Texto del botón
                );

                // Opcional: guardar las horas acumuladas para el próximo reporte
                 const lastAccumulated = parseFloat(previousHoursInput.value || 0) + parseFloat(totalHoursDisplaySpan.textContent || 0);
                 localStorage.setItem('socialServiceLastAccumulatedHours', lastAccumulated.toFixed(1));

            }, 500);


        } catch (error) {
            if (progressIntervalId) clearInterval(progressIntervalId);
            updateProgressBar(100, `Error`, true); 
            showError(`Error al generar reporte: ${error.message}`);
            console.error('Error en la generación o subida:', error);
        } finally {
             submitButton.disabled = false; 
             submitButton.innerHTML = '<i class="bi bi-eye me-2"></i>Generar Vista Previa del Reporte'; // Restaurar texto botón
             // No limpiar el formulario aquí, el usuario puede querer generar de nuevo o corregir
        }
    });

    // --- Funciones de Ayuda para la Barra de Progreso y Logs ---
    const progressStages = [
        { percent: 10, text: "Validando datos...", consoleMsg: "FORM DATA VALIDATION..." },
        { percent: 25, text: "Enviando a servidor...", consoleMsg: "TRANSMITTING DATA TO FLASK BACKEND..." },
        { percent: 50, text: "Generando estructura PDF...", consoleMsg: "RENDERING REPORT TEMPLATE (HTML/CSS)..." },
        { percent: 80, text: "Convirtiendo a PDF (WeasyPrint)...", consoleMsg: "CONVERTING TO PDF DOCUMENT (WEASYPRINT ENGINE)..." },
        { percent: 95, text: "Preparando descarga...", consoleMsg: "PREPARING DOWNLOAD LINK..." },
    ];
    let currentStageIndex = 0;

    function startLoadingAnimationWithStages() {
        loadingProgressArea.style.display = 'block';
        if (hollywoodConsoleDiv && consoleOutputPre) {
            hollywoodConsoleDiv.classList.remove('hollywood-console-hidden');
            hollywoodConsoleDiv.classList.add('hollywood-console-visible');
            consoleOutputPre.textContent = ''; 
        }
        
        currentStageIndex = 0;
        updateProgressBar(0, "Iniciando generación...");
        logToHollywoodConsole("> INITIATING REPORT GENERATION PIPELINE...");

        if (progressIntervalId) clearInterval(progressIntervalId);

        const totalAnimationTime = 4000; // Duración simulada (ajustar)
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
                updateProgressBar(99, "Finalizando..."); // Mostrar casi 100% mientras espera respuesta
            }
        }, intervalTime); 
    }

    function updateProgressBar(percent, text, isError = false) {
        if (!progressBar || !progressStageText) return; 

        const p = Math.min(100, Math.max(0, percent)); // Asegurar entre 0 y 100
        progressBar.style.width = p + '%';
        progressBar.setAttribute('aria-valuenow', p);
        progressBar.textContent = `${p}%`; // Solo porcentaje en la barra
        if (text) progressStageText.textContent = text; // Texto de etapa arriba

        progressBar.classList.remove('bg-success', 'bg-danger', 'bg-primary', 'progress-bar-animated', 'text-dark');
        if (isError) {
            progressBar.classList.add('bg-danger');
             progressBar.textContent = `Error`;
        } else if (p >= 100) {
            progressBar.classList.add('bg-success');
             progressBar.textContent = `¡Completado!`;
        } else if (p > 0) {
            progressBar.classList.add('bg-primary', 'progress-bar-animated');
        } else { // 0%
             progressBar.classList.add('bg-primary');
             progressBar.textContent = '0%'; 
        }
        // Añadir lógica para texto oscuro en fondos claros si usas bg-warning o bg-info
        // if (progressBar.classList.contains('bg-warning') || progressBar.classList.contains('bg-info')) {
        //     progressBar.classList.add('text-dark');
        // }
    }
    
    function logToHollywoodConsole(message) {
        if (hollywoodConsoleDiv && hollywoodConsoleDiv.classList.contains('hollywood-console-visible') && consoleOutputPre) {
            const timestamp = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
            consoleOutputPre.textContent += `[${timestamp}] ${message}\n`;
            hollywoodConsoleDiv.scrollTop = hollywoodConsoleDiv.scrollHeight;
        }
    }

    async function completeProgressAnimation(finalMessage) {
        if (progressIntervalId) {
            clearInterval(progressIntervalId);
            progressIntervalId = null;
        }
        
        let currentPercent = parseInt(progressBar.style.width.replace('%','')) || 0;
        
        // Asegurar que pase por las últimas etapas visualmente
        while(currentStageIndex < progressStages.length) {
            const stage = progressStages[currentStageIndex];
             if(stage.percent > currentPercent) {
                 updateProgressBar(stage.percent, stage.text);
                 logToHollywoodConsole(stage.consoleMsg);
                 await new Promise(resolve => setTimeout(resolve, 200)); 
             }
            currentStageIndex++;
        }
        
        // Llegar al 99% si no estaba ya
        if(currentPercent < 99) {
             updateProgressBar(99, "Compilando PDF final..."); 
             logToHollywoodConsole("COMPILING FINAL PDF...");
             await new Promise(resolve => setTimeout(resolve, 300)); 
        }
        
        updateProgressBar(100, finalMessage, false); // Marcar como éxito
        logToHollywoodConsole("PROCESS COMPLETE. PDF READY.");
    }

    function validateForm() {
        let isValid = true;
        form.querySelectorAll('input[required], textarea[required]').forEach(input => {
             input.classList.remove('is-invalid'); // Limpiar errores previos
            if (!input.value.trim()) {
                input.classList.add('is-invalid'); 
                isValid = false;
            }
        });
         // Validar filas de horas: al menos una fecha debe estar llena
         const dateInputs = logEntriesContainer.querySelectorAll('input[name="log_date[]"]');
         let hasAtLeastOneDate = false;
         dateInputs.forEach(input => {
             if (input.value) hasAtLeastOneDate = true;
             // Podrías añadir validación de hora aquí también
         });
         if (!hasAtLeastOneDate && dateInputs.length > 0) {
              isValid = false;
               if(dateInputs[0]) dateInputs[0].classList.add('is-invalid'); // Marcar la primera fecha como inválida
               alert("Debes registrar al menos un día de asistencia."); // O mostrar error de forma más elegante
         }

        return isValid;
    }
    
     // Función para mostrar mensajes de éxito con enlace de descarga
    function showSuccessMessage(message, downloadUrl, downloadText) {
        errorMessageDiv.innerHTML = ''; // Limpiar contenido anterior
        errorMessageDiv.classList.remove('alert-danger');
        errorMessageDiv.classList.add('alert', 'alert-success'); // Usar estilo de éxito

        const p = document.createElement('p');
        p.textContent = message;
        errorMessageDiv.appendChild(p);

        if(downloadUrl && downloadText) {
            const downloadLink = document.createElement('a');
            downloadLink.href = downloadUrl;
            downloadLink.target = '_blank'; // Abrir en nueva pestaña o iniciar descarga
            downloadLink.innerText = downloadText;
            downloadLink.classList.add('btn', 'btn-sm', 'btn-outline-success', 'ms-2');
            p.appendChild(downloadLink); // Añadir el botón al párrafo
        }
        errorMessageDiv.style.display = 'block';
    }

    // Función para mostrar errores (modificada ligeramente)
    function showError(message) {
        if (progressIntervalId) clearInterval(progressIntervalId);
        // Opcional: actualizar barra a estado de error
        updateProgressBar(100, "Error", true); 

        // Ocultar área de progreso después de un momento
        setTimeout(() => { 
            loadingProgressArea.style.display = 'none';
            if (hollywoodConsoleDiv) {
                hollywoodConsoleDiv.classList.remove('hollywood-console-visible');
                hollywoodConsoleDiv.classList.add('hollywood-console-hidden');
            }
        }, 1500); 

        errorMessageDiv.textContent = message;
        errorMessageDiv.classList.remove('alert-success'); // Asegurar que no tenga estilo de éxito
        errorMessageDiv.classList.add('alert', 'alert-danger');
        errorMessageDiv.style.display = 'block';
        // No ocultar el área de resultados necesariamente, el usuario podría querer ver la imagen que subió
    }

}); // Fin de DOMContentLoaded