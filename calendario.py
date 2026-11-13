#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calendario moderno con cuenta regresiva.
Tkinter puro, sin dependencias externas.

Ejecutar:
    python3 calendario.py
"""

import calendar
import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import date, datetime, timedelta

# En macOS 27 el Tk 8.5 que trae el Python del sistema dibuja la ventana en
# blanco/negro. Si detectamos esa versión, nos relanzamos con el Python moderno
# que instalamos junto a la app (Tk 9).
RUTA_PYTHON_MODERNO = os.path.expanduser(
    "~/.local/share/calendario-python/bin/python3"
)


def _usar_tk_moderno():
    if tk.TkVersion >= 8.6:
        return
    moderno = os.path.realpath(RUTA_PYTHON_MODERNO)
    actual = os.path.realpath(sys.executable)
    if os.path.exists(moderno) and actual != moderno:
        os.execv(moderno, [moderno, os.path.abspath(__file__), *sys.argv[1:]])

# ----------------------------------------------------------------------------
# Paleta y tipografía
# ----------------------------------------------------------------------------

BG          = "#0A0C11"
CARD        = "#141925"
CARD_SOFT   = "#1C2231"
CELL        = "#1A2130"
CELL_HOVER  = "#273044"
STROKE      = "#262E40"
TEXT        = "#F5F7FC"
MUTED       = "#8E97AB"
DIM         = "#5A6378"
ACCENT      = "#7C5CFF"
ACCENT_SOFT = "#2E2758"
ACCENT_2    = "#3DDC97"
RED         = "#FF6B7A"

FAMILY = "Helvetica Neue"

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
DIAS_CORTOS = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
DIAS_NOMBRE = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]


def F(size, weight="normal"):
    return (FAMILY, size, weight)


def elegir_familia(root):
    disponibles = set(tkfont.families(root))
    for nombre in ("SF Pro Display", "Helvetica Neue", "Avenir Next",
                   "Helvetica", "Segoe UI", "Arial"):
        if nombre in disponibles:
            return nombre
    return "Helvetica"


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------

def fmt(numero):
    """Formato de miles al estilo español: 1368 -> 1.368."""
    return f"{numero:,}".replace(",", ".")


def dec1(valor):
    """Un decimal con coma; quita el ',0' sobrante."""
    texto = f"{valor:.1f}".replace(".", ",")
    return texto[:-2] if texto.endswith(",0") else texto


def fecha_larga(fecha, con_dia_semana=False):
    texto = f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"
    if con_dia_semana:
        texto = DIAS_NOMBRE[fecha.weekday()].capitalize() + ", " + texto
    return texto


def parsear_mes(texto):
    """Acepta '1', '01', 'ene', 'enero', 'setiembre'... Devuelve 1-12 o None."""
    t = texto.strip().lower().replace(".", "")
    if not t:
        return None
    if t.isdigit():
        m = int(t)
        return m if 1 <= m <= 12 else None
    if len(t) < 3:
        return None
    for i, nombre in enumerate(MESES, 1):
        if nombre.startswith(t):
            return i
    if t.startswith("set"):
        return 9
    return None


def sumar_meses(fecha, cantidad):
    indice = fecha.month - 1 + cantidad
    año = fecha.year + indice // 12
    mes = indice % 12 + 1
    dia = min(fecha.day, calendar.monthrange(año, mes)[1])
    return date(año, mes, dia)


def resolver_objetivo(dia, mes, año, hoy):
    """
    Calcula la fecha objetivo.
    - Con año: fecha exacta.
    - Sin mes: ese día del mes actual o del siguiente si ya pasó.
    - Con mes y sin año: la próxima vez que ocurra esa fecha.
    """
    if año is not None:
        if mes is None:
            raise ValueError("Se necesita el mes")
        return date(año, mes, dia)

    if mes is None:
        try:
            base = date(hoy.year, hoy.month, dia)
        except ValueError:
            base = None
        if base is not None and base >= hoy:
            return base

        año, mes_actual = hoy.year, hoy.month
        for _ in range(12):
            mes_actual += 1
            if mes_actual == 13:
                mes_actual = 1
                año += 1
            try:
                return date(año, mes_actual, dia)
            except ValueError:
                continue
        raise ValueError("No se encontró una fecha válida")

    if mes == 2 and dia == 29:
        año_bisiesto = hoy.year
        while True:
            if calendar.isleap(año_bisiesto):
                objetivo = date(año_bisiesto, 2, 29)
                if objetivo >= hoy:
                    return objetivo
            año_bisiesto += 1

    objetivo = date(hoy.year, mes, dia)
    if objetivo < hoy:
        objetivo = date(hoy.year + 1, mes, dia)
    return objetivo


def brecha_humana(inicio, fin):
    """'1 mes y 27 días' entre dos fechas (fin >= inicio)."""
    meses = (fin.year - inicio.year) * 12 + (fin.month - inicio.month)
    if fin.day < inicio.day:
        meses -= 1
    meses = max(0, meses)
    ancla = sumar_meses(inicio, meses)
    resto = (fin - ancla).days

    partes = []
    if meses:
        partes.append(f"{meses} mes" if meses == 1 else f"{meses} meses")
    if resto:
        partes.append(f"{resto} día" if resto == 1 else f"{resto} días")
    return " y ".join(partes) if partes else "0 días"


def contar_fines_de_semana(inicio, fin):
    """Sábados y domingos entre inicio (exclusivo) y fin (inclusivo)."""
    total = (fin - inicio).days
    if total <= 0:
        return 0
    semanas, resto = divmod(total, 7)
    cuenta = semanas * 2
    for i in range(1, resto + 1):
        if (inicio + timedelta(days=i)).weekday() >= 5:
            cuenta += 1
    return cuenta


def redondear_rect(canvas, x1, y1, x2, y2, radio, fill, outline="", width=0, tags=()):
    """Rectángulo redondeado dibujado como un único polígono suavizado."""
    radio = max(0, min(radio, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    puntos = [
        x1 + radio, y1,
        x2 - radio, y1,
        x2, y1,
        x2, y1 + radio,
        x2, y2 - radio,
        x2, y2,
        x2 - radio, y2,
        x1 + radio, y2,
        x1, y2,
        x1, y2 - radio,
        x1, y1 + radio,
        x1, y1,
    ]
    return canvas.create_polygon(
        puntos, smooth=True, splinesteps=24,
        fill=fill, outline=outline, width=width, tags=tags,
    )


# ----------------------------------------------------------------------------
# Componentes visuales
# ----------------------------------------------------------------------------

class Card(tk.Canvas):
    """Panel con esquinas redondeadas que contiene un Frame interno."""

    def __init__(self, master, bg=CARD, outer=BG, radius=20, pad=20,
                 outline=STROKE, **kwargs):
        super().__init__(master, bg=outer, highlightthickness=0, bd=0, **kwargs)
        self.bg = bg
        self.radius = radius
        self.pad = pad
        self.outline = outline
        self.inner = tk.Frame(self, bg=bg)
        self._win = self.create_window(pad, pad, anchor="nw", window=self.inner)
        self.bind("<Configure>", self._al_redimensionar)

    def _al_redimensionar(self, evento):
        ancho, alto = evento.width, evento.height
        if ancho < 4 or alto < 4:
            return
        self.delete("card_shape")
        redondear_rect(
            self, 1, 1, ancho - 1, alto - 1, self.radius,
            fill=self.bg, outline=self.outline, width=1, tags=("card_shape",),
        )
        self.tag_lower("card_shape")
        self.coords(self._win, self.pad, self.pad)
        self.itemconfigure(
            self._win,
            width=max(1, ancho - 2 * self.pad),
            height=max(1, alto - 2 * self.pad),
        )


class Pill(tk.Canvas):
    """Botón tipo píldora, dibujado a mano para controlar los colores."""

    def __init__(self, master, texto, comando=None, width=90, height=34,
                 radius=None, fill=CARD_SOFT, hover=ACCENT, fg=TEXT,
                 hover_fg="#FFFFFF", outline=STROKE, hover_outline=None,
                 font=None, bg=CARD):
        super().__init__(master, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.texto = texto
        self.comando = comando
        self.radius = height / 2.0 if radius is None else radius
        self.fill = fill
        self.hover = hover
        self.fg = fg
        self.hover_fg = hover_fg
        self.outline = outline
        self.hover_outline = hover if hover_outline is None else hover_outline
        self.font = font or F(10, "bold")
        self._encima = False

        self.bind("<Configure>", lambda e: self._dibujar())
        self.bind("<Enter>", self._entrar)
        self.bind("<Leave>", self._salir)
        self.bind("<Button-1>", self._clic)
        self._dibujar()

    def _entrar(self, _evento):
        self._encima = True
        self._dibujar()

    def _salir(self, _evento):
        self._encima = False
        self._dibujar()

    def _clic(self, _evento):
        if callable(self.comando):
            self.comando()

    def _dibujar(self):
        ancho = self.winfo_width()
        alto = self.winfo_height()
        if ancho <= 1 or alto <= 1:
            ancho = int(self["width"])
            alto = int(self["height"])
        self.delete("all")
        relleno = self.hover if self._encima else self.fill
        borde = self.hover_outline if self._encima else self.outline
        redondear_rect(self, 1, 1, ancho - 1, alto - 1, self.radius,
                       fill=relleno, outline=borde, width=1)
        self.create_text(
            ancho / 2.0, alto / 2.0 - 1,
            text=self.texto,
            fill=self.hover_fg if self._encima else self.fg,
            font=self.font,
        )


class DayCell(tk.Canvas):
    """Celda de un día del calendario."""

    def __init__(self, master, app, fecha, atenuado, es_hoy, seleccionado):
        super().__init__(master, bg=CARD, width=44, height=44,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.app = app
        self.fecha = fecha
        self.atenuado = atenuado
        self.es_hoy = es_hoy
        self.seleccionado = seleccionado
        self._encima = False

        self.bind("<Configure>", lambda e: self._dibujar())
        self.bind("<Enter>", self._entrar)
        self.bind("<Leave>", self._salir)
        self.bind("<Button-1>", lambda e: self.app.seleccionar_fecha(self.fecha))
        self._dibujar()

    def _entrar(self, _evento):
        self._encima = True
        self._dibujar()

    def _salir(self, _evento):
        self._encima = False
        self._dibujar()

    def _dibujar(self):
        ancho = self.winfo_width()
        alto = self.winfo_height()
        if ancho <= 2 or alto <= 2:
            return

        self.delete("all")

        if self.seleccionado:
            relleno, color, borde = ACCENT, "#FFFFFF", ""
        elif self.es_hoy:
            relleno, color, borde = CELL_HOVER, ACCENT, ACCENT
        elif self._encima:
            relleno, color, borde = CELL_HOVER, DIM if self.atenuado else TEXT, ""
        elif self.atenuado:
            relleno, color, borde = CARD, DIM, ""
        else:
            relleno, color, borde = CELL, TEXT, ""

        redondear_rect(self, 2, 2, ancho - 2, alto - 2, 11,
                       fill=relleno, outline=borde, width=1)

        peso = "bold" if (self.seleccionado or self.es_hoy) else "normal"
        centro_y = alto / 2.0 - (2 if self.es_hoy and not self.seleccionado else 0)
        self.create_text(ancho / 2.0, centro_y, text=str(self.fecha.day),
                         fill=color, font=F(15, peso))

        if self.es_hoy and not self.seleccionado:
            cy = alto - 10
            self.create_oval(ancho / 2.0 - 2, cy - 2, ancho / 2.0 + 2, cy + 2,
                             fill=ACCENT, outline="")


class StatTile(Card):
    """Tarjeta pequeña para una estadística."""

    def __init__(self, master, titulo, **kwargs):
        super().__init__(master, bg=CARD_SOFT, outer=CARD, radius=12, pad=10,
                         outline=CARD_SOFT, width=120, height=58, **kwargs)
        self.valor = tk.Label(self.inner, text="—", bg=CARD_SOFT, fg=TEXT,
                              font=F(15, "bold"), anchor="w")
        self.valor.pack(fill="x")
        self.titulo = tk.Label(self.inner, text=titulo, bg=CARD_SOFT, fg=MUTED,
                               font=F(8, "bold"), anchor="w")
        self.titulo.pack(fill="x", pady=(1, 0))


# ----------------------------------------------------------------------------
# Aplicación
# ----------------------------------------------------------------------------

class CalendarApp:

    def __init__(self, root):
        self.root = root
        self.hoy = date.today()
        self.ver_año = self.hoy.year
        self.ver_mes = self.hoy.month
        self.seleccionado = None
        self.objetivo = None

        self._numero_mostrado = 0
        self._numero_job = None
        self._numero_tam = 0
        self._barra_pct = 0.0
        self._barra_objetivo = 0.0
        self._barra_job = None
        self._reloj_job = None

        self._construir()
        self.dia_var.set("1")
        self.mes_var.set("1")
        self.año_var.set("")
        self._fijar_objetivo(
            resolver_objetivo(1, 1, None, self.hoy),
            navegar=False, sincronizar_campos=False,
        )
        self._tic()

    # -- construcción de la interfaz -----------------------------------------

    def _construir(self):
        self.root.configure(bg=BG)
        self.root.option_add("*Entry.selectBackground", ACCENT)
        self.root.option_add("*Entry.selectForeground", "#FFFFFF")
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        self._construir_cabecera()

        cuerpo = tk.Frame(self.root, bg=BG)
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=30, pady=(6, 28))
        cuerpo.rowconfigure(0, weight=1)
        cuerpo.columnconfigure(0, weight=3, uniform="cuerpo")
        cuerpo.columnconfigure(1, weight=2, uniform="cuerpo")

        self._construir_calendario(cuerpo)
        self._construir_cuenta(cuerpo)

    def _construir_cabecera(self):
        cabecera = tk.Frame(self.root, bg=BG)
        cabecera.grid(row=0, column=0, sticky="ew", padx=32, pady=(22, 10))

        izquierda = tk.Frame(cabecera, bg=BG)
        izquierda.pack(side="left")
        fila = tk.Frame(izquierda, bg=BG)
        fila.pack(anchor="w")
        tk.Label(fila, text="●", bg=BG, fg=ACCENT,
                 font=F(17, "bold")).pack(side="left", padx=(0, 9))
        tk.Label(fila, text="Calendario", bg=BG, fg=TEXT,
                 font=F(23, "bold")).pack(side="left")
        tk.Label(izquierda, text="Cuenta regresiva · el tiempo, a la vista",
                 bg=BG, fg=MUTED, font=F(10)).pack(anchor="w", pady=(1, 0))

        derecha = tk.Frame(cabecera, bg=BG)
        derecha.pack(side="right")
        self.reloj = tk.Label(derecha, text="", bg=BG, fg=TEXT,
                              font=F(20, "bold"))
        self.reloj.pack(anchor="e")
        self.fecha_cabecera = tk.Label(derecha, text="", bg=BG, fg=MUTED,
                                       font=F(10))
        self.fecha_cabecera.pack(anchor="e")

    def _construir_calendario(self, padre):
        self.card_cal = Card(padre, width=620, height=620)
        self.card_cal.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        c = self.card_cal.inner
        c.columnconfigure(0, weight=1)
        c.rowconfigure(2, weight=1)

        # Fila superior: mes + navegación
        superior = tk.Frame(c, bg=CARD)
        superior.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))

        self.titulo_mes = tk.Label(superior, text="", bg=CARD, fg=TEXT,
                                   font=F(19, "bold"))
        self.titulo_mes.pack(side="left")

        nav = tk.Frame(superior, bg=CARD)
        nav.pack(side="right")
        self.btn_anterior = Pill(nav, "‹", comando=lambda: self.cambiar_mes(-1),
                                 width=34, height=34, radius=17,
                                 font=F(17, "bold"))
        self.btn_anterior.pack(side="left", padx=(0, 6))
        self.btn_siguiente = Pill(nav, "›", comando=lambda: self.cambiar_mes(1),
                                  width=34, height=34, radius=17,
                                  font=F(17, "bold"))
        self.btn_siguiente.pack(side="left", padx=(0, 6))
        self.btn_hoy = Pill(nav, "Hoy", comando=self.ir_a_hoy,
                            width=60, height=34, radius=17,
                            font=F(10, "bold"))
        self.btn_hoy.pack(side="left")

        # Días de la semana
        cab_dias = tk.Frame(c, bg=CARD)
        cab_dias.grid(row=1, column=0, sticky="ew", padx=20, pady=(2, 2))
        for i, nombre in enumerate(DIAS_CORTOS):
            cab_dias.columnconfigure(i, weight=1, uniform="cabdia")
            tk.Label(cab_dias, text=nombre, bg=CARD,
                     fg=MUTED if i < 5 else DIM,
                     font=F(9, "bold")).grid(row=0, column=i)

        # Cuadrícula de días
        self.marco_dias = tk.Frame(c, bg=CARD)
        self.marco_dias.grid(row=2, column=0, sticky="nsew", padx=16, pady=(2, 6))
        for i in range(7):
            self.marco_dias.columnconfigure(i, weight=1, uniform="dia")
        for i in range(6):
            self.marco_dias.rowconfigure(i, weight=1, uniform="semdia", minsize=40)

        # Pie: progreso del año
        pie = tk.Frame(c, bg=CARD)
        pie.grid(row=3, column=0, sticky="ew", padx=20, pady=(4, 16))
        fila_pie = tk.Frame(pie, bg=CARD)
        fila_pie.pack(fill="x")
        self.texto_progreso = tk.Label(fila_pie, text="", bg=CARD, fg=MUTED,
                                       font=F(9, "bold"))
        self.texto_progreso.pack(side="left")
        self.pct_progreso = tk.Label(fila_pie, text="", bg=CARD, fg=TEXT,
                                     font=F(9, "bold"))
        self.pct_progreso.pack(side="right")
        self.barra = tk.Canvas(pie, height=8, bg=CARD, highlightthickness=0, bd=0)
        self.barra.pack(fill="x", pady=(7, 0))
        self.barra.bind("<Configure>", lambda e: self._dibujar_barra())

    def _construir_cuenta(self, padre):
        self.card_cuenta = Card(padre, width=430, height=620)
        self.card_cuenta.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        d = self.card_cuenta.inner
        d.bind("<Configure>", self._redimensionar_numero)

        arriba = tk.Frame(d, bg=CARD)
        arriba.pack(side="top", fill="x")

        tk.Label(arriba, text="CUENTA REGRESIVA", bg=CARD, fg=MUTED,
                 font=F(9, "bold")).pack(anchor="w")

        self.etiqueta_objetivo = tk.Label(
            arriba, text="", bg=CARD, fg=TEXT, font=F(15, "bold"),
            anchor="w", justify="left", wraplength=380,
        )
        self.etiqueta_objetivo.pack(anchor="w", pady=(8, 0))

        fila_num = tk.Frame(arriba, bg=CARD)
        fila_num.pack(fill="x", pady=(4, 0))
        self.numero = tk.Label(fila_num, text="0", bg=CARD, fg=ACCENT,
                               font=F(68, "bold"))
        self.numero.pack(side="left")
        self.unidad = tk.Label(fila_num, text="días\nrestantes", bg=CARD, fg=MUTED,
                               font=F(11), justify="left", anchor="w")
        self.unidad.pack(side="left", anchor="s", padx=(10, 0), pady=(0, 12))

        self.mensaje = tk.Label(arriba, text="", bg=CARD, fg=MUTED,
                                font=F(10), anchor="w", justify="left",
                                wraplength=380)
        self.mensaje.pack(anchor="w", pady=(2, 0))

        # Estadísticas (2 filas x 3)
        estadisticas = tk.Frame(arriba, bg=CARD)
        estadisticas.pack(fill="x", pady=(18, 0))
        for i in range(3):
            estadisticas.columnconfigure(i, weight=1, uniform="stat")
        titulos = ["SEMANAS", "MESES APROX.", "HORAS",
                   "DÍAS HÁBILES", "FINES DE SEMANA", "MINUTOS"]
        self.tiles = []
        for i, titulo in enumerate(titulos):
            tile = StatTile(estadisticas, titulo)
            tile.grid(
                row=i // 3, column=i % 3, sticky="ew",
                padx=(0, 6) if i % 3 < 2 else (0, 0),
                pady=(0, 7) if i < 3 else (0, 0),
            )
            self.tiles.append(tile)

        abajo = tk.Frame(d, bg=CARD)
        abajo.pack(side="bottom", fill="x")

        tk.Frame(abajo, bg=STROKE, height=1).pack(fill="x", pady=(16, 14))
        tk.Label(abajo, text="CALCULAR OTRA FECHA", bg=CARD, fg=MUTED,
                 font=F(9, "bold")).pack(anchor="w")

        campos = tk.Frame(abajo, bg=CARD)
        campos.pack(fill="x", pady=(8, 0))
        self.dia_var = tk.StringVar()
        self.mes_var = tk.StringVar()
        self.año_var = tk.StringVar()

        self.entrada_dia = self._campo(campos, "DÍA", self.dia_var, 0, 2, True)
        self.entrada_mes = self._campo(campos, "MES", self.mes_var, 1, 12, False)
        self.entrada_año = self._campo(campos, "AÑO", self.año_var, 2, 4, True)

        self.error = tk.Label(abajo, text=" ", bg=CARD, fg=RED, font=F(9),
                              anchor="w")
        self.error.pack(anchor="w", pady=(6, 0))

        self.btn_calcular = Pill(
            abajo, "Calcular días restantes", comando=self.calcular,
            width=300, height=46, radius=14, fill=ACCENT, hover="#9077FF",
            fg="#FFFFFF", hover_fg="#FFFFFF", outline=ACCENT,
            font=F(11, "bold"),
        )
        self.btn_calcular.pack(fill="x", pady=(8, 0))

        atajos = tk.Frame(abajo, bg=CARD)
        atajos.pack(fill="x", pady=(12, 0))
        fuente_atajo = tkfont.Font(family=FAMILY, size=9, weight="bold")
        for texto, dia, mes in (("Año Nuevo", 1, 1),
                                ("Navidad", 25, 12),
                                ("Fin de año", 31, 12)):
            ancho = fuente_atajo.measure(texto) + 28
            chip = Pill(atajos, texto, comando=lambda d=dia, m=mes: self._atajo(d, m),
                        width=ancho, height=30, radius=15, fill=CARD_SOFT,
                        hover=ACCENT_SOFT, hover_fg=TEXT, outline=STROKE,
                        hover_outline=ACCENT, font=fuente_atajo)
            chip.pack(side="left", padx=(0, 7))

        tk.Label(abajo, text="Sin año se usa la próxima vez que ocurra la fecha.",
                 bg=CARD, fg=DIM, font=F(9), anchor="w").pack(anchor="w", pady=(10, 0))

    def _campo(self, padre, titulo, variable, columna, limite, solo_digitos):
        padre.columnconfigure(columna, weight=1, uniform="campo")
        marco = tk.Frame(padre, bg=CARD)
        marco.grid(row=0, column=columna, sticky="ew",
                   padx=(0, 7) if columna < 2 else (0, 0))
        tk.Label(marco, text=titulo, bg=CARD, fg=MUTED,
                 font=F(8, "bold"), anchor="w").pack(anchor="w", pady=(0, 4))

        entrada = tk.Entry(
            marco, textvariable=variable, bg="#0E131D", fg=TEXT,
            insertbackground=TEXT, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=STROKE,
            highlightcolor=ACCENT, justify="center", font=F(13, "bold"),
        )
        entrada.pack(fill="x", ipady=5)

        if solo_digitos:
            vcmd = (self.root.register(self._validar_digitos), "%P", limite)
        else:
            vcmd = (self.root.register(self._validar_longitud), "%P", limite)
        entrada.configure(validate="key", validatecommand=vcmd)

        entrada.bind("<FocusIn>", lambda e, w=entrada: w.configure(
            highlightbackground=ACCENT, highlightcolor=ACCENT))
        entrada.bind("<FocusOut>", lambda e, w=entrada: w.configure(
            highlightbackground=STROKE))
        entrada.bind("<Return>", lambda e: self.calcular())
        return entrada

    @staticmethod
    def _validar_digitos(propuesto, limite):
        return (propuesto == "" or propuesto.isdigit()) and len(propuesto) <= int(limite)

    @staticmethod
    def _validar_longitud(propuesto, limite):
        return len(propuesto) <= int(limite)

    # -- lógica de fechas ----------------------------------------------------

    def calcular(self):
        self._mostrar_error("")
        dia_txt = self.dia_var.get().strip()
        mes_txt = self.mes_var.get().strip()
        año_txt = self.año_var.get().strip()

        if not dia_txt:
            self._mostrar_error("Escribe un día entre 1 y 31.")
            self.entrada_dia.focus_set()
            return
        dia = int(dia_txt)
        if not 1 <= dia <= 31:
            self._mostrar_error("El día debe estar entre 1 y 31.")
            self.entrada_dia.focus_set()
            return

        mes = None
        if mes_txt:
            mes = parsear_mes(mes_txt)
            if mes is None:
                self._mostrar_error("Mes inválido: usa 1-12 o su nombre.")
                self.entrada_mes.focus_set()
                return

        año = None
        if año_txt:
            if len(año_txt) != 4 or not (1900 <= int(año_txt) <= 2999):
                self._mostrar_error("Escribe un año de 4 cifras (ej. 2027).")
                self.entrada_año.focus_set()
                return
            año = int(año_txt)
            if mes is None:
                self._mostrar_error("Indica también el mes cuando escribas un año.")
                self.entrada_mes.focus_set()
                return

        try:
            objetivo = resolver_objetivo(dia, mes, año, date.today())
        except ValueError:
            self._mostrar_error("Esa fecha no existe. Revisa el día y el mes.")
            return

        self._fijar_objetivo(objetivo, navegar=True, sincronizar_campos=False)

    def _atajo(self, dia, mes):
        self.dia_var.set(str(dia))
        self.mes_var.set(str(mes))
        self.año_var.set("")
        self.calcular()

    def _fijar_objetivo(self, objetivo, navegar=False, sincronizar_campos=False):
        self.objetivo = objetivo
        self.seleccionado = objetivo

        if navegar:
            self.ver_año, self.ver_mes = objetivo.year, objetivo.month
        if sincronizar_campos:
            self.dia_var.set(str(objetivo.day))
            self.mes_var.set(str(objetivo.month))
            self.año_var.set(str(objetivo.year))

        self._renderizar_calendario()
        self._actualizar_cuenta()

    def seleccionar_fecha(self, fecha):
        self._fijar_objetivo(fecha, navegar=True, sincronizar_campos=True)

    def cambiar_mes(self, delta):
        indice = self.ver_mes - 1 + delta
        self.ver_año += indice // 12
        self.ver_mes = indice % 12 + 1
        self._renderizar_calendario()

    def ir_a_hoy(self):
        hoy = date.today()
        self._fijar_objetivo(hoy, navegar=True, sincronizar_campos=True)

    def _al_pulsar_flecha(self, delta):
        if isinstance(self.root.focus_get(), tk.Entry):
            return
        self.cambiar_mes(delta)

    # -- render --------------------------------------------------------------

    def _renderizar_calendario(self):
        self.titulo_mes.config(
            text=f"{MESES[self.ver_mes - 1].capitalize()} {self.ver_año}"
        )
        for hijo in self.marco_dias.winfo_children():
            hijo.destroy()

        hoy = date.today()
        primero = date(self.ver_año, self.ver_mes, 1)
        inicio = primero - timedelta(days=primero.weekday())

        for indice in range(42):
            fecha = inicio + timedelta(days=indice)
            celda = DayCell(
                self.marco_dias, self, fecha,
                atenuado=(fecha.month != self.ver_mes),
                es_hoy=(fecha == hoy),
                seleccionado=(self.seleccionado == fecha),
            )
            celda.grid(row=indice // 7, column=indice % 7,
                       sticky="nsew", padx=2, pady=2)

        self._actualizar_progreso()

    def _actualizar_cuenta(self):
        hoy = date.today()
        self.hoy = hoy
        objetivo = self.objetivo
        dias = (objetivo - hoy).days
        abs_dias = abs(dias)

        self.etiqueta_objetivo.config(text=fecha_larga(objetivo, con_dia_semana=True))

        if dias > 0:
            self.numero.config(fg=ACCENT)
            self.unidad.config(text="día\nrestante" if dias == 1 else "días\nrestantes")
            self.mensaje.config(text=brecha_humana(hoy, objetivo) + " por delante")
        elif dias == 0:
            self.numero.config(fg=ACCENT_2)
            self.unidad.config(text="¡es\nhoy!")
            self.mensaje.config(text="Hoy es el día · disfrútalo")
        else:
            self.numero.config(fg=RED)
            self.unidad.config(text="día\ntranscurrido" if abs_dias == 1
                               else "días\ntranscurridos")
            self.mensaje.config(text="Hace " + brecha_humana(objetivo, hoy))

        fines = contar_fines_de_semana(objetivo, hoy) if dias < 0 else \
            contar_fines_de_semana(hoy, objetivo)
        habiles = abs_dias - fines

        valores = [
            dec1(abs_dias / 7.0),
            dec1(abs_dias / 30.4375),
            fmt(abs_dias * 24),
            fmt(habiles),
            fmt(fines),
            fmt(abs_dias * 24 * 60),
        ]
        for tile, valor in zip(self.tiles, valores):
            tam = 15 if len(valor) <= 7 else (12 if len(valor) <= 10 else 10)
            tile.valor.config(text=valor, font=F(tam, "bold"))

        self._animar_numero(abs_dias)
        self._actualizar_progreso()

    def _actualizar_progreso(self):
        hoy = date.today()
        total = 366 if calendar.isleap(hoy.year) else 365
        objetivo = hoy.timetuple().tm_yday / float(total)

        self.texto_progreso.config(text=f"Progreso de {hoy.year}")
        if abs(objetivo - self._barra_objetivo) > 1e-6:
            self._barra_objetivo = objetivo
            self._animar_barra()
        else:
            self._dibujar_barra()

    def _dibujar_barra(self):
        ancho = self.barra.winfo_width()
        alto = 8
        if ancho <= 2:
            return
        self.barra.delete("all")
        redondear_rect(self.barra, 0, 0, ancho, alto, alto / 2.0,
                       fill="#242B3C")
        relleno = max(0.0, min(1.0, self._barra_pct)) * ancho
        if relleno > 0:
            redondear_rect(self.barra, 0, 0, max(relleno, 8), alto, alto / 2.0,
                           fill=ACCENT)
        self.pct_progreso.config(text=f"{int(round(self._barra_pct * 100))} %")

    def _animar_barra(self):
        if self._barra_job:
            self.root.after_cancel(self._barra_job)
            self._barra_job = None

        def paso():
            diferencia = self._barra_objetivo - self._barra_pct
            if abs(diferencia) < 0.002:
                self._barra_pct = self._barra_objetivo
                self._dibujar_barra()
                self._barra_job = None
                return
            self._barra_pct += diferencia * 0.22
            self._dibujar_barra()
            self._barra_job = self.root.after(16, paso)

        paso()

    def _animar_numero(self, destino):
        if self._numero_job:
            self.root.after_cancel(self._numero_job)
            self._numero_job = None

        inicio = self._numero_mostrado
        pasos = 18

        def paso(i=0):
            t = min(1.0, i / float(pasos))
            suavizado = 1 - (1 - t) ** 3
            valor = int(round(inicio + (destino - inicio) * suavizado))
            self._numero_mostrado = valor
            self.numero.config(text=fmt(valor))
            if i < pasos:
                self._numero_job = self.root.after(16, paso, i + 1)
            else:
                self._numero_mostrado = destino
                self.numero.config(text=fmt(destino))
                self._numero_job = None

        paso()

    def _redimensionar_numero(self, evento):
        tam = int(max(42, min(74, evento.width * 0.165)))
        if tam != self._numero_tam:
            self._numero_tam = tam
            self.numero.config(font=F(tam, "bold"))
            self.etiqueta_objetivo.config(wraplength=max(240, evento.width - 10))
            self.mensaje.config(wraplength=max(240, evento.width - 10))

    # -- reloj ---------------------------------------------------------------

    def _tic(self):
        ahora = datetime.now()
        self.reloj.config(text=ahora.strftime("%H:%M:%S"))
        if ahora.date() != self.hoy:
            self.hoy = ahora.date()
            self._renderizar_calendario()
            self._actualizar_cuenta()
        self.fecha_cabecera.config(text=fecha_larga(ahora.date(), con_dia_semana=True))
        self._reloj_job = self.root.after(1000, self._tic)

    # -- errores / cierre ----------------------------------------------------

    def _mostrar_error(self, texto):
        self.error.config(text=texto if texto else " ", fg=RED if texto else CARD)

    def cerrar(self):
        for job in (self._numero_job, self._barra_job, self._reloj_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
        self.root.destroy()


# ----------------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------------

def main():
    global FAMILY
    _usar_tk_moderno()
    root = tk.Tk()
    FAMILY = elegir_familia(root)

    root.title("Calendario · Cuenta regresiva")
    try:
        root.tk.call("tk::unsupported::MacWindowStyle", "appearance",
                     root._w, "darkaqua")
    except tk.TclError:
        pass

    ancho_pantalla = root.winfo_screenwidth()
    alto_pantalla = root.winfo_screenheight()
    ancho = min(1260, ancho_pantalla - 100)
    alto = min(800, alto_pantalla - 130)
    x = (ancho_pantalla - ancho) // 2
    y = max(30, (alto_pantalla - alto) // 3)
    root.geometry(f"{ancho}x{alto}+{x}+{y}")
    root.minsize(1020, 740)

    app = CalendarApp(root)
    root.bind("<Left>", lambda e: app._al_pulsar_flecha(-1))
    root.bind("<Right>", lambda e: app._al_pulsar_flecha(1))
    root.protocol("WM_DELETE_WINDOW", app.cerrar)
    root.mainloop()


if __name__ == "__main__":
    main()
