import bpy
import sys
import os
import json
import math

# --- 1. STRUKTUR DATA & CORE LOGIC ---
class ModelFeatures:
    def __init__(self):
        self.polygon_count = 0
        self.vertex_count = 0
        self.material_count = 0
        self.texture_count = 0
        self.rig_count = 0

def extract_features(obj):
    features = ModelFeatures()
    if obj.type != 'MESH': return None
    
    features.polygon_count = len(obj.data.polygons)
    features.vertex_count = len(obj.data.vertices)
    features.material_count = len(obj.material_slots)
    
    unique_textures = set()
    for slot in obj.material_slots:
        if slot.material and slot.material.use_nodes:
            for node in slot.material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    unique_textures.add(node.image.name)
    features.texture_count = len(unique_textures)
    
    has_armature = any(m.type == 'ARMATURE' for m in obj.modifiers)
    parent_armature = (obj.parent and obj.parent.type == 'ARMATURE')
    features.rig_count = 1 if (has_armature or parent_armature) else 0
    return features

# --- 2. DATASET & KNN LOGIC ---
# Data Latih (Hardcoded sesuai Jurnal Tabel 2 Sample)
TRAINING_DATA = [
    [1240, 1350, 1, 1, 0, "Low-Poly"],   
    [3500, 3600, 2, 1, 1, "Low-Poly"],
    [800, 850, 1, 0, 0, "Low-Poly"],
    [25400, 26100, 5, 3, 1, "Medium-Poly"], 
    [15000, 15500, 3, 2, 1, "Medium-Poly"],
    [45000, 46000, 4, 4, 1, "Medium-Poly"],
    [150500, 152000, 10, 8, 1, "High-Poly"],
    [85000, 86000, 8, 5, 0, "High-Poly"],
    [200000, 205000, 15, 10, 1, "High-Poly"]
]

def get_min_max(dataset):
    min_vals = [float('inf')] * 5
    max_vals = [float('-inf')] * 5
    for row in dataset:
        for i in range(5):
            if row[i] < min_vals[i]: min_vals[i] = row[i]
            if row[i] > max_vals[i]: max_vals[i] = row[i]
    return min_vals, max_vals

def normalize(raw_values, min_vals, max_vals):
    norm = []
    for i in range(5):
        if max_vals[i] - min_vals[i] == 0: norm.append(0.0)
        else: norm.append((raw_values[i] - min_vals[i]) / (max_vals[i] - min_vals[i]))
    return norm

def predict_knn(raw_features):
    # Persiapan KNN
    min_v, max_v = get_min_max(TRAINING_DATA)
    
    # Ubah input object ke list
    input_vals = [
        raw_features.polygon_count, raw_features.vertex_count,
        raw_features.material_count, raw_features.texture_count,
        raw_features.rig_count
    ]
    norm_input = normalize(input_vals, min_v, max_v)
    
    # Hitung Jarak (Euclidean)
    distances = []
    for row in TRAINING_DATA:
        norm_train = normalize(row[:5], min_v, max_v)
        dist = math.sqrt(sum((norm_input[i] - norm_train[i])**2 for i in range(5)))
        distances.append((row, dist))
    
    distances.sort(key=lambda x: x[1])
    
    # Ambil K=5 (Sesuai Jurnal)
    neighbors = [d[0][-1] for d in distances[:5]]
    prediction = max(set(neighbors), key=neighbors.count)
    return prediction, input_vals

# --- 3. LOGIKA BISNIS ---
def get_business_logic(label):
    if label == "Low-Poly":
        return {"price": "$5 - $15", "render": "Light", "hw": "Mobile/Web Compatible"}
    elif label == "Medium-Poly":
        return {"price": "$20 - $40", "render": "Medium", "hw": "PC/Console Standard"}
    else:
        return {"price": "$45 - $60+", "render": "Heavy", "hw": "High-End GPU (>6GB)"}

# --- 4. MAIN EXECUTION (HEADLESS) ---
def main():
    # Ambil argumen setelah "--" (File path target)
    try:
        argv = sys.argv
        if "--" in argv:
            args = argv[argv.index("--") + 1:]
            target_file = args[0]
            output_json_path = args[1]
        else:
            return # Tidak ada argumen
        
        # Buka File 3D secara otomatis
        bpy.ops.wm.open_mainfile(filepath=target_file)
        
        # Cari objek mesh pertama
        target_obj = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                target_obj = obj
                break
        
        result_data = {}
        
        if target_obj:
            feats = extract_features(target_obj)
            prediction, raw_vals = predict_knn(feats)
            biz = get_business_logic(prediction)
            
            result_data = {
                "status": "success",
                "filename": os.path.basename(target_file),
                "stats": {
                    "poly": raw_vals[0],
                    "vert": raw_vals[1],
                    "mat": raw_vals[2],
                    "tex": raw_vals[3],
                    "rig": raw_vals[4]
                },
                "classification": prediction,
                "business": biz
            }
        else:
            result_data = {"status": "error", "message": "No Mesh Found"}

        # SIMPAN KE JSON
        with open(output_json_path, 'w') as f:
            json.dump(result_data, f, indent=4)
            
    except Exception as e:
        # Error handling
        with open("error_log.txt", "w") as f:
            f.write(str(e))

if __name__ == "__main__":
    main()