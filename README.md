# 🏢 daxe_software

## 🚀 ¿Qué hace nuestra empresa?
Desarrollamos una solución de software orientada a automatizar la clasificación, lectura y procesamiento eficiente de pedidos mensuales para la empresa Rápido Paisa.

## 👥 Nuestro Equipo de Trabajo
A continuación se detallan los integrantes del proyecto, sus usuarios de GitHub y los roles asignados:

| Nombre Completo | Usuario de GitHub | Rol en la Empresa |
| :--- | :--- | :--- |
| **Evelin Johana Pérez Correa** | @Evelin2405 | Líder de Proyecto / Desarrolladora |
| **Sebastian Correa** | @SebastianCorrea001 | Desarrollador |
| **Juan David Peña** | @juaan06 | Desarrollador |
| **Xime Acevedo** | @xa452087-ctrl | Desarrolladora |

## 📁 Organización del Repositorio
Así está estructurado el árbol de carpetas de nuestro proyecto:

```text
daxe_software/
├── docs/               # Documentación general del proyecto
│   └── bitacora/       # Bitácoras semanales individuales del equipo
├── equipo/             # Perfiles individuales de los integrantes
│   ├── evelin-perez.md
│   ├── sebastian-correa.md
│   ├── juan-pena.md
│   └── xime-acevedo.md
├── src/                # Código fuente principal de la aplicación
│   ├── organizar.py    # Script principal y orquestador del flujo
│   ├── sedes.py        # Funciones de reconocimiento de sedes
│   └── lectores.py     # Funciones de lectura (.txt, .csv, .json)
├── .gitignore          # Archivos excluidos del control de versiones
├── CONTRIBUTING.md     # Reglas y acuerdos del equipo
├── generar_pedidos.py  # Script de datos de prueba del cliente
└── README.md           # Descripción general del repositorio (este archivo)
```

## 📦 Generación de Datos de Prueba (Rápido Paisa)
El repositorio incluye el script proporcionado por el cliente para simular de manera local la bandeja de entrada.

* **Para generar los pedidos del Lote 1 (Septiembre):**
  ```bash
  python generar_pedidos.py
  ```
* **Para generar los pedidos del Lote 2 (Octubre):**
  ```bash
  python generar_pedidos.py --lote 2
  ```

> ⚠️ **Nota:** Las carpetas resultantes `bandeja_entrada/`, `pedidos_ordenados/` y `revisar/` están configuradas en el `.gitignore` y no se sincronizan en GitHub. Cada desarrollador debe ejecutar el script localmente.
