# Cómo trabajamos en daxe software

## Ramas
Cada tarea se trabaja en su propia rama, nunca directo en `main`.
Formato: `tipo/descripcion-corta`, en minúscula y con guiones.
Ejemplo: `docs/perfil-juan`, `feat/script-reportes`

## Commits
Usamos el formato `tipo: qué hiciste`, en minúscula y en presente.
Tipos: `feat`, `fix`, `docs`, `chore`.
Ejemplo: `docs: agrega perfil de juan`

## Revisión de Pull Requests
- Todo Pull Request lo revisa un integrante distinto a quien lo escribió.
- El líder del encargo asigna quién revisa a quién, y se va rotando.
- Antes de aprobar miramos: que los archivos sean los de la tarea,
  que no haya errores de redacción o código, y que el commit siga la convención.

## Cuándo se aprueba un Pull Request
- Está enlazado a un issue (`Closes #número`).
- Tiene al menos 1 aprobación de otro integrante.
- No incluye archivos que no corresponden (claves, `.env`, carpetas generadas).
- El título y los commits siguen la convención.
