# ══════════════════════════════════════════════════════════════════════════════
# app_estudiante.py — Dashboard Línea 123 · Sesión 29 · Streamlit
# Visualización I · Ciencia de Datos · Universidad Externado de Colombia
#
# Este archivo es una versión de trabajo del app.py del curso.
# Contiene dos secciones marcadas con # TODO que deben completarse.
#
# Las secciones completas funcionan correctamente — no modificarlas.
# Solo completar lo indicado en cada TODO.
#
# Uso local (Colab):
#   %%writefile app_estudiante.py  ← pegar este contenido
#   !streamlit run app_estudiante.py &
# ══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Línea 123 Bogotá · Q4 2025",
    page_icon="🚨",
    layout="wide",
)

st.markdown(
    """
    <style>
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="block-container"] {
        background-color: #F0F2F6 !important;
        color: #333333 !important;
    }
    [data-testid="stSidebar"] { background-color: #E4E7EF !important; }
    [data-testid="stSidebar"] * { color: #333333 !important; }
    h1, h2, h3, p, span, label, div { color: #333333 !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #333333 !important; }
    .stCaption, [data-testid="stCaptionContainer"] { color: #666666 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Paleta y funciones auxiliares ─────────────────────────────────────────────
AZUL_BOGOTA   = '#225495'
GRIS_CONTEXTO = '#B0B0B0'

COLORES_PRIORIDAD = {
    'Crítica': '#AA1023',
    'Alta':    '#C0392B',
    'Media':   '#F7B325',
    'Baja':    '#B0B0B0',
}
ORDEN_PRIORIDAD = ['Baja', 'Media', 'Alta', 'Crítica']

COLORES_GENERO = {
    'Femenino':  '#225495',
    'Masculino': '#4E6FA3',
}

ORDEN_GRUPO_EDAD = [
    'Primera infancia (0-5)', 'Infancia (6-11)', 'Adolescencia (12-17)',
    'Juventud (18-28)', 'Adultez (29-59)', 'Persona mayor (60 o más)',
    'Sin información',
]

ORDEN_DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']

def fmt_col(valor):
    return f'{int(valor):,}'.replace(',', '.')

def fmt_col_dec(valor, decimales=1):
    texto = f'{valor:,.{decimales}f}'
    return texto.replace(',', '@').replace('.', ',').replace('@', '.')

PLANTILLA_CURSO = go.layout.Template(
    layout=go.Layout(
        font=dict(family='Segoe UI, sans-serif', size=12, color='#333333'),
        title=dict(font=dict(size=14)),
        plot_bgcolor='white', paper_bgcolor='white',
        separators=',.',
        xaxis=dict(gridcolor='#E0E0E0', gridwidth=0.5, linecolor='#CCCCCC',
                   linewidth=0.5, tickfont=dict(color='#666666')),
        yaxis=dict(gridcolor='#E0E0E0', gridwidth=0.5, linecolor='#CCCCCC',
                   linewidth=0.5, tickfont=dict(color='#666666')),
    )
)

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data
def cargar_datos(ruta: str) -> pd.DataFrame:
    df = pd.read_parquet(ruta)

    # Variables categóricas temporales.
    # Nota: no se deduplica por NUMERO_INCIDENTE porque un incidente puede
    # involucrar varias personas. Cada fila representa una persona atendida.
    DIAS_EN_ES = {
        'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
        'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado',
        'Sunday': 'domingo',
    }
    df['DIA_SEMANA'] = (
        df['FECHA_INICIO_DESPLAZAMIENTO_MOVIL'].dt.day_name().map(DIAS_EN_ES)
    )
    df['DIA_SEMANA'] = pd.Categorical(
        df['DIA_SEMANA'], categories=ORDEN_DIAS, ordered=True
    )

    MESES_ES = {10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['MES'] = df['FECHA_INICIO_DESPLAZAMIENTO_MOVIL'].dt.month.map(MESES_ES)
    ORDEN_MESES = ['Octubre', 'Noviembre', 'Diciembre']
    df['MES'] = pd.Categorical(df['MES'], categories=ORDEN_MESES, ordered=True)

    if df['FECHA'].dtype != 'object':
        df['FECHA'] = pd.to_datetime(df['FECHA']).dt.date

    def edad_a_anios(row):
        if pd.isna(row['EDAD']) or pd.isna(row['UNIDAD']): return np.nan
        if row['UNIDAD'] == 'Años':   return row['EDAD']
        elif row['UNIDAD'] == 'Meses': return row['EDAD'] // 12
        elif row['UNIDAD'] == 'Días':  return row['EDAD'] // 365
        elif row['UNIDAD'] == 'Horas': return 0
        return np.nan

    def asignar_grupo(edad):
        if pd.isna(edad): return 'Sin información'
        elif edad <= 5:   return 'Primera infancia (0-5)'
        elif edad <= 11:  return 'Infancia (6-11)'
        elif edad <= 17:  return 'Adolescencia (12-17)'
        elif edad <= 28:  return 'Juventud (18-28)'
        elif edad <= 59:  return 'Adultez (29-59)'
        else:             return 'Persona mayor (60 o más)'

    df['EDAD_ANIOS'] = df.apply(edad_a_anios, axis=1)
    df['GRUPO_EDAD'] = df['EDAD_ANIOS'].apply(asignar_grupo)
    df['GRUPO_EDAD'] = pd.Categorical(
        df['GRUPO_EDAD'], categories=ORDEN_GRUPO_EDAD, ordered=True
    )
    return df


RUTA_PARQUET = 'llamadas123_limpio.parquet'

try:
    df_total = cargar_datos(RUTA_PARQUET)
except FileNotFoundError:
    st.error("No se encontró el archivo Parquet. Verificar la ruta.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 · CONTROLES (SIDEBAR)
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("# 🏙️")
    st.markdown("## Línea 123 · Bogotá")
    st.divider()

    meses_disponibles = ['Todos'] + list(df_total['MES'].cat.categories)
    mes_sel = st.selectbox("📅 Mes", options=meses_disponibles)

    prioridades_disponibles = ['Todas'] + ORDEN_PRIORIDAD[::-1]
    prioridad_sel = st.selectbox("🚨 Prioridad", options=prioridades_disponibles)

    dias_disponibles = ['Todos'] + ORDEN_DIAS
    dia_sel = st.selectbox("📆 Día de la semana", options=dias_disponibles)

    # ══════════════════════════════════════════════════════════════════════════
    # TODO 1 · Agregar un tercer control: filtro por día de la semana
    #
    # Objetivo: permitir que el usuario filtre todas las gráficas por un día
    # específico de la semana, o ver todos los días juntos.
    #
    # Instrucciones:
    #   1. Construir la lista de opciones: 'Todos' + los días en orden correcto.
    #      La variable ORDEN_DIAS (definida arriba) contiene el orden correcto.
    #   2. Crear el selectbox con etiqueta "📆 Día de la semana".
    #      Guardar el valor seleccionado en la variable: dia_sel
    #   3. Revisar cómo se construyeron mes_sel y prioridad_sel arriba
    #      para replicar el mismo patrón.
    #
    # Pista: la columna del DataFrame que se usará en el filtro es DIA_SEMANA.
    # ══════════════════════════════════════════════════════════════════════════

    # --- Escribir el código aquí ---

    dia_sel = 'Todos'   # ← reemplazar esta línea con el selectbox correcto

    st.divider()
    st.caption("Fuente: Datos Abiertos Bogotá · datos.gov.co · Q4 2025")

# ── Aplicar filtros ───────────────────────────────────────────────────────────
# Cada condición reduce el DataFrame antes de construir las gráficas.
# Esta es la diferencia central entre Streamlit y Plotly updatemenus:
# aquí los datos se recalculan; en Plotly solo se ocultaban trazas.

df = df_total.copy()
if mes_sel != 'Todos':
    df = df[df['MES'] == mes_sel]
if prioridad_sel != 'Todas':
    df = df[df['PRIORIDAD_FINAL'] == prioridad_sel]

# ══════════════════════════════════════════════════════════════════════════════
# TODO 2 · Agregar el filtro por día al bloque de aplicación de filtros
#          y construir un subtítulo dinámico
#
# Parte A — Filtro:
#   Agregar una condición if que filtre df por DIA_SEMANA cuando
#   dia_sel sea distinto de 'Todos'. Seguir el mismo patrón de
#   mes_sel y prioridad_sel arriba.
#
# Parte B — Subtítulo dinámico:
#   El subtítulo debe cambiar según el día seleccionado:
#   - Si dia_sel == 'Todos': "Octubre a diciembre de 2025"
#   - Si se seleccionó un día: "<Día capitalizado> · Octubre a diciembre de 2025"
#   Guardar el subtítulo en la variable: subtitulo
#
# Pista para capitalizar: Python tiene el método .capitalize() para strings.
# Ejemplo: 'viernes'.capitalize() → 'Viernes'
# ══════════════════════════════════════════════════════════════════════════════

# --- Escribir el código aquí (Parte A: filtro) ---
if dia_sel != 'Todos': 
    df = df[df['DIA_SEMANA'] == dia_sel]

# --- Escribir el código aquí (Parte B: subtítulo) ---
if dia_sel == 'Todos':
    subtitulo = "Octubre a diciembre de 2025"
else:
    # Capitaliza el día seleccionado y lo concatena con el periodo
    subtitulo = f"{dia_sel.capitalize()} · Octubre a diciembre de 2025"

# ── Encabezado ────────────────────────────────────────────────────────────────
st.markdown("## 8 de cada 10 emergencias en Bogotá son de prioridad alta o crítica")
st.markdown(f"**{subtitulo}**")
st.caption(
    "Los controles del panel izquierdo filtran simultáneamente las cuatro gráficas. "
    "Compare con el dashboard de Power BI: el comportamiento es equivalente al de los slicers."
)

# ── KPIs ──────────────────────────────────────────────────────────────────────
# Un incidente puede involucrar varias personas, por lo que el DataFrame
# tiene más filas que incidentes únicos. Para contar incidentes se usa
# nunique() sobre NUMERO_INCIDENTE, que ignora las filas repetidas del
# mismo incidente.
total_incidentes = df['NUMERO_INCIDENTE'].nunique()
pct_critica_alta = (
    df[df['PRIORIDAD_FINAL'].isin(['Crítica', 'Alta'])].shape[0] / len(df) * 100
    if len(df) > 0 else 0
)
localidad_top = (
    df[~df['LOCALIDAD'].isin(['Sin información', 'Fuera de Bogotá'])]
    ['LOCALIDAD'].value_counts().idxmax()
    if len(df) > 0 else '—'
)

col1, col2, col3 = st.columns(3)
col1.metric("Total incidentes", fmt_col(total_incidentes))
col2.metric("Prioridad Crítica o Alta", f"{fmt_col_dec(pct_critica_alta)}%")
col3.metric("Localidad con más incidentes", localidad_top)

st.divider()

if len(df) == 0:
    st.warning("El filtro seleccionado no produce registros. Ajustar los controles.")
    st.stop()

# ── Datos compartidos ─────────────────────────────────────────────────────────
EXCLUIR_LOC = ['Sin información', 'Fuera de Bogotá']

loc_top7 = (
    df[~df['LOCALIDAD'].isin(EXCLUIR_LOC)]
    ['LOCALIDAD'].value_counts().head(7).reset_index()
)
loc_top7.columns = ['LOCALIDAD', 'INCIDENTES']
loc_top7 = loc_top7.iloc[::-1].reset_index(drop=True)

colores_barra = [
    AZUL_BOGOTA if loc in loc_top7['LOCALIDAD'].tail(3).values else GRIS_CONTEXTO
    for loc in loc_top7['LOCALIDAD']
]

n_dias = df['FECHA'].nunique()
# Conteo distintivo de incidentes por hora — no personas.
prom_hora = (
    df.groupby('HORA')['NUMERO_INCIDENTE'].nunique()
    .reset_index(name='TOTAL')
)
prom_hora['PROMEDIO'] = (prom_hora['TOTAL'] / n_dias).round(1)
hora_pico = prom_hora.loc[prom_hora['PROMEDIO'].idxmax()]

# ── Fila superior ─────────────────────────────────────────────────────────────
col_izq, col_der = st.columns(2)

with col_izq:
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=loc_top7['INCIDENTES'], y=loc_top7['LOCALIDAD'],
        orientation='h', marker_color=colores_barra,
        text=[fmt_col(v) for v in loc_top7['INCIDENTES']],
        textposition='outside', textfont=dict(size=10),
        hovertemplate='<b>%{y}</b><br>Personas atendidas: %{text}<extra></extra>',
    ))
    fig1.update_layout(
        template=PLANTILLA_CURSO,
        title=dict(
            text=('<b>Kennedy, Engativá y Suba concentran el 34% de las personas atendidas</b>'
                  '<br><sup>Personas involucradas en incidentes por localidad · '
                  '7 localidades principales (61%)</sup>'),
            font=dict(size=13), x=0, xanchor='left', pad=dict(l=10),
        ),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                   range=[0, loc_top7['INCIDENTES'].max() * 1.35]),
        yaxis=dict(tickfont=dict(size=10), automargin=True, ticklabelstandoff=8),
        showlegend=False, height=380,
        margin=dict(t=90, b=40, l=10, r=30),
        plot_bgcolor='white', paper_bgcolor='white',
    )
    st.plotly_chart(fig1, use_container_width=True)

with col_der:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=prom_hora['HORA'], y=prom_hora['PROMEDIO'],
        mode='lines+markers',
        line=dict(color=AZUL_BOGOTA, width=2),
        marker=dict(size=4, color=AZUL_BOGOTA),
        hovertemplate='<b>Hora %{x}:00</b><br>Promedio: %{y} inc./día<extra></extra>',
        showlegend=False,
    ))
    fig2.add_trace(go.Scatter(
        x=[hora_pico['HORA']], y=[hora_pico['PROMEDIO']],
        mode='markers+text',
        marker=dict(size=10, color='#AA1023'),
        text=[fmt_col_dec(hora_pico['PROMEDIO'], 0)],
        textposition='top center', textfont=dict(size=11, color='#AA1023'),
        showlegend=False, hoverinfo='skip',
    ))
    fig2.update_layout(
        template=PLANTILLA_CURSO,
        title=dict(
            text=('<b>En promedio, cada día registra su pico de demanda entre las 10 y las 11 a.m.</b>'
                  '<br><sup>Promedio de incidentes por hora del día</sup>'),
            font=dict(size=13), x=0, xanchor='left', pad=dict(l=10),
        ),
        xaxis=dict(tickfont=dict(size=10), dtick=4, range=[-0.5, 23.5],
                   title=dict(text='Hora del día', font=dict(size=11, color='#666666'))),
        yaxis=dict(tickfont=dict(size=10), automargin=True, rangemode='tozero'),
        showlegend=False, height=380,
        margin=dict(t=90, b=60, l=10, r=30),
        plot_bgcolor='white', paper_bgcolor='white',
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Fila inferior ─────────────────────────────────────────────────────────────
col_izq2, col_der2 = st.columns(2)

with col_izq2:
    top_tipos = df['TIPO_INCIDENTE'].value_counts().head(6).index.tolist()
    df_tipo = df[df['TIPO_INCIDENTE'].isin(top_tipos)]
    tabla_tipo = pd.crosstab(
        df_tipo['TIPO_INCIDENTE'], df_tipo['PRIORIDAD_FINAL'], normalize='index'
    ) * 100
    for p in ['Crítica', 'Alta', 'Media', 'Baja']:
        if p not in tabla_tipo.columns: tabla_tipo[p] = 0.0
    tabla_tipo = tabla_tipo[['Crítica', 'Alta', 'Media', 'Baja']]
    critica_alta_abs = (
        df_tipo[df_tipo['PRIORIDAD_FINAL'].isin(['Crítica', 'Alta'])]
        .groupby('TIPO_INCIDENTE').size()
        .reindex(tabla_tipo.index, fill_value=0)
    )
    tabla_tipo = tabla_tipo.loc[critica_alta_abs.sort_values(ascending=True).index]
    orden_tipos = tabla_tipo.index.tolist()

    fig3 = go.Figure()
    for prioridad, color, mostrar in [
        ('Crítica', COLORES_PRIORIDAD['Crítica'], True),
        ('Alta',    COLORES_PRIORIDAD['Alta'],    True),
        ('Media',   COLORES_PRIORIDAD['Media'],   False),
        ('Baja',    COLORES_PRIORIDAD['Baja'],    False),
    ]:
        valores = [tabla_tipo.loc[t, prioridad] for t in orden_tipos]
        fig3.add_trace(go.Bar(
            name=prioridad, x=valores, y=orden_tipos, orientation='h',
            marker_color=color,
            text=[f'{v:.0f}%' if (mostrar and v >= 7) else '' for v in valores],
            textposition='inside', insidetextanchor='middle',
            textfont=dict(size=10, color='white'),
            customdata=[fmt_col_dec(v, 1) for v in valores],
            hovertemplate='<b>%{y}</b><br>' + prioridad + ': %{customdata}%<extra></extra>',
        ))
    fig3.update_layout(
        template=PLANTILLA_CURSO, barmode='stack',
        title=dict(
            text=('<b>El 80% de los tipos de atención principales se clasifican '
                  'con prioridad crítica o alta</b>'
                  '<br><sup>Distribución de prioridad por tipo de atención · '
                  '6 tipos principales (72%)</sup>'),
            font=dict(size=13), x=0, xanchor='left', pad=dict(l=10),
        ),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, 105]),
        yaxis=dict(tickfont=dict(size=10), automargin=True, ticklabelstandoff=10,
                   categoryorder='array', categoryarray=orden_tipos),
        legend=dict(orientation='h', y=-0.15, x=0,
                    title=dict(text='Prioridad final:', font=dict(size=11)),
                    font=dict(size=11), traceorder='normal'),
        height=400, margin=dict(t=110, b=80, l=10, r=30),
        plot_bgcolor='white', paper_bgcolor='white',
    )
    st.plotly_chart(fig3, use_container_width=True)

with col_der2:
    df_demo = df[(df['GRUPO_EDAD'] != 'Sin información') & (df['GENERO'].notna())]
    tabla_edad = pd.crosstab(
        df_demo['GRUPO_EDAD'], df_demo['GENERO'], normalize='index'
    ) * 100
    orden_invertido = [g for g in reversed(ORDEN_GRUPO_EDAD) if g != 'Sin información']
    tabla_edad = tabla_edad.reindex(orden_invertido)
    for g in ['Femenino', 'Masculino']:
        if g not in tabla_edad.columns: tabla_edad[g] = 0.0
    tabla_edad_long = tabla_edad.reset_index().melt(
        id_vars='GRUPO_EDAD', var_name='GENERO', value_name='PORCENTAJE'
    )
    tabla_edad_long['PORCENTAJE_FMT'] = tabla_edad_long['PORCENTAJE'].apply(
        lambda v: fmt_col_dec(v, 1)
    )
    fig4 = px.bar(
        tabla_edad_long, x='PORCENTAJE', y='GRUPO_EDAD',
        color='GENERO', orientation='h',
        color_discrete_map=COLORES_GENERO,
        category_orders={'GENERO': ['Femenino', 'Masculino'], 'GRUPO_EDAD': orden_invertido},
        barmode='stack', text='PORCENTAJE', custom_data=['PORCENTAJE_FMT'],
    )
    fig4.update_traces(
        texttemplate='%{text:.0f}%', textposition='inside',
        insidetextanchor='middle', textfont=dict(size=10, color='white'),
        hovertemplate='<b>%{y}</b><br>%{fullData.name}: %{customdata[0]}%<extra></extra>',
    )
    # Masculino (#4E6FA3) es azul intermedio: se fuerza texto blanco
    # explícitamente para esa traza con selector por nombre.
    fig4.update_traces(
        textfont=dict(size=10, color='white'),
        selector=dict(name='Masculino'),
    )
    fig4.update_layout(
        template=PLANTILLA_CURSO,
        title=dict(
            text=('<b>Las personas mayores y los adultos concentran el 68% '
                '<br>de las emergencias con datos demográficos completos</b>'
                  '<br><sup>Distribución por grupo de edad y género</sup>'),
            font=dict(size=13), x=0, xanchor='left', pad=dict(l=10),
        ),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                   range=[0, 105], title=dict(text='')),
        yaxis=dict(tickfont=dict(size=10), automargin=True, ticklabelstandoff=8,
                   title=dict(text='Grupo de edad', font=dict(size=11, color='#666666'))),
        legend=dict(orientation='h', y=-0.15, x=0,
                    title=dict(text='Género:', font=dict(size=11)), font=dict(size=11)),
        height=400, margin=dict(t=110, b=80, l=10, r=30),
        plot_bgcolor='white', paper_bgcolor='white',
    )
    st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.caption("Fuente: Datos Abiertos Bogotá · datos.gov.co · Línea 123 · Octubre–Diciembre 2025.")
