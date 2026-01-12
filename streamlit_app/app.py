import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import sys
import os
from scipy import stats

# === FUNCIONES AUXILIARES ===
def get_intensidad(corr: float) -> str:
    abs_corr = abs(corr)
    if abs_corr >= 0.7: return "FUERTE"
    elif abs_corr >= 0.4: return "MODERADA"
    elif abs_corr >= 0.2: return "DÉBIL"
    else: return "NULA"

def interpretar_correlacion(corr: float):
    st.write("### Interpretación:")
    if abs(corr) >= 0.7:
        st.success(f"🔴 **Correlación {'POSITIVA' if corr > 0 else 'NEGATIVA'} FUERTE**")
    elif abs(corr) >= 0.4:
        st.info(f"🟡 **Correlación {'POSITIVA' if corr > 0 else 'NEGATIVA'} MODERADA**")
    elif abs(corr) >= 0.2:
        st.warning(f"🟢 **Correlación {'POSITIVA' if corr > 0 else 'NEGATIVA'} DÉBIL**")
    else:
        st.error("⚪ **Correlación NULA o INEXISTENTE**")

def safe_numeric_columns(df: pd.DataFrame) -> list:
    return df.select_dtypes(include=['number']).columns.tolist()

def label_probabilidad(p: float) -> str:
    if p == 0: return "Imposible"
    elif p < 0.1: return "Muy poco probable"
    elif p < 0.3: return "Poco probable"
    elif p < 0.6: return "Probable"
    elif p < 0.9: return "Muy probable"
    else: return "Casi seguro"

# Agregar utils al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from db_connector import obtener_pedidos

# Configuración de página
st.set_page_config(
    page_title="Dashboard Gaseosas - Reparto",
    page_icon="🥤",
    layout="wide"
)

st.title("Dashboard de Reparto - GRUPO JUYO")

# Cargar datos desde Supabase
with st.spinner('Conectando a Supabase...'):
    datos = obtener_pedidos()

if not datos:
    st.error("No se encontraron datos en la tabla 'pedidos'")
    st.stop()

df = pd.DataFrame(datos)
st.success(f"Conectado a Supabase | {len(df)} registros cargados")

# Sidebar con filtros
st.sidebar.header("Rutas")
rutas = df['ruta'].unique() if 'ruta' in df.columns else []
ruta_seleccionada = st.sidebar.multiselect(
    "Selecciona Ruta(s):",
    options=rutas,
    default=rutas
)

# Filtrar dataframe
df_filtrado = df[df['ruta'].isin(ruta_seleccionada)] if len(ruta_seleccionada) > 0 else df

# PESTAÑAS PRINCIPALES
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Estadística descriptiva",
    "Estadística inferencial",
    "Probabilidad",
    "Distribución normal",
    "Datos brutos"
])

# === PESTAÑA 1: ESTADÍSTICA DESCRIPTIVA ===
with tab1:
    st.header("Estadística descriptiva")

    if df_filtrado.empty:
        st.warning("No hay datos para mostrar. Ajusta los filtros.")
    else:
        vars_num = safe_numeric_columns(df_filtrado)
        if len(vars_num) == 0:
            st.error("No se encontraron variables numéricas en los datos filtrados.")
        else:
            var_desc = st.selectbox("Variable para resumen", vars_num, index=0, key="desc_var")

            colA, colB, colC = st.columns(3)
            with colA:
                st.subheader("Tendencia central")
                st.metric("Media", f"{df_filtrado[var_desc].mean():,.3f}")
                st.metric("Mediana", f"{df_filtrado[var_desc].median():,.3f}")
                moda = df_filtrado[var_desc].mode()
                st.metric("Moda", f"{moda.iloc[0]:,.3f}" if not moda.empty else "—")

            with colB:
                st.subheader("Dispersión")
                st.metric("Varianza", f"{df_filtrado[var_desc].var():,.3f}")
                st.metric("Desv. estándar", f"{df_filtrado[var_desc].std():,.3f}")
                rango = df_filtrado[var_desc].max() - df_filtrado[var_desc].min()
                st.metric("Rango", f"{rango:,.3f}")

            with colC:
                st.subheader("Posición relativa")
                st.metric("Percentil 25", f"{df_filtrado[var_desc].quantile(0.25):,.3f}")
                st.metric("Percentil 50", f"{df_filtrado[var_desc].quantile(0.50):,.3f}")
                st.metric("Percentil 75", f"{df_filtrado[var_desc].quantile(0.75):,.3f}")

            col1, col2 = st.columns(2)
            with col1:
                fig_box = px.box(df_filtrado, y=var_desc, title=f"Boxplot de {var_desc}")
                st.plotly_chart(fig_box, use_container_width=True, key="desc_box")
            with col2:
                fig_hist = px.histogram(df_filtrado, x=var_desc, nbins=30, title=f"Histograma de {var_desc}")
                st.plotly_chart(fig_hist, use_container_width=True, key="desc_hist")

# === PESTAÑA 2: ESTADÍSTICA INFERENCIAL ===
with tab2:
    st.header("Estadística inferencial")

    if df_filtrado.empty:
        st.warning("No hay datos para análisis inferencial. Ajusta los filtros.")
    else:
        vars_num = safe_numeric_columns(df_filtrado)
        if len(vars_num) < 2:
            st.error("Se requieren al menos dos variables numéricas para correlaciones.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                var_x = st.selectbox("Variable X", vars_num, key='inf_x')
            with col2:
                var_y = st.selectbox("Variable Y", vars_num, index=1 if len(vars_num) > 1 else 0, key='inf_y')
            with col3:
                metodo = st.selectbox("Método de correlación", ["pearson", "spearman", "kendall"], key='inf_metodo')

            if var_x != var_y:
                corr = df_filtrado[var_x].corr(df_filtrado[var_y], method=metodo)
                st.metric(
                    label=f"Correlación ({metodo.capitalize()})",
                    value=f"{corr:.3f}",
                    delta=f"Intensidad: {get_intensidad(corr)}"
                )
                interpretar_correlacion(corr)

                fig = px.scatter(
                    df_filtrado,
                    x=var_x, y=var_y,
                    color='estado_entrega' if 'estado_entrega' in df_filtrado.columns else None,
                    title=f"Correlación {metodo.capitalize()}: {corr:.3f}",
                    trendline="ols" if metodo == "pearson" else None
                )
                st.plotly_chart(fig, use_container_width=True, key="corr_scatter")
            else:
                st.warning("⚠️ Selecciona variables diferentes")

# === PESTAÑA 3: PROBABILIDAD ===
with tab3:
    st.header("Probabilidad de eventos")

    if df_filtrado.empty:
        st.warning("No hay datos para calcular probabilidades. Ajusta los filtros.")
    else:
        if 'estado_entrega' in df_filtrado.columns:
            frec_rel = df_filtrado['estado_entrega'].value_counts(normalize=True)
            if not frec_rel.empty:
                df_prob = frec_rel.reset_index()
                df_prob.columns = ['estado_entrega', 'probabilidad']
                df_prob['clasificación'] = df_prob['probabilidad'].apply(label_probabilidad)

                st.subheader("Probabilidad por estado de entrega")
                st.dataframe(df_prob)

                fig_pie = px.pie(
                    df_prob,
                    values='probabilidad',
                    names='estado_entrega',
                    title="Probabilidad de estados de entrega"
                )
                st.plotly_chart(fig_pie, use_container_width=True, key="prob_pie")
            else:
                st.info("No hay estados de entrega para los filtros actuales.")
        else:
            st.info("No se encontró la columna 'estado_entrega' para calcular probabilidades.")

# === PESTAÑA 4: DISTRIBUCIÓN NORMAL ===
with tab4:
    st.header("Distribución normal y pruebas de normalidad")

    if df_filtrado.empty:
        st.warning("No hay datos para analizar distribución. Ajusta los filtros.")
    else:
        vars_num = safe_numeric_columns(df_filtrado)
        if len(vars_num) == 0:
            st.error("No se encontraron variables numéricas en los datos filtrados.")
        else:
            var_norm = st.selectbox("Variable numérica", vars_num, key='norm_var')
            serie = df_filtrado[var_norm].dropna()

            col1, col2 = st.columns(2)
            with col1:
                fig_hist = px.histogram(df_filtrado, x=var_norm, nbins=30, title=f"Histograma de {var_norm}")
                st.plotly_chart(fig_hist, use_container_width=True, key="norm_hist")
            with col2:
                fig_box = px.box(df_filtrado, y=var_norm, title=f"Boxplot de {var_norm}")
                st.plotly_chart(fig_box, use_container_width=True, key="norm_box")

            # Prueba de normalidad (Shapiro-Wilk)
            if len(serie) >= 3:
                stat, p_val = stats.shapiro(serie.sample(min(len(serie), 5000), random_state=42))
                st.subheader("Prueba de normalidad (Shapiro-Wilk)")
                st.metric("Estadístico", f"{stat:.3f}")
                st.metric("p-valor", f"{p_val:.4f}")
                st.info("Interpretación: si p < 0.05, se rechaza la hipótesis de normalidad al 95%.")
            else:
                st.warning("No hay suficientes datos para la prueba de normalidad (mínimo 3).")

# === PESTAÑA 5: DATOS BRUTOS ===
with tab5:
    st.header("Vista de datos")
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar. Ajusta los filtros.")
    else:
        st.dataframe(df_filtrado)