import json, warnings
import joblib, numpy as np, pandas as pd, shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Riesgo de Preeclampsia · IA explicable", page_icon="🤰", layout="wide")

NOMBRES = {
    "edad": "Edad", "edad_gestacion": "Edad gestacional", "imc": "IMC", "pam": "Presión arterial media",
    "hemoglobina": "Hemoglobina", "hipertension": "Hipertensión", "diabetes": "Diabetes",
    "ant_fam_hiper": "Antec. familiar HTA",
}
def mostrar_fig(fig):
    """Renderiza la figura a PNG sin pasar por savefig (evita el error 'Done' de matplotlib en la nube)."""
    import io
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.colors import to_hex
    mapa = {"#008bfb": AZUL, "#ff0051": ROJO}
    for o in fig.findobj():
        for atr, setter in (("get_facecolor", "set_facecolor"), ("get_color", "set_color")):
            try:
                c = to_hex(getattr(o, atr)()).lower()
                if c in mapa:
                    getattr(o, setter)(mapa[c])
            except Exception:
                pass
    try:
        fig.tight_layout(); fig.subplots_adjust(right=0.9)
    except Exception:
        pass
    buf = io.BytesIO()
    FigureCanvasAgg(fig).print_png(buf)
    plt.close(fig)
    st.image(buf.getvalue(), width="stretch")


ROJO, VERDE, AZUL, AMBAR = "#ff7aa2", "#5eead4", "#b9a6ff", "#ffb38a"

st.markdown("""
<style>
.stApp{background:radial-gradient(1200px 600px at 85% -10%,#2a1d4a 0%,#120f1c 55%)}
.block-container{padding-top:4.2rem;max-width:1200px}
.hero2{display:flex;flex-wrap:wrap;background:linear-gradient(120deg,#241a42 0%,#3a1f4f 55%,#4d2457 100%);border:1px solid #4a3a73;border-radius:22px;overflow:hidden;
       box-shadow:0 12px 40px rgba(10,6,24,.55);margin-bottom:6px}
.hero2 .txt{flex:1 1 380px;padding:30px 34px}
.hero2 .tag{display:inline-block;background:#ff7aa222;color:#ffb3cb;border:1px solid #ff7aa255;border-radius:999px;padding:3px 12px;font-size:.75rem;letter-spacing:1px;text-transform:uppercase}
.hero2 h1{margin:12px 0 0;font-size:2.1rem;line-height:1.15;letter-spacing:-.5px;background:linear-gradient(90deg,#fff,#ffc2d6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero2 p{margin:10px 0 0;color:#cdc2e6;font-size:.98rem}
.hero2 .chips{margin-top:16px;display:flex;gap:8px;flex-wrap:wrap}
.hero2 .chips span{background:#ffffff12;border:1px solid #ffffff22;border-radius:10px;padding:5px 11px;font-size:.78rem;color:#e6def7}
.hero2 .pic{flex:1 1 340px;min-height:260px;position:relative}
.hero2 .pic::before{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(90deg,#3a1f4f 0%,rgba(58,31,79,0) 38%);pointer-events:none}
.hero2 .foto{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:60% 40%}
.hero2 .illu{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:14px}
.hero{background:linear-gradient(120deg,#241a42 0%,#3a1f4f 55%,#4d2457 100%);border:1px solid #4a3a73;border-radius:22px;padding:30px 34px;
      box-shadow:0 12px 40px rgba(10,6,24,.55)}
.hero .tag{display:inline-block;background:#ff7aa222;color:#ffb3cb;border:1px solid #ff7aa255;border-radius:999px;padding:3px 12px;font-size:.75rem;letter-spacing:1px;text-transform:uppercase}
.hero h1{margin:12px 0 0;font-size:2.1rem;line-height:1.15;letter-spacing:-.5px;background:linear-gradient(90deg,#fff,#ffc2d6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{margin:10px 0 0;color:#cdc2e6;font-size:.98rem;max-width:560px}
.chips{margin-top:16px;display:flex;gap:8px;flex-wrap:wrap}
.chips span{background:#ffffff12;border:1px solid #ffffff22;border-radius:10px;padding:5px 11px;font-size:.78rem;color:#e6def7}
.card{background:linear-gradient(160deg,#1f1938,#18132b);border:1px solid #33295a;border-radius:18px;padding:20px 22px;height:100%}
.card h4{margin:0 0 10px;font-size:.78rem;text-transform:uppercase;letter-spacing:1.3px;color:#a798cf;font-weight:600}
.badge{display:inline-block;padding:6px 15px;border-radius:999px;font-weight:600;font-size:.85rem;margin-top:8px}
.mini{display:flex;justify-content:space-between;color:#bdb0dc;font-size:.88rem;padding:7px 0;border-bottom:1px solid #2c2450}
.mini b{color:#f1ecfa}
.kpi{background:linear-gradient(160deg,#241a42,#1b1730);border:1px solid #3a2f63;border-radius:16px;padding:16px;text-align:center}
.kpi .v{font-size:1.6rem;font-weight:700;color:#ffb3cb}.kpi .l{color:#a798cf;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;margin-top:2px}
.aviso{background:#2d2018;border:1px solid #5b3f2a;color:#ffd2b3;border-radius:12px;padding:10px 14px;font-size:.85rem;margin-top:12px}
div[data-testid="stForm"]{border:1px solid #33295a;border-radius:18px;background:#17122a}
.stTabs [data-baseweb="tab"]{font-weight:600}
.stTabs [aria-selected="true"]{color:#ff7aa2}
button[data-testid^="stBaseButton-primary"]{background:linear-gradient(90deg,#ff7aa2,#c86bd6)!important;border:0!important;box-shadow:0 6px 18px rgba(255,122,162,.28)}
button[data-testid^="stBaseButton-primary"] p{color:#1a1030!important;font-weight:700!important}
button[data-testid^="stBaseButton-primary"]:hover{filter:brightness(1.08)}
.illu{display:flex;align-items:center;justify-content:center}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def cargar():
    modelo = joblib.load("modelo_preeclampsia.joblib")
    cfg = json.load(open("config_modelo.json"))
    bg = pd.read_csv("background.csv")[cfg["features"]]
    glob = json.load(open("shap_global.json"))
    f = lambda a: modelo.predict_proba(pd.DataFrame(a, columns=cfg["features"]))[:, 1]
    explainer = shap.Explainer(f, bg, seed=42)
    return modelo, cfg["features"], cfg["threshold"], explainer, glob


modelo, FEATURES, UMBRAL, explainer, GLOBAL = cargar()


def gauge(p, umbral):
    """Semicirculo SVG: la marca blanca es el umbral de decision."""
    import math
    def pt(frac, r=80):
        a = math.pi * (1 - frac)
        return 100 + r * math.cos(a), 100 - r * math.sin(a)
    x, y = pt(min(max(p, 0.001), 0.999)); tx, ty = pt(umbral, 92); tx2, ty2 = pt(umbral, 68)
    color = ROJO if p >= umbral else VERDE
    return f"""<svg viewBox="0 0 200 118" width="100%">
    <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="#252d42" stroke-width="16" stroke-linecap="round"/>
    <path d="M20 100 A80 80 0 0 1 {x:.1f} {y:.1f}" fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round"/>
    <line x1="{tx:.1f}" y1="{ty:.1f}" x2="{tx2:.1f}" y2="{ty2:.1f}" stroke="#fff" stroke-width="2.5"/>
    <text x="100" y="98" text-anchor="middle" fill="#f1ecfa" font-size="30" font-weight="700">{p:.0%}</text>
    <text x="100" y="114" text-anchor="middle" fill="#8b95ad" font-size="8">probabilidad estimada</text></svg>"""


def imagen_html():
    import os, base64
    for ext, mime in (("jpg", "jpeg"), ("jpeg", "jpeg"), ("png", "png"), ("webp", "webp")):
        if os.path.exists(f"embarazada.{ext}"):
            b64 = base64.b64encode(open(f"embarazada.{ext}", "rb").read()).decode()
            return f'<img class="foto" src="data:image/{mime};base64,{b64}" alt="Control prenatal">'
    return '<div class="illu">' + open("embarazada.svg", encoding="utf-8").read() + "</div>"


st.markdown(f"""<div class="hero2">
<div class="txt"><span class="tag">Tesis · IA explicable</span>
<h1>Detección temprana del riesgo de preeclampsia</h1>
<p>Metamodelo Ensemble Stacking con explicabilidad SHAP para apoyar la identificación temprana de gestantes con riesgo, en el primer control prenatal.</p>
<div class="chips"><span>🌲 Random Forest</span><span>🐱 CatBoost</span><span>⚡ XGBoost</span><span>💡 LightGBM</span><span>📈 Reg. Logística</span></div></div>
<div class="pic">{imagen_html()}</div></div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Predicción individual", "🔍 Importancia global (SHAP)", "ℹ️ Sobre el modelo"])

with tab1:
    izq, der = st.columns([5, 7], gap="large")
    with izq:
        with st.form("form"):
            st.markdown("##### Datos de la gestante")
            c1, c2 = st.columns(2)
            edad = c1.number_input("Edad (años)", 12, 50, 28)
            edad_g = c2.number_input("Edad gestacional (sem.)", 8, 14, 11)
            peso = c1.number_input("Peso (kg)", 35.0, 160.0, 65.0, 0.1)
            talla = c2.number_input("Talla (cm)", 120.0, 200.0, 155.0, 0.5)
            sis = c1.number_input("P.A. sistólica (mmHg)", 70, 220, 110)
            dia = c2.number_input("P.A. diastólica (mmHg)", 40, 140, 70)
            hb = st.number_input("Hemoglobina (g/dL)", 5.0, 20.0, 12.0, 0.1)
            st.markdown("##### Antecedentes")
            a, b, c = st.columns(3)
            hta = a.checkbox("Hipertensión")
            dm = b.checkbox("Diabetes")
            fam = c.checkbox("Antec. fam. HTA")
            ok = st.form_submit_button("Calcular riesgo", type="primary", width="stretch")
        st.markdown('<div class="aviso">⚠️ Herramienta académica de apoyo. No constituye un diagnóstico médico.</div>',
                    unsafe_allow_html=True)

    with der:
        if not ok:
            st.markdown('<div class="card"><h4>Resultado</h4><p style="color:#bdb0dc">Completa el formulario y pulsa '
                        '<b>Calcular riesgo</b> para ver la probabilidad estimada y qué variables la explican.</p></div>',
                        unsafe_allow_html=True)
        else:
            imc = peso / (talla / 100) ** 2
            pam = (sis + 2 * dia) / 3
            fila = pd.DataFrame([{"edad": edad, "edad_gestacion": edad_g, "imc": imc, "pam": pam,
                                  "hemoglobina": hb, "hipertension": int(hta), "diabetes": int(dm),
                                  "ant_fam_hiper": int(fam)}])[FEATURES]
            p = float(modelo.predict_proba(fila)[0, 1])
            alto = p >= UMBRAL
            col, tag = (ROJO, "RIESGO ALTO · requiere evaluación clínica") if alto else (VERDE, "RIESGO BAJO según el modelo")
            g1, g2 = st.columns([6, 5])
            g1.markdown(f'<div class="card"><h4>Riesgo estimado</h4>{gauge(p, UMBRAL)}'
                        f'<span class="badge" style="background:{col}22;color:{col};border:1px solid {col}66">{tag}</span></div>',
                        unsafe_allow_html=True)
            g2.markdown(f"""<div class="card"><h4>Valores calculados</h4>
              <div class="mini"><span>IMC</span><b>{imc:.1f} kg/m²</b></div>
              <div class="mini"><span>PAM</span><b>{pam:.1f} mmHg</b></div>
              <div class="mini"><span>Umbral de decisión</span><b>{UMBRAL:.2f}</b></div>
              <div class="mini"><span>Marca blanca</span><b>= umbral</b></div></div>""", unsafe_allow_html=True)

            st.markdown("##### ¿Por qué este resultado? (SHAP)")
            sv = explainer(fila)
            nombres = [f"{NOMBRES[f]} = {fila.iloc[0][f]:.1f}" if f in ("imc", "pam", "hemoglobina")
                       else f"{NOMBRES[f]} = {int(fila.iloc[0][f])}" for f in FEATURES]
            ex = shap.Explanation(values=sv.values[0], base_values=sv.base_values[0],
                                  data=None, feature_names=nombres)
            with plt.rc_context({"figure.facecolor": "#120f1c", "axes.facecolor": "#120f1c", "text.color": "#f1ecfa",
                                 "axes.labelcolor": "#f1ecfa", "xtick.color": "#bdb0dc", "ytick.color": "#f1ecfa"}):
                shap.plots.waterfall(ex, max_display=8, show=False)
                fig = plt.gcf(); fig.set_size_inches(7.5, 4.2); fig.patch.set_facecolor("#120f1c")
                mostrar_fig(fig)
            orden = np.argsort(-np.abs(sv.values[0]))[:3]
            frases = []
            for i in orden:
                sube = sv.values[0][i] > 0
                frases.append(f"**{NOMBRES[FEATURES[i]]}** {'aumenta' if sube else 'reduce'} el riesgo "
                              f"({sv.values[0][i]*100:+.1f} pts)")
            st.caption("Rosa = empuja la predicción hacia mayor riesgo · Lila = hacia menor riesgo. "
                       f"Valor base (gestante promedio): {sv.base_values[0]:.1%}.")
            st.info("Principales factores: " + " · ".join(frases))

with tab2:
    imp = pd.Series(GLOBAL["importance"], index=[NOMBRES[f] for f in GLOBAL["features"]]).sort_values()
    st.markdown("##### Importancia global de variables (media |SHAP| en 100 casos de Test)")
    with plt.rc_context({"figure.facecolor": "#120f1c", "axes.facecolor": "#120f1c", "text.color": "#f1ecfa",
                         "axes.labelcolor": "#f1ecfa", "xtick.color": "#bdb0dc", "ytick.color": "#f1ecfa"}):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(imp.index, imp.values, color=[ROJO if v == imp.max() else "#8f7be0" for v in imp.values])
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#3a2f63"); ax.set_xlabel("Contribución media a la probabilidad")
        for i, v in enumerate(imp.values):
            ax.text(v + imp.max() * 0.01, i, f"{v:.3f}", va="center", color="#f1ecfa", fontsize=9)
        mostrar_fig(fig)
    st.markdown(f"La **presión arterial media (PAM)** domina las predicciones del modelo, muy por encima del resto de variables. "
                "Esta importancia describe la lógica del modelo, no relaciones causales.")

with tab3:
    k = st.columns(5)
    for col, (v, l) in zip(k, [("93.7 %", "Recall (Test)"), ("71.8 %", "Precision (Test)"), ("0.813", "F1 (Test)"),
                               ("0.983", "ROC-AUC (Test)"), ("0.946", "PR-AUC (Test)")]):
        col.markdown(f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown("""
**Arquitectura.** Preprocesamiento (imputación + estandarización) → SMOTE (solo en entrenamiento) → 5 modelos base
(Random Forest, CatBoost, XGBoost, LightGBM, Regresión Logística) → metamodelo de Regresión Logística.

**Umbral de decisión: 0.55.** Elegido en validación priorizando Recall ≥ 0.93 y maximizando F1, para minimizar falsos negativos
(en Test: 74 de 79 casos detectados, 5 falsos negativos, 29 falsos positivos).

**Variables de entrada:** edad, edad gestacional, IMC, presión arterial media, hemoglobina, hipertensión, diabetes y antecedente familiar de hipertensión.

**Equipo:** Hidalgo Jauregui Karla Monica · Pedraza Perez Joshua Josue · Quispe Mamani Deyvis.
""")
