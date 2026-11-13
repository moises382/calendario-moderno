# Calendario · Cuenta regresiva

Aplicación de escritorio hecha con **Python + Tkinter**, sin dependencias externas.
Combina un calendario mensual interactivo con una cuenta regresiva grande y animada.

## Cómo ejecutarla

Haz doble clic en **`Abrir Calendario.command`**.

La primera vez, si no encuentra el Python moderno, lo descarga e instala
automáticamente en `~/.local/share/calendario-python` (unos 25 MB, sin permisos
de administrador). Después ya abre al instante.

Desde la Terminal también funciona:

```bash
cd ~/calendario-moderno
./Abrir\ Calendario.command
# o, si ya está instalado el Python moderno:
~/.local/share/calendario-python/bin/python3 calendario.py
```

Si ejecutas `python3 calendario.py` con el Python del sistema, la app detecta
que su Tk 8.5 no dibuja bien en macOS 27 y se relanza sola con el Python
moderno. Para reinstalar ese Python manualmente:

```bash
cd ~/calendario-moderno
./instalar-python.sh
```

## Cómo se usa

- **Haz clic en un día del calendario** para calcular cuánto falta (o cuánto ha pasado) respecto a hoy.
- O escribe una fecha en los campos:
  - **DÍA**: obligatorio (1–31).
  - **MES**: número (1–12) o nombre (`enero`, `ene`, `septiembre`…). Si lo dejas vacío, se usa el mes actual o el siguiente. Si escribes un año, el mes es obligatorio.
  - **AÑO**: opcional. Si lo dejas vacío se calcula la próxima vez que ocurra esa fecha.
- Botones rápidos: **Año Nuevo**, **Navidad** y **Fin de año**.
- Navega con **‹ ›**, vuelve al mes actual con **Hoy**, o usa las flechas **← →** del teclado.
- Pulsa **Enter** en cualquier campo para calcular.

## Qué muestra

- Número grande de **días restantes** (o días transcurridos si la fecha ya pasó).
- Equivalencia en **semanas, meses aproximados, horas, días hábiles, fines de semana y minutos**.
- Progreso del año en curso.
- Reloj y fecha actualizados en vivo.
- Animación al cambiar de fecha y efectos hover en los controles.

## Reglas de cálculo

| Lo que escribes | Resultado |
| --- | --- |
| `1 / 1 / (vacío)` | Próximo 1 de enero (este año o el siguiente). |
| `1 / (vacío) / (vacío)` | Día 1 del mes actual; si ya pasó, del mes siguiente. |
| `25 / 12 / 2026` | 25 de diciembre de 2026 (aunque ya haya pasado). |
| `29 / 2 / (vacío)` | Próximo 29 de febrero, buscando el siguiente año bisiesto. |

## Personalización

Los colores están al inicio de `calendario.py`, en la sección **Paleta**.
Cambia `ACCENT` para modificar el color principal de toda la interfaz.

## Nota para macOS

macOS 27 incluye Python 3.9 con Tk 8.5, y esa combinación dibuja la ventana en
negro/blanco (sin la interfaz). Por eso esta app usa un **Python 3.13 con Tk 9**
instalado en tu carpeta de usuario. No necesitas Homebrew ni permisos de
administrador.

Si mueves la carpeta a otro Mac, ejecuta `./instalar-python.sh` una vez (o abre
`Abrir Calendario.command`, que lo hace solo).
