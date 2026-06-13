# Manual de uso: Enseñar una nueva letra y verificar el reconocimiento

Este manual explica paso a paso cómo capturar datos para una nueva letra (o clase), entrenar el modelo y verificar el reconocimiento en vivo.

## Requisitos previos
- Windows 64-bit, cámara web funcional.
- Python 3.9–3.11 (recomendado 64-bit).
- Dependencias instaladas (desde la raíz del proyecto):
```powershell
py -m pip install -r requirements.txt
```
- Ejecutar los comandos desde la carpeta raíz del proyecto (donde están `main.py` y `teaching.py`).

## Flujo general
1. Capturar ejemplos con `teaching.py` (modo estático y/o dinámico).
2. Entrenar el modelo estático con `ml/train.py` (y opcionalmente el dinámico con `ml/train_dynamic.py`).
3. Probar el reconocimiento en vivo con `main.py`.

---

## 1) Captura de datos con `teaching.py`
Inicia la herramienta de captura interactiva:
```powershell
py teaching.py
```
Verás un overlay con el estado del sistema y los controles. Asegúrate de que tu mano aparezca y se mantenga estable dentro del cuadro.

### Controles clave
- `m`: Abrir/cerrar menú de selección de etiqueta.
- `Flechas arriba/abajo`: Navegar el menú.
- `Enter`: Confirmar selección en el menú.
- `s`: Cambiar entre modo estático y dinámico.
- `t`: 
  - Modo estático: Captura una muestra.
  - Modo dinámico: Inicia/Detiene la grabación de una secuencia.
- `q`: Salir y guardar los datasets.

### Seleccionar o crear etiqueta
- Elige la etiqueta (por ejemplo, `A`, `B`, `C`).
- Si necesitas una etiqueta nueva, selecciónala/ingrésala según tu menú. Si tu versión no permite crear desde la interfaz, puedes capturar con una etiqueta existente y luego ajustar antes de entrenar (o bien capturar con la etiqueta deseada si el menú lo soporta). 

### Modo estático (recomendado para letras “fijas”)
1. Cambia a modo estático (`s`) si no lo estás.
2. Coloca tu mano formando la letra. Varía ligeramente posición, rotación e iluminación.
3. Pulsa `t` para capturar. Verás mensajes como:
   - `"Captura estática guardada: <etiqueta>"`
4. Captura múltiples muestras por etiqueta (sugerencia: 40–100). Cuantas más y más variadas, mejor generaliza.

### Modo dinámico (opcional para letras/gestos “en movimiento”)
1. Cambia a modo dinámico (`s`).
2. Pulsa `t` para iniciar la grabación; realiza el gesto; pulsa `t` de nuevo para detener.
3. Verás mensajes como:
   - `"Secuencia dinámica guardada: <etiqueta> (<n> frames)"`
4. Graba varias secuencias por etiqueta (sugerencia: 15–40), intentando consistencia y variaciones realistas.

### Guardado de datasets
Al salir con `q`, los datos se guardan automáticamente en:
- `data/datasets/dataset_static.json`
- `data/datasets/dataset_dynamic.json`

Si ves mensajes como:
- `"Landmarks incompletos: X/21"` → Asegúrate de que la mano esté completamente visible y bien detectada.
- `"No se pudo abrir la cámara"` → Revisa permisos, que otra app no esté usando la cámara y selecciona el dispositivo correcto.

---

## 2) Entrenamiento de modelos

### 2.1 Entrenamiento estático (obligatorio si agregaste etiquetas nuevas)
Ejecuta:
```powershell
py ml/train.py
```
Comportamiento:
- Usa `data/datasets/dataset_static.json` si existe; de lo contrario, puede recurrir a `data/datasets/dataset_final.json`.
- Genera/actualiza los archivos del modelo estático en `data/models/`:
  - `model.h5`
  - `labels.json`

Notas:
- Si has agregado o cambiado etiquetas, es necesario **reentrenar** para que el modelo las aprenda.
- El tiempo de entrenamiento depende de tu CPU/GPU y del tamaño del dataset (puede ir de minutos a decenas de minutos).

### 2.2 Entrenamiento dinámico (opcional)
Si capturaste secuencias dinámicas y quieres habilitar el reconocimiento temporal, ejecuta:
```powershell
py ml/train_dynamic.py
```
Esto entrena un modelo temporal (BiLSTM, etc.) desde `data/datasets/dataset_dynamic.json` y genera en `data/models/`:
- `model_dynamic.h5`
- `labels_dynamic.json`

---

## 3) Verificación en vivo con `main.py`
Ejecuta el sistema principal de reconocimiento:
```powershell
py main.py
```
En la vista verás:
- Predicción **Estático** (usa `model.h5` + `labels.json`).
- Predicción **Dinámico** (si has entrenado `model_dynamic.h5` + `labels_dynamic.json`).
- Estado de tracking (p. ej., `Tracking: OK/RECUPERANDO/PERDIDO`).

Consejos para validar:
- Prueba la(s) letra(s) nuevas varias veces y desde distintos ángulos/iluminaciones.
- Si la precisión es baja, recolecta más muestras variadas y reentrena.

---

## Ubicación de archivos importantes
- Datasets:
  - `data/datasets/dataset_static.json`
  - `data/datasets/dataset_dynamic.json`
- Modelos y assets:
  - `data/models/model.h5`
  - `data/models/labels.json`
  - `data/models/model_dynamic.h5` (si usas dinámico)
  - `data/models/labels_dynamic.json` (si usas dinámico)
  - `data/models/hand_landmarker.task` (modelo de detección de mano)

---

## Buenas prácticas y resolución de problemas
- Balancea el dataset: número similar de muestras por etiqueta.
- Varía condiciones (distancia, rotación, iluminación), pero mantén la forma clara.
- Si recibes `Landmarks incompletos`, encuadra mejor la mano y asegúrate de que los 21 puntos sean visibles.
- Si `main.py` no muestra la cámara, cierra apps que la usen (Teams/Zoom/etc.) y vuelve a intentar.
- Cambiar nombres de etiquetas en `labels.json` **no** cambia el modelo entrenado; para nuevos nombres/clases, reentrena.

---

## Anexo: consumo de recursos (referencial)
- Ejecución en vivo: ~700–1,200 MB de RAM.
- Entrenamiento: puede subir a 2–6 GB según tamaño del dataset y configuración.

Si necesitas un PDF para la entrega, puedes exportar este `.md` desde tu IDE o usando Pandoc.
