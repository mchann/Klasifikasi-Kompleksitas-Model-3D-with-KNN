import streamlit as st
import streamlit.components.v1 as components
import subprocess
import os
import json
import tempfile
import base64
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import random  # PENTING: Untuk fitur acak data

# --- BAGIAN 1: UTILS & HELPER FUNCTIONS ---

def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def load_local_css(file_name, logo, bg):
    with open(file_name) as f: css = f.read()
    logo_b64 = get_img_as_base64(logo)
    bg_b64 = get_img_as_base64(bg)
    css = css.replace('__LOGO__', f'data:image/png;base64,{logo_b64}')
    css = css.replace('__BG__', f'data:image/png;base64,{bg_b64}')
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def render_3d_viewer(glb_path):
    with open(glb_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    html = f"""
    <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.1.1/model-viewer.min.js"></script>
    <style> model-viewer {{ width: 100%; height: 500px; background-color: #111418; border-radius: 18px; border: 1px solid #333; }} </style>
    <model-viewer src="data:model/gltf-binary;base64,{b64}" alt="3D" auto-rotate camera-controls ar shadow-intensity="1"></model-viewer>
    """
    components.html(html, height=520)

# --- CLASS KNN UNTUK STREAMLIT (Agar Tab 2 & 3 jalan tanpa Blender) ---
class StreamlitKNN:
    def __init__(self, k=5):
        self.k = k
        self.training_data = []
        self.min_vals = [] 
        self.max_vals = []

    def fit(self, dataset_path):
        if os.path.exists(dataset_path):
            with open(dataset_path, 'r') as f:
                self.training_data = json.load(f)
        else: return False
            
        self.min_vals = [float('inf')] * 5
        self.max_vals = [float('-inf')] * 5
        for row in self.training_data:
            for i in range(5):
                val = float(row[i])
                if val < self.min_vals[i]: self.min_vals[i] = val
                if val > self.max_vals[i]: self.max_vals[i] = val
        return True

    def _normalize(self, features):
        norm = []
        for i in range(5):
            denom = self.max_vals[i] - self.min_vals[i]
            if denom == 0: norm.append(0.0)
            else: norm.append((features[i] - self.min_vals[i]) / denom)
        return norm

    def predict(self, input_row):
        norm_input = self._normalize(input_row)
        distances = []
        for row in self.training_data:
            train_feats = [float(x) for x in row[:5]]
            norm_train = self._normalize(train_feats)
            dist = math.sqrt(sum((norm_input[i] - norm_train[i])**2 for i in range(5)))
            distances.append((row[-1], dist))
        
        distances.sort(key=lambda x: x[1])
        neighbors = [d[0] for d in distances[:self.k]]
        if not neighbors: return "Unknown"
        unique_labels = sorted(list(set(neighbors)))
        return max(unique_labels, key=neighbors.count)

# --- FUNGSI EVALUASI (INI YANG HILANG TADI) ---
def run_evaluation(test_file, train_file):
    knn = StreamlitKNN(k=5)
    # Coba load data latih
    if not knn.fit(train_file): 
        return None, None, 0
    
    # Coba load data uji
    if not os.path.exists(test_file):
        return None, None, 0
        
    with open(test_file, 'r') as f: test_data = json.load(f)
    
    correct = 0
    labels = ["Low-Poly", "Medium-Poly", "High-Poly"]
    matrix = {l: {l2: 0 for l2 in labels} for l in labels}
    
    for row in test_data:
        actual = row[-1]
        predicted = knn.predict(row[:5])
        
        if predicted == actual: correct += 1
        if actual in labels and predicted in labels:
            matrix[actual][predicted] += 1
            
    accuracy = (correct / len(test_data)) * 100
    return matrix, labels, accuracy

# --- APP CONFIG & SETUP ---
st.set_page_config(page_title="PolyPix AI", page_icon="🧊", layout="wide")
load_local_css("style.css", "logo.png", "bgr_new.png")


with st.sidebar:
    st.header("⚙️ Settings")
    exe = st.text_input("Blender Path:", r"D:\blender.exe")

# PATH DATASET
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAIN_FILE = os.path.join(BASE_DIR, "train_dataset.json")
TEST_FILE = os.path.join(BASE_DIR, "test_dataset.json")

# --- TABS SYSTEM ---
# [MODIFIKASI] Ubah nama tab jadi bhs Inggris agar CSS Navbar bekerja (Home, Evaluation, 3D Vis)
tab_main, tab_eval, tab_vis = st.tabs(["Home", "Evaluation", "3D Visualization"])

# ================= TAB 1: MAIN ANALYSIS (ORIGINAL) =================
with tab_main:

    # JUDUL & SIDEBAR
    st.title("ANALYZE YOUR 3D ASSETS INSTANTLY")
    st.markdown('<p class="subtitle">Automatic complexity classification & pricing engine for studios.</p>', unsafe_allow_html=True)

    uploaded = st.file_uploader("", type=["blend", "obj"])

    if uploaded:
        st.write("")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: run = st.button("🚀 RUN ANALYSIS", type="primary", use_container_width=True)

        if run:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded.getvalue())
                path = tmp.name
            
            script = os.path.join(BASE_DIR, "backend_processor.py")
            res_json = os.path.join(BASE_DIR, "result.json")
            res_glb = os.path.join(BASE_DIR, "preview.glb")

            with st.spinner('Processing Geometry & AI Classification...'):
                try:
                    subprocess.run([exe, "-b", "--python", script, "--", path, res_json, res_glb], capture_output=True)
                    
                    if os.path.exists(res_json):
                        with open(res_json, 'r') as f: d = json.load(f)
                        
                        if d["status"] == "success":
                            st.success("Analysis Complete!")
                            st.markdown("---")
                            
                            # Parsing Data
                            poly = f"{d['stats']['poly']:,}"
                            vert = f"{d['stats']['vert']:,}"
                            mat = d['stats']['mat']
                            rig = "Yes ✅" if d['stats']['rig'] else "No ❌"
                            lbl = d['classification'].upper().replace("-", "<br>")
                            price = d['business']['price']
                            render = d['business']['render']
                            
                            if "HIGH" in lbl: cls="status-high"
                            elif "MEDIUM" in lbl: cls="status-med"
                            else: cls="status-low"

                            html_dashboard = f"""
<div class="result-container">
<div class="card">
    <div class="card-title">Technical Stats</div>
    <div class="stat-row"><span>Polygon Count</span><span class="stat-val">{poly}</span></div>
    <div class="stat-row"><span>Vertices</span><span class="stat-val">{vert}</span></div>
    <div class="stat-row"><span>Materials</span><span class="stat-val">{mat}</span></div>
    <div class="stat-row" style="border:none"><span>Rigged</span><span class="stat-val">{rig}</span></div>
</div>
<div class="card">
    <div class="card-title" style="text-align:center">Classification</div>
    <div class="gauge-container">
        <div class="gauge-circle {cls}">
            <div class="gauge-text">{lbl}</div>
        </div>
        <div class="desc-text">Geometry suitable for<br><strong style="color:white">{render}</strong></div>
    </div>
</div>
<div class="card">
    <div class="card-title">Smart Recommendations</div>
    <div class="rec-item">
        <div class="rec-icon-row">
            <span style="font-size:30px">💲</span>
            <div class="rec-price">{price}</div>
        </div>
        <div class="rec-label">Suggested Market Price</div>
    </div>
    <div class="rec-item">
        <div class="rec-icon-row">
            <span style="font-size:30px">💾</span>
            <div class="rec-render-text">{render}</div>
        </div>
        <div class="rec-label">Resource Usage</div>
    </div>
</div>
</div>
"""
                            st.markdown(html_dashboard, unsafe_allow_html=True)
                            
                            st.markdown("### 🧊 Interactive 3D Preview")
                            if os.path.exists(res_glb): render_3d_viewer(res_glb)
                        else: st.error("Processing Failed.")
                    else: st.error("No Result Data.")
                except Exception as e: st.error(f"Error: {e}")
                finally:
                     if os.path.exists(path): os.remove(path)

# ================= TAB 2: LIVE TRAINING & EVALUATION =================
with tab_eval:
    c_title, c_btn = st.columns([3, 1])
    with c_title:
        st.header("📊 Live Model Evaluation")
        st.caption("Uji validitas model dengan data acak (Real-time).")
    
    # TOMBOL SAKTI: RETRAIN
    with c_btn:
        if st.button("🔄 Retrain & Reshuffle", help="Kocok ulang dataset dan latih model baru", type="secondary"):
            if os.path.exists(TRAIN_FILE) and os.path.exists(TEST_FILE):
                with st.spinner("Mengocok ulang data & Melatih model..."):
                    try:
                        with open(TRAIN_FILE, 'r') as f: d1 = json.load(f)
                        with open(TEST_FILE, 'r') as f: d2 = json.load(f)
                        
                        full_data = d1 + d2
                        random.shuffle(full_data)
                        
                        split_idx = int(len(full_data) * 0.8)
                        new_train = full_data[:split_idx]
                        new_test = full_data[split_idx:]
                        
                        with open(TRAIN_FILE, 'w') as f: json.dump(new_train, f)
                        with open(TEST_FILE, 'w') as f: json.dump(new_test, f)
                        
                        st.cache_data.clear() # Reset cache
                        st.success("Model berhasil dilatih ulang!")
                    except Exception as e:
                        st.error(f"Error saat retrain: {e}")
            else:
                st.error("Dataset tidak lengkap.")

    # TAMPILAN EVALUASI
    if os.path.exists(TRAIN_FILE) and os.path.exists(TEST_FILE):
        matrix, labels, acc = run_evaluation(TEST_FILE, TRAIN_FILE)
        
        if matrix:
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Accuracy", f"{acc:.2f}%", delta="Live Result")
            m2.metric("Training Data", f"{len(json.load(open(TRAIN_FILE)))} Samples", "80%")
            m3.metric("Testing Data", f"{len(json.load(open(TEST_FILE)))} Samples", "20%")
            
            st.subheader("Confusion Matrix (Real-Time)")
            
            # HTML Table Render
            html_table = """
            <table style="width:100%; text-align:center; border-collapse: collapse;">
                <tr style="background-color:#262730; color:white;">
                    <th style="padding:10px; border:1px solid #444;">Actual ▼ | Pred ►</th>
                    <th style="border:1px solid #444;">Low-Poly</th>
                    <th style="border:1px solid #444;">Medium-Poly</th>
                    <th style="border:1px solid #444;">High-Poly</th>
                </tr>
            """
            for l_act in labels:
                html_table += f"<tr><td style='font-weight:bold; background-color:#1E1E1E; border:1px solid #444;'>{l_act}</td>"
                for l_pred in labels:
                    val = matrix[l_act][l_pred]
                    if l_act == l_pred:
                        bg = "rgba(0, 204, 150, 0.4)" if val > 0 else "transparent"
                    else:
                        bg = "rgba(255, 75, 75, 0.4)" if val > 0 else "transparent"
                    
                    html_table += f"<td style='background-color:{bg}; border:1px solid #444;'>{val}</td>"
                html_table += "</tr>"
            html_table += "</table>"
            
            st.markdown(html_table, unsafe_allow_html=True)
            
            if acc > 90:
                st.success("✅ **Kesimpulan:** Model sangat stabil (>90%).")
            elif acc > 70:
                st.warning("⚠️ **Kesimpulan:** Model cukup stabil.")
            else:
                st.error("❌ **Kesimpulan:** Model tidak stabil.")
        else:
            st.warning("Gagal memuat evaluasi. Cek file JSON.")
            
    else:
        st.warning("Dataset not found. Please run data_splitter.py first.")

# ================= TAB 3: VISUALIZATION =================
with tab_vis:
    st.header("📈 3D Data Distribution")
    
    if os.path.exists(TRAIN_FILE):
        with open(TRAIN_FILE, 'r') as f: data = json.load(f)
        
        groups = {
            "Low-Poly": {"x": [], "y": [], "z": [], "c": "green", "m": "o"},
            "Medium-Poly": {"x": [], "y": [], "z": [], "c": "orange", "m": "^"},
            "High-Poly": {"x": [], "y": [], "z": [], "c": "red", "m": "x"}
        }

        for row in data:
            lbl = row[-1]
            if lbl in groups:
                groups[lbl]["x"].append(row[0])
                groups[lbl]["y"].append(row[1])
                groups[lbl]["z"].append(row[2])
                
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor('#0E1117') 
        fig.patch.set_facecolor('#0E1117')
        
        for label, grp in groups.items():
            ax.scatter(grp["x"], grp["y"], grp["z"], c=grp["c"], marker=grp["m"], label=label)

        ax.set_xlabel('Polygon', color='white')
        ax.set_ylabel('Vertex', color='white')
        ax.set_zlabel('Material', color='white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.tick_params(axis='z', colors='white')
        ax.legend(facecolor='#262730', labelcolor='white')
        
        st.pyplot(fig)
        st.info("Grafik ini membuktikan bahwa data terkelompok dengan baik secara geometri.")
    else:
        st.warning("Data latih belum tersedia.")