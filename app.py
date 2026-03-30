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
st.set_page_config(page_title="Monitor ONs | BDI", layout="wide", page_icon="📈")

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
# 2. CONEXIÓN A LAS APIS
# ==========================================
def obtener_dolar_mep():
    try:
        url = "https://dolarapi.com/v1/dolares/bolsa"
        respuesta = requests.get(url).json()
        return respuesta["venta"]
    except: return 1040.0

def descargar_panel_data912():
    precios = {}
    try:
        url = "https://data912.com/live/arg_corp"
        headers = {'Accept': 'application/json'}
        respuesta = requests.get(url, headers=headers)
        if respuesta.status_code == 200:
            for item in respuesta.json():
                if item.get("symbol") and item.get("c"):
                    precios[item["symbol"]] = float(item["c"])
    except: pass
    return precios

# ==========================================
# 3. BASE DE DATOS MAESTRA
# ==========================================
bonos_maestros = {
    "TLCP": {
        "ars": "TLCPO", "usd": "TLCPD", 
        "empresa": "Telecom Arg.", "lamina": 1, "ley": "NY", "calificacion": "AA-", 
        "cupon_anual": 9.25, "vr_actual": 100.0,
        "descripcion": "Empresa líder en telecomunicaciones de Argentina. Provee servicios de telefonía, internet y televisión.", 
        "fechas": [date(2025, 5, 28), date(2025, 11, 28), date(2026, 5, 28), date(2026, 11, 28), date(2027, 5, 28), date(2027, 11, 28), date(2028, 5, 28), date(2028, 11, 28), date(2029, 5, 28), date(2029, 11, 28), date(2030, 5, 28), date(2030, 11, 28), date(2031, 5, 28), date(2031, 11, 28), date(2032, 5, 28), date(2032, 11, 28), date(2033, 5, 28)], 
        "flujos": [0.00, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 4.63, 54.63, 2.31, 52.31]
    },
    "IRCP": {
        "ars": "IRCPO", "usd": "IRCPD", 
        "empresa": "IRSA", "lamina": 1, "ley": "NY", "calificacion": "-", 
        "cupon_anual": 8.00, "vr_actual": 100.0,
        "descripcion": "Desarrolladora inmobiliaria (shoppings, oficinas).", 
        "fechas": [date(2025, 3, 31), date(2025, 9, 30), date(2026, 3, 31), date(2026, 9, 30), date(2027, 3, 31), date(2027, 9, 30), date(2028, 3, 31), date(2028, 9, 30), date(2029, 3, 31), date(2029, 9, 30), date(2030, 3, 31), date(2030, 9, 30), date(2031, 3, 31), date(2031, 9, 30), date(2032, 3, 31), date(2032, 9, 30), date(2033, 3, 31), date(2033, 9, 30), date(2034, 3, 31), date(2034, 9, 30), date(2035, 3, 31)], 
        "flujos": [0.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 37.00, 2.68, 35.68, 1.36, 35.36]
    },
    "VSCV": {
        "ars": "VSCVO", "usd": "VSCVD", 
        "empresa": "Vista Energy", "lamina": 1000, "ley": "NY", "calificacion": "-", 
        "cupon_anual": 8.50, "vr_actual": 100.0,
        "descripcion": "Empresa enfocada en exploración y producción de petróleo y gas (Vaca Muerta).", 
        "fechas": [date(2025, 6, 10), date(2025, 12, 10), date(2026, 6, 10), date(2026, 12, 10), date(2027, 6, 10), date(2027, 12, 10), date(2028, 6, 10), date(2028, 12, 10), date(2029, 6, 10), date(2029, 12, 10), date(2030, 6, 10), date(2030, 12, 10), date(2031, 6, 10), date(2031, 12, 10), date(2032, 6, 10), date(2032, 12, 10), date(2033, 6, 10)], 
        "flujos": [0.00, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 37.25, 2.85, 35.85, 1.45, 35.45]
    },
    "PLC5": {
        "ars": "PLC5O", "usd": "PLC5D", 
        "empresa": "Pampa Energía", "lamina": 1000, "ley": "NY", "calificacion": "-", 
        "cupon_anual": 8.12, "vr_actual": 100.0,
        "descripcion": "Generación, transmisión y distribución de energía eléctrica, y gas.", 
        "fechas": [date(2025, 11, 18), date(2026, 5, 18), date(2026, 11, 18), date(2027, 5, 18), date(2027, 11, 18), date(2028, 5, 18), date(2028, 11, 18), date(2029, 5, 18), date(2029, 11, 18), date(2030, 5, 18), date(2030, 11, 18), date(2031, 5, 18)], 
        "flujos": [0.00, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 4.06, 104.06]
    },
    "TSC4": {
        "ars": "TSC4O", "usd": "TSC4D", 
        "empresa": "Tecpetrol", "lamina": 1000, "ley": "NY", "calificacion": "-", 
        "cupon_anual": 7.76, "vr_actual": 100.0,
        "descripcion": "Compañía de energía, enfocada en la exploración y producción de hidrocarburos.", 
        "fechas": [date(2025, 11, 20), date(2026, 5, 20), date(2026, 11, 20), date(2027, 5, 20), date(2027, 11, 20), date(2028, 5, 20), date(2028, 11, 20), date(2029, 5, 20), date(2029, 11, 20), date(2030, 5, 20), date(2030, 11, 20), date(2031, 5, 20), date(2031, 11, 20), date(2032, 5, 20), date(2032, 11, 20), date(2033, 5, 20), date(2033, 11, 20), date(2034, 5, 20), date(2034, 11, 20), date(2035, 5, 20), date(2035, 11, 20)], 
        "flujos": [0.00, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 103.88]
    },
    "MGCO": {
        "ars": "MGCOO", "usd": "MGCOD", 
        "empresa": "CGC", "lamina": 1000, "ley": "NY", "calificacion": "-", 
        "cupon_anual": 7.88, "vr_actual": 100.0,
        "descripcion": "Compañía General de Combustibles.", 
        "fechas": [date(2024, 12, 16), date(2025, 6, 16), date(2025, 12, 16), date(2026, 6, 16), date(2026, 12, 16), date(2027, 6, 16), date(2027, 12, 16), date(2028, 6, 16), date(2028, 12, 16), date(2029, 6, 16), date(2029, 12, 16), date(2030, 6, 16), date(2030, 12, 16), date(2031, 6, 16), date(2031, 12, 16), date(2032, 6, 16), date(2032, 12, 16), date(2033, 6, 16), date(2033, 12, 16), date(2034, 6, 16), date(2034, 12, 16)], 
        "flujos": [0.00, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 3.94, 103.94]
    },
    "TTCD": {
        "ars": "TTCDO", "usd": "TTCDD", 
        "empresa": "Transportadora Gas", "lamina": 1000, "ley": "NY", "calificacion": "-", 
        "cupon_anual": 7.62, "vr_actual": 100.0,
        "descripcion": "Transporte de gas natural.", 
        "fechas": [date(2025, 11, 3), date(2026, 5, 3), date(2026, 11, 3), date(2027, 5, 3), date(2027, 11, 3), date(2028, 5, 3), date(2028, 11, 3), date(2029, 5, 3), date(2029, 11, 3), date(2030, 5, 3), date(2030, 11, 3)], 
        "flujos": [0.00, 3.81, 3.81, 3.81, 3.81, 3.81, 3.81, 3.81, 3.81, 3.81, 103.81]
    },
    "BACG": {
        "ars": "BACGO", "usd": "BACGD", 
        "empresa": "Banco Macro", "lamina": 1000, "ley": "NY", "calificacion": "-", 
        "cupon_anual": 8.00, "vr_actual": 100.0,
        "descripcion": "Entidad bancaria privada de Argentina.", 
        "fechas": [date(2025, 6, 23), date(2025, 12, 23), date(2026, 6, 23), date(2026, 12, 23), date(2027, 6, 23), date(2027, 12, 23), date(2028, 6, 23), date(2028, 12, 23), date(2029, 6, 23)], 
        "flujos": [0.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 104.00]
    }
}

# MEMORIA DE SESIÓN
if 'precios_vivo' not in st.session_state:
    st.session_state['precios_vivo'] = {}
    st.session_state['mep_hoy'] = 1040.0

# ==========================================
# 4. INTERFAZ WEB BDI
# ==========================================
st.markdown(f"<h1 style='color: {C_VERDE_OSC}; font-weight: bold;'>BDI Consultora Patrimonial</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color: {C_GRIS_OSC};'>Frontera Eficiente de Obligaciones Negociables</h3>", unsafe_allow_html=True)
st.divider()

col_boton, col_info = st.columns([1, 2])
with col_boton:
    if st.button("🔄 1. Descargar Precios Reales en Vivo", type="primary"):
        with st.spinner('Conectando a Data912 y DolarAPI...'):
            st.session_state['mep_hoy'] = obtener_dolar_mep()
            st.session_state['precios_vivo'] = descargar_panel_data912()

if st.session_state['precios_vivo']:
    st.divider()
    
    st.markdown(f"<h4 style='color: {C_VERDE_OSC};'>🎛️ 2. Panel de Sensibilidad Interactivo</h4>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1: var_global = st.number_input("🌍 Variación Global al mercado (%)", min_value=-50.0, max_value=50.0, value=0.0, step=0.5)
    with col2: ticker_especifico = st.selectbox("🎯 Seleccionar Ticker Específico", ["Ninguno"] + list(bonos_maestros.keys()))
    with col3: var_especifica = st.number_input("📉 Variación extra al Ticker Elegido (%)", min_value=-50.0, max_value=50.0, value=0.0, step=0.5)
    
    resultados = []
    hoy = date.today()
    mep_hoy = st.session_state['mep_hoy']
    precios_vivo = st.session_state['precios_vivo']
    
    for ticker, info in bonos_maestros.items():
        p_usd_real = precios_vivo.get(info["usd"], 0)
        p_ars_real = precios_vivo.get(info["ars"], 0)
        
        if p_usd_real <= 0: continue
        
        var_total_aplicada = var_global + (var_especifica if ticker == ticker_especifico else 0)
        p_usd_simulado = p_usd_real * (1 + (var_total_aplicada / 100))
        p_ars_simulado = p_ars_real * (1 + (var_total_aplicada / 100))
        
        precio_inversion_usd = p_usd_simulado * 100 if p_usd_simulado < 10 else p_usd_simulado
        dolar_cable = p_ars_simulado / p_usd_simulado if p_usd_simulado > 0 else 0
        costo_inversion_ars_en_usd = precio_inversion_usd * (dolar_cable / mep_hoy) if mep_hoy else precio_inversion_usd

        # Cálculo de Vencimiento y Próximo Pago
        vencimiento = max(info["fechas"]).strftime("%d/%m/%Y")
        fechas_futuras_completas = [(f, m) for f, m in zip(info["fechas"], info["flujos"]) if f >= hoy]
        if not fechas_futuras_completas: continue
        
        prox_fecha, prox_monto = fechas_futuras_completas[0]
        str_prox_pago = f"{prox_fecha.strftime('%d/%m/%y')} (US${prox_monto:.2f})"
        
        # Matemáticas de TIR, Duration y Convexity
        fechas_tir = [hoy] + [f for f, m in fechas_futuras_completas]
        flujos_tir_usd = [-precio_inversion_usd] + [m for f, m in fechas_futuras_completas]
        flujos_tir_ars = [-costo_inversion_ars_en_usd] + [m for f, m in fechas_futuras_completas]
        
        try:
            tir_usd = pyxirr.xirr(fechas_tir, flujos_tir_usd)
            tir_ars = pyxirr.xirr(fechas_tir, flujos_tir_ars)
            
            pv_total, suma_t_pv, suma_convexity = 0, 0, 0
            for i, (f, m) in enumerate(fechas_futuras_completas):
                t = (f - hoy).days / 365.0
                pv = m / ((1 + tir_usd) ** t)
                pv_total += pv
                suma_t_pv += (t * pv)
                suma_convexity += pv * (t**2 + t)
                
            macaulay_duration = suma_t_pv / pv_total
            convexity = suma_convexity / (pv_total * (1 + tir_usd)**2)
            
            # Cálculo Institucional de Paridad (% del Valor Técnico)
            fechas_pasadas = [f for f in info["fechas"] if f < hoy]
            ultima_fecha_pago = max(fechas_pasadas) if fechas_pasadas else hoy.replace(year=hoy.year-1)
            dias_corridos = (hoy - ultima_fecha_pago).days
            interes_corrido = info["vr_actual"] * (info["cupon_anual"] / 100) * (dias_corridos / 365.0)
            valor_tecnico = info["vr_actual"] + interes_corrido
            paridad = (precio_inversion_usd / valor_tecnico) * 100 if valor_tecnico > 0 else 0
            
            resultados.append({
                "Ticker": ticker,
                "Empresa": info["empresa"],
                "Lámina": info["lamina"],
                "Ley": info["ley"],
                "Calificación": info["calificacion"],
                "Cupón (%)": f"{info['cupon_anual']:.2f}%",
                "Precio ARS": round(p_ars_simulado, 2),
                "Precio USD": round(precio_inversion_usd, 2),
                "TC Implícito": round(dolar_cable, 2),
                "Paridad (%)": round(paridad, 2),
                "TIR USD (%)": round(tir_usd * 100, 2),
                "TIR ARS (%)": round(tir_ars * 100, 2),
                "Mac. Duration": round(macaulay_duration, 2),
                "Convexity": round(convexity, 2),
                "Próximo Pago": str_prox_pago,
                "Vencimiento": vencimiento
            })
        except: continue
            
    if resultados:
        # Armamos el DataFrame y lo ordenamos
        df_resultados = pd.DataFrame(resultados).sort_values(by="TIR USD (%)", ascending=False)
        df_resultados.set_index("Ticker", inplace=True)
        
        # TABLA DEFINITIVA BLOOMBERG
        st.subheader("📊 Panel de Rendimientos Institucional")
        st.markdown("💡 **Tip:** Hacé clic en cualquier fila de la tabla para ver la ficha técnica de la empresa.")
        
        # Formateo visual
        formato_columnas = {
            "Precio ARS": "${:,.2f}", 
            "Precio USD": "US${:,.2f}", 
            "TC Implícito": "${:,.2f}",
            "Paridad (%)": "{:.2f}%",
            "TIR USD (%)": "{:.2f}%", 
            "TIR ARS (%)": "{:.2f}%", 
            "Mac. Duration": "{:.2f}",
            "Convexity": "{:.2f}"
        }
        
        # 1. Tabla interactiva
        seleccion = st.dataframe(
            df_resultados.style.format(formato_columnas), 
            use_container_width=True, 
            height=350,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # 2. La tarjeta de información
        filas_seleccionadas = seleccion.selection.rows
        if len(filas_seleccionadas) > 0:
            indice_fila = filas_seleccionadas[0]
            ticker_elegido = df_resultados.index[indice_fila]
            
            nombre_empresa = bonos_maestros[ticker_elegido]["empresa"]
            desc_empresa = bonos_maestros[ticker_elegido]["descripcion"]
            calificacion = bonos_maestros[ticker_elegido]["calificacion"]
            ley = bonos_maestros[ticker_elegido]["ley"]
            
            st.markdown("---")
            st.markdown(f"<h4 style='color: {C_VERDE_OSC};'>🏢 Ficha Técnica: {nombre_empresa} ({ticker_elegido})</h4>", unsafe_allow_html=True)
            
            col_info1, col_info2, col_info3 = st.columns(3)
            col_info1.markdown(f"**Calificación Crediticia:** {calificacion}")
            col_info2.markdown(f"**Legislación:** Ley {ley}")
            col_info3.markdown(f"**Lámina Mínima:** {bonos_maestros[ticker_elegido]['lamina']}")
            
            st.info(f"**Perfil Corporativo:** {desc_empresa}")
            st.markdown("---")
        
        # GRÁFICO (Sin Mod Duration, ahora usa Macaulay)
        st.subheader("📈 Curva de Riesgo/Retorno")
        fig, ax = plt.subplots(figsize=(12, 7))
        
        x = df_resultados["Mac. Duration"]
        y = df_resultados["TIR USD (%)"]

        plt.scatter(x, y, color=C_CYAN, s=160, edgecolor=C_VERDE_OSC, linewidth=1.5, zorder=5, label='ONs')

        if len(x) > 2:
            z = np.polyfit(x, y, 2)
            p = np.poly1d(z)
            x_trend = np.linspace(min(x), max(x), 100)
            plt.plot(x_trend, p(x_trend), color=C_LIMA, linestyle='--', linewidth=3, zorder=4, alpha=0.9, label='Curva de Rendimiento')

        for i, row in df_resultados.iterrows():
            plt.annotate(row.name, (row["Mac. Duration"], row["TIR USD (%)"]), textcoords="offset points", xytext=(0,13), ha='center', fontsize=10, fontweight='bold', color=C_GRIS_OSC, bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.8, pad=1))

        plt.title("Frontera Eficiente: Obligaciones Negociables", fontsize=18, fontweight='bold', color=C_VERDE_OSC, pad=15)
        plt.xlabel("Riesgo (Macaulay Duration - Años)", fontsize=12, fontweight='bold', color=C_GRIS_OSC)
        plt.ylabel("Retorno (TIR USD)", fontsize=12, fontweight='bold', color=C_GRIS_OSC)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
        ax.tick_params(colors=C_GRIS_OSC)
        for spine in ax.spines.values(): spine.set_edgecolor(C_GRIS_OSC)
        plt.grid(True, color=C_VERDE_OSC, linestyle='-', alpha=0.15, zorder=0)
        plt.legend(loc='best', facecolor=C_CREMA, edgecolor=C_GRIS_OSC, labelcolor=C_GRIS_OSC)
        
        st.pyplot(fig)
