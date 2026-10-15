# Bitácora de Evelin Johana Pérez Correa

## Qué hice
Como líder del proyecto daxe_software, he realizado las siguientes actividades de gestión, configuración y documentación a lo largo del desarrollo:

**Actividades de la Fase Anterior (Puesta en marcha):**
* Configuré el tablero visual de la empresa creando y estructurando los 7 issues obligatorios para el equipo de 4 integrantes.
* Coordiné la asignación correcta de las tareas generales y los perfiles de los compañeros (Xime, Juan, Sebastián y mi persona).
* Redacté y subí el archivo `README.md` principal de la empresa a través del PR #10, detallando los roles y el árbol de carpetas del repositorio.
* Diseñé y cargué mi perfil profesional individual en la ruta `equipo/evelin-perez.md` con el PR #11.

**Actividades de Hoy (Requerimiento R1 y Adelanto R2 - Rápido Paisa):**
* Configuré los campos personalizados del tablero de GitHub Projects, habilitando la columna de tipo fecha para monitorear la "Fecha límite" de las tareas del equipo.
* Creé y estructuré el archivo `.gitignore` en la raíz del proyecto para excluir de forma definitiva las carpetas locales de datos generados (`bandeja_entrada/`, `pedidos_ordenados/` y `revisar/`).
* Completé la redacción del archivo `README.md` principal, especificando la nueva estructura de directorios de la solución (dentro de la carpeta `src/`), los roles reales de los 4 integrantes y el manual detallado de ejecución del script del cliente.
* Desarrollé e implementé con éxito el script `src/resumen.py` (Ticket #39) para recorrer la bandeja de entrada del cliente usando pathlib, procesar formatos mixtos y exportar el informe consolidado `resumen.txt`.
* Desarrollé e implementé con éxito el script `src/reportes.py` (Ticket #38) para normalizar y estructurar los pedidos válidos, corrigiendo las fechas al formato internacional ISO (AAAA-MM-DD) y guardando los resultados en la raíz como `reporte.csv`.
* Sincronicé con éxito los cambios locales mediante la consola solventando un error de autenticación con un token de acceso personal (PAT) y abrí la solicitud de extracción vinculando el cierre automático de los tickets correspondientes.

## La revisión
* Revisé y aprobé el Pull Request #3 de Sebastián correspondiente a las reglas del equipo (`CONTRIBUTING.md`).
* Revisé la bitácora inicial de Sebastián (`sebastiancorrea001.md`) y le solicité una corrección en la sección de revisión para limpiar los campos pendientes y remover los corchetes antes de proceder con la fusión.
* Coordiné con Juan David Peña (@juaan06) la asignación del flujo de revisión cruzada (Code Review) para evaluar mis Pull Requests.
* Asigné a Sebastián (@SebastianCorrea001) como revisor oficial en GitHub del nuevo Pull Request abierto para la unificación de los entregables lógicos del requerimiento R2.

## Uso de IA
* Utilicé la Inteligencia Artificial como asistente técnico y metodológico en la fase inicial para estructurar el formato de los issues en la interfaz web de GitHub, verificar la sintaxis de las tablas en Markdown para el archivo README y solucionar los errores de fusión (`MERGE_HEAD`) en la terminal local de Git.
* Apliqué el uso de la IA el día de hoy para corregir la organización del tablero Kanban (eliminando las tarjetas genéricas de fases por tareas individuales atómicas), validar la sintaxis de exclusión en el archivo de entorno .gitignore y estructurar los algoritmos de ordenamiento, lectura y conversión de fechas mezcladas en los scripts resumen.py y reportes.py.
