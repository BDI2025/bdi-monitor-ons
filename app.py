import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.font_manager as fm
import urllib.request
import os
import numpy as np
import pyxirr
import requests
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA BDI
# ==========================================
st.set_page_config(page_title="Monitor ONs | BDI Consultora", layout="wide", page_icon="📈")

C_VERDE_OSC = '#137247'
C_GRIS_OSC = '#323232'
C_CREMA = '#EFEDEA'
C_CYAN = '#17BEBB'
C_LIMA = '#B5E61D'

@st.cache_resource
def cargar_fuente():
    font_url = 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf'
    font_bold_url = 'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf'
    if not os.path.exists('Poppins-Regular.ttf'):
        urllib.request.urlretrieve(font_url, 'Poppins-Regular.ttf')
    if not os.path.exists('Poppins-Bold.ttf'):
        urllib.request.urlretrieve(font_bold_url, 'Poppins-Bold.ttf')
    fm.fontManager.addfont('Poppins-Regular.ttf')
    fm.fontManager.addfont('Poppins-Bold.ttf')
    plt.rcParams['font.family'] = 'Poppins'

cargar_fuente()

# ==========================================
# 2. CONEXIÓN A LAS APIS (Data912 y Dólar)
# ==========================================
def obtener_dolar_mep():
    try:
        url = "https://dolarapi.com/v1/dolares/bolsa"
        respuesta = requests.get(url).json()
        return respuesta["venta"]
    except Exception as e:
        st.error(f"⚠️ Error MEP: {e}")
        return 1040.0

def descargar_panel_data912():
    precios = {}
    try:
        url = "https://data912.com/live/arg_corp"
        headers = {'Accept': 'application/json'}
        respuesta = requests.get(url, headers=headers)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            for item in datos:
                ticker = item.get("symbol")
                precio = item.get("c")
                if ticker and precio:
                    precios[ticker] = float(precio)
        else:
            st.error(f"⚠️ Error Data912 HTTP: {respuesta.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error conectando a Data912: {e}")
    return precios

# ==========================================
# 3. BASE DE DATOS MAESTRA (Con Tickers)
# ==========================================
bonos_maestros = {
    "TLCP": {"ars": "TLCPO", "usd": "TLCPD", "fechas": [date(2025, 5, 28), date(2025, 11, 28), date(2026, 5, 28), date(2026, 11, 28), date(2027, 5, 28), date(2027, 11, 28), date(2028, 5, 28), date(2028, 11, 28), date(2029, 5, 28), date(2029, 11, 28), date(2030, 5, 28), date(2030, 11, 28), date(2031, 5, 28), date(2031, 11, 28), date(2032, 5, 28), date(2032, 11, 28), date(2033, 5, 28)], "flujos": [0.00, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 54.63, 2.31, 52.31]},
    "IRCP": {"ars": "IRCPO", "usd": "IRCPD", "fechas": [date(2025, 3, 31), date(2025, 9, 30), date(2026, 3, 31), date(2026, 9, 30), date(2027, 3, 31), date(2027, 9, 30), date(2028, 3, 31), date(2028, 9, 30), date(2029, 3, 31), date(2029, 9, 30), date(2030, 3, 31), date(2030, 9, 30), date(2031, 3, 31), date(2031, 9, 30), date(2032, 3, 31), date(2032, 9, 30), date(2033, 3, 31), date(2033, 9, 30), date(2034, 3, 31), date(2034, 9, 30), date(2035, 3, 31)], "flujos": [0.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 37.00, 2.68, 35.68, 1.36, 35.36]},
    "VSCV": {"ars": "VSCVO", "usd": "VSCVD", "fechas": [date(2025, 6, 10), date(2025, 12, 10), date(2026, 6, 10), date(2026, 12, 10), date(2027, 6, 10), date(2027, 12, 10), date(2028, 6, 10), date(2028, 12, 10), date(2029, 6, 10), date(2029, 12, 10), date(2030, 6, 10), date(2030, 12, 10), date(2031, 6, 10), date(2031, 12, 10), date(2032, 6, 10), date(2032, 12, 10), date(2033, 6, 10)], "flujos": [0.00, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 37.25, 2.85, 35.85, 1.45, 35.45]},
    "PLC5": {"ars": "PLC5O", "usd": "PLC5D", "fechas": [date(2025, 11, 18), date(2026, 5, 18), date(2026, 11, 18), date(2027, 5, 18), date(2027, 11, 18), date(2028, 5, 18), date(2028, 11, 18), date(2029, 5, 18), date(2029, 11, 18), date(2030, 5, 18), date(2030, 11, 18), date(2031, 5, 18)], "flujos": [0.00, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 104.06]},
    "TSC4": {"ars": "TSC4O", "usd": "TSC4D", "fechas": [date(2025, 11, 20), date(2026, 5, 20), date(2026, 11, 20), date(2027, 5, 20), date(2027, 11, 20), date(2028, 5, 20), date(2028, 11, 20), date(2029, 5, 20), date(2029, 11, 20), date(2030, 5, 20), date(2030, 11, 20), date(2031, 5, 20), date(2031, 11, 20), date(2032, 5, 20), date(2032, 11, 20), date(2033, 5, 20), date(2033, 11, 20), date(2034, 5, 20), date(2034, 11, 20), date(2035, 5, 20), date(2035, 11, 20)], "flujos": [0.00, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 103.88]},
    "MGCO": {"ars": "MGCOO", "usd": "MGCOD", "fechas": [date(2024, 12, 16), date(2025, 6, 16), date(2025, 12, 16), date(2026, 6, 16), date(2026, 12, 16), date(2027, 6, 16), date(2027, 12, 16), date(2028, 6, 16), date(2028, 12, 16), date(2029, 6, 16), date(2029, 12, 16), date(2030, 6, 16), date(2030, 12, 16), date(2031, 6, 16), date(2031, 12, 16), date(2032, 6, 16), date(2032, 12, 16), date(2033, 6, 16), date(2033, 12, 16), date(2034, 6, 16), date(2034, 12, 16)], "flujos": [0.00, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 103.94]},
    "TTCD": {"ars": "TTCDO", "usd": "TTCDD", "fechas": [date(2025, 11, 3), date(2026, 5, 3), date(2026, 11, 3), date(2027, 5, 3), date(2027, 11, 3), date(2028, 5, 3), date(2028, 11, 3), date(2029, 5, 3), date(2029, 11, 3), date(2030, 5, 3), date(2030, 11, 3)], "flujos": [0.00, 3.81, 3.81, 3.81, 3.81, 3.81, 3.81, 3.81, 3.81, 3.81, 103.81]},
    "BACG": {"ars": "BACGO", "usd": "BACGD", "fechas": [date(2025, 6, 23), date(2025, 12, 23), date(2026, 6, 23), date(2026, 12, 23), date(2027, 6, 23), date(2027, 12, 23), date(2028, 6, 23), date(2028, 12, 23), date(2029, 6, 23)], "flujos": [0.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 104.00]}
}

# ==========================================
# 4. MEMORIA DE SESIÓN
# ==========================================
if 'precios_vivo' not in st.session_state:
    st.session_state['precios_vivo'] = {}
    st.session_state['mep_hoy'] = 1040.0

# ==========================================
# 5. INTERFAZ WEB BDI
# ==========================================
st.markdown(f"<h1 style='color: {C_VERDE_OSC}; font-weight: bold;'>BDI Consultora Patrimonial</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color: {C_GRIS_OSC};'>Frontera Eficiente de Obligaciones Negociables</h3>", unsafe_allow_html=True)
st.divider()

# Botón de Descarga Inicial
col_boton, col_info = st.columns([1, 2])
with col_boton:
    if st.button("🔄 1. Descargar Precios Reales en Vivo", type="primary"):
        with st.spinner('Conectando a Data912 y DolarAPI...'):
            st.session_state['mep_hoy'] = obtener_dolar_mep()
            st.session_state['precios_vivo'] = descargar_panel_data912()
        st.success("✅ Datos sincronizados con el mercado.")

# Si ya tenemos datos, mostramos el panel de simulación individual
if st.session_state['precios_vivo']:
    st.divider()
    
    st.markdown(f"<h4 style='color: {C_VERDE_OSC};'>🎛️ 2. Panel de Sensibilidad por Ticker</h4>", unsafe_allow_html=True)
    st.markdown("Ajustá el precio de cada bono de forma independiente para visualizar escenarios puntuales (Ej: impacto de un buen balance en IRCP).")
    
    # Creamos una cuadrícula de 4 columnas para que quede prolijo
    cols = st.columns(4)
    variaciones = {}
    
    # Generamos los ajustadores de porcentaje dinámicamente
    for i, ticker in enumerate(bonos_maestros.keys()):
        with cols[i % 4]:
            variaciones[ticker] = st.number_input(
                f"Variación {ticker} (%)", 
                min_value=-50.0, 
                max_value=50.0, 
                value=0.0, 
                step=0.5,
                key=f"var_{ticker}"
            )
    
    resultados = []
    hoy = date.today()
    mep_hoy = st.session_state['mep_hoy']
    precios_vivo = st.session_state['precios_vivo']
    
    for ticker, info in bonos_maestros.items():
        p_usd_real = precios_vivo.get(info["usd"], 0)
        p_ars_real = precios_vivo.get(info["ars"], 0)
        
        if p_usd_real <= 0: 
            continue
        
        # APLICAMOS LA VARIACIÓN INDIVIDUAL QUE ELIGIÓ EL USUARIO
        var_individual = variaciones[ticker]
        p_usd_simulado = p_usd_real * (1 + (var_individual / 100))
        p_ars_simulado = p_ars_real * (1 + (var_individual / 100))
        
        precio_inversion_usd = p_usd_simulado * 100 if p_usd_simulado < 10 else p_usd_simulado
        dolar_cable = p_ars_simulado / p_usd_simulado if p_usd_simulado > 0 else 0
        costo_inversion_ars_en_usd = precio_inversion_usd * (dolar_cable / mep_hoy) if mep_hoy else precio_inversion_usd

        fechas_futuras = [f for f in info["fechas"] if f >= hoy]
        flujos_futuros = [info["flujos"][i] for i, f in enumerate(info["fechas"]) if f >= hoy]
        
        if not fechas_futuras: continue
        
        fechas_tir = [hoy] + fechas_futuras
        flujos_tir_usd = [-precio_inversion_usd] + flujos_futuros
        flujos_tir_ars = [-costo_inversion_ars_en_usd] + flujos_futuros
        
        try:
            tir_usd = pyxirr.xirr(fechas_tir, flujos_tir_usd)
            tir_ars = pyxirr.xirr(fechas_tir, flujos_tir_ars)
            
            pv_total, suma_t_pv = 0, 0
            for i in range(len(fechas_futuras)):
                t = (fechas_futuras[i] - hoy).days / 365.0
                pv = flujos_futuros[i] / ((1 + tir_usd) ** t)
                pv_total += pv
                suma_t_pv += (t * pv)
                
            macaulay_duration = suma_t_pv / pv_total
            modified_duration = macaulay_duration / (1 + tir_usd)
            
            resultados.append({
                "Ticker": ticker,
                "Precio ARS (Sim)": round(p_ars_simulado, 2),
                "Precio USD (Sim)": round(precio_inversion_usd, 2),
                "Dólar Implícito": round(dolar_cable, 2),
                "TIR USD (%)": round(tir_usd * 100, 2),
                "TIR ARS (%)": round(tir_ars * 100, 2),
                "Macaulay Duration": round(macaulay_duration, 2),
                "Modified Duration": round(modified_duration, 2)
            })
        except Exception as e:
            st.warning(f"Error calculando {ticker}: {e}")
            continue
            
    if resultados:
        df_resultados = pd.DataFrame(resultados).sort_values(by="TIR USD (%)", ascending=False)
        
        # TABLA
        st.subheader(f"📊 Panel de Rendimientos (Dólar MEP de ref: ${mep_hoy:,.2f})")
        st.dataframe(df_resultados.style.format({
            "Precio ARS (Sim)": "${:,.2f}", 
            "Precio USD (Sim)": "US${:,.2f}", 
            "Dólar Implícito": "${:,.2f}",
            "TIR USD (%)": "{:.2f}%", 
            "TIR ARS (%)": "{:.2f}%", 
            "Macaulay Duration": "{:.2f}",
            "Modified Duration": "{:.2f}"
        }), use_container_width=True)
        
        # GRÁFICO
        st.subheader("📈 Curva de Riesgo/Retorno (Escenario Personalizado)")
        fig, ax = plt.subplots(figsize=(12, 7))
        
        x = df_resultados["Modified Duration"]
        y = df_resultados["TIR USD (%)"]

        plt.scatter(x, y, color=C_CYAN, s=160, edgecolor=C_VERDE_OSC, linewidth=1.5, zorder=5, label='ONs')

        if len(x) > 2:
            z = np.polyfit(x, y, 2)
            p = np.poly1d(z)
            x_trend = np.linspace(min(x), max(x), 100)
            plt.plot(x_trend, p(x_trend), color=C_LIMA, linestyle='--', linewidth=3, zorder=4, alpha=0.9, label='Curva de Rendimiento')

        for i, row in df_resultados.iterrows():
            plt.annotate(row["Ticker"], 
                         (row["Modified Duration"], row["TIR USD (%)"]),
                         textcoords="offset points", 
                         xytext=(0,13), 
                         ha='center',
                         fontsize=10,
                         fontweight='bold',
                         color=C_GRIS_OSC,
                         bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.8, pad=1))

        plt.title("Frontera Eficiente: Obligaciones Negociables", fontsize=18, fontweight='bold', color=C_VERDE_OSC, pad=15)
        plt.xlabel("Riesgo (Modified Duration - Años)", fontsize=12, fontweight='bold', color=C_GRIS_OSC)
        plt.ylabel("Retorno (TIR USD)", fontsize=12, fontweight='bold', color=C_GRIS_OSC)

        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
        ax.tick_params(colors=C_GRIS_OSC)
        for spine in ax.spines.values():
            spine.set_edgecolor(C_GRIS_OSC)

        plt.grid(True, color=C_VERDE_OSC, linestyle='-', alpha=0.15, zorder=0)
        plt.legend(loc='best', facecolor=C_CREMA, edgecolor=C_GRIS_OSC, labelcolor=C_GRIS_OSC)
        
        st.pyplot(fig)
