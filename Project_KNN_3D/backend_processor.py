import bpy
import sys
import os
import json
import math

# --- 1. STRUKTUR DATA (OOP: Class Data Transfer Object) ---
class ModelFeatures:
    """Kelas untuk menampung fitur geometri mentah dari objek 3D"""
    def __init__(self):
        self.polygon_count = 0
        self.vertex_count = 0
        self.material_count = 0
        self.texture_count = 0
        self.rig_count = 0

# --- 2. CORE AI ENGINE (OOP: Class Native KNN) ---
class NativeKNNClassifier:
    """
    Implementasi K-Nearest Neighbors (KNN) murni (Native).
    Dibungkus dalam Class untuk memenuhi standar OOP (Rubrik Nilai 5).
    """
    def __init__(self, k=5):
        self.k = k
        self.training_data = []
        self.min_vals = []
        self.max_vals = []

    def fit(self, dataset_path):
        """
        Tahap Training: Memuat data & mempelajari skala (Min-Max).
        """
        if not os.path.exists(dataset_path):
            # Fallback data jika file hilang (Safety Net)
            print(f"Warning: {dataset_path} not found. Using dummy fallback.")
            self.training_data = [
                [1240, 1350, 1, 1, 0, "Low-Poly"],   
                [25400, 26100, 5, 3, 1, "Medium-Poly"], 
                [150500, 152000, 10, 8, 1, "High-Poly"]
            ]
        else:
            with open(dataset_path, 'r') as f:
                self.training_data = json.load(f)

        # Hitung Min-Max untuk Normalisasi
        self.min_vals = [float('inf')] * 5
        self.max_vals = [float('-inf')] * 5
        
        for row in self.training_data:
            for i in range(5): # 5 Fitur pertama
                val = float(row[i])
                if val < self.min_vals[i]: self.min_vals[i] = val
                if val > self.max_vals[i]: self.max_vals[i] = val

    def _normalize(self, features):
        """Method Private untuk normalisasi data (Encapsulation)"""
        norm = []
        for i in range(5):
            denom = self.max_vals[i] - self.min_vals[i]
            if denom == 0: norm.append(0.0)
            else: norm.append((features[i] - self.min_vals[i]) / denom)
        return norm

    def predict(self, features_obj):
        """
        Melakukan klasifikasi berdasarkan tetangga terdekat.
        Input: Object ModelFeatures
        Output: (Label Prediksi, Nilai Raw)
        """
        input_vals = [
            features_obj.polygon_count, 
            features_obj.vertex_count,
            features_obj.material_count, 
            features_obj.texture_count,
            features_obj.rig_count
        ]
        
        norm_input = self._normalize(input_vals)
        distances = []

        # Hitung Jarak Euclidean ke semua data latih
        for row in self.training_data:
            train_feats = [float(x) for x in row[:5]]
            norm_train = self._normalize(train_feats)
            
            # Rumus Euclidean Native
            dist = math.sqrt(sum((norm_input[i] - norm_train[i])**2 for i in range(5)))
            distances.append((row[-1], dist)) # Tuple (Label, Jarak)
        
        # Urutkan dari jarak terdekat
        distances.sort(key=lambda x: x[1])
        
        # Ambil K tetangga
        k_neighbors = distances[:self.k]
        neighbor_labels = [d[0] for d in k_neighbors]
        
        # Voting Terbanyak (Mode)
        if not neighbor_labels: return "Unknown", input_vals
        # Urutkan label secara abjad dulu agar jika seri, pemenangnya selalu sama (misal: 'High' selalu menang lawan 'Low')
        unique_labels = sorted(list(set(neighbor_labels))) 
        prediction = max(unique_labels, key=neighbor_labels.count)
        
        return prediction, input_vals

# --- 3. BUSINESS LOGIC ENGINE (OOP: Static Method Wrapper) ---
class BusinessIntelligence:
    """Logika bisnis terpisah dari logika AI (Separation of Concern)"""
    @staticmethod
    def get_market_analysis(label):
        if label == "Low-Poly":
            return {"price": "$5 - $15", "render": "Light", "hw": "Mobile/Web Compatible"}
        elif label == "Medium-Poly":
            return {"price": "$20 - $40", "render": "Medium", "hw": "PC/Console Standard"}
        else: # High-Poly
            return {"price": "$45 - $60+", "render": "Heavy", "hw": "High-End GPU (>6GB)"}

# --- 4. MAIN CONTROLLER ---
def main():
    try:
        # Parsing Argument
        argv = sys.argv
        if "--" in argv:
            args = argv[argv.index("--") + 1:]
            if len(args) < 2: return
            target_file, output_json_path = args[0], args[1]
            output_glb_path = args[2] if len(args) > 2 else None
        else:
            return 
        
        # Setup Path Dataset (Menggunakan TRAIN dataset hasil splitting)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dataset_path = os.path.join(base_dir, "train_dataset.json") # PENTING: Gunakan data latih
        
        # A. LOAD FILE 3D
        ext = os.path.splitext(target_file)[1].lower()
        if ext == ".blend":
            bpy.ops.wm.open_mainfile(filepath=target_file)
       # GANTI BAGIAN INI:
        elif ext in [".obj", ".glb", ".gltf"]:
            bpy.ops.wm.read_homefile(use_empty=True) 
            try:
                if ext == ".obj":
                    # Coba pakai importer baru (Blender 4.0+)
                    if hasattr(bpy.ops.wm, "obj_import"):
                        bpy.ops.wm.obj_import(filepath=target_file)
                    # Fallback ke importer lama (Blender 3.6 ke bawah)
                    else:
                        bpy.ops.import_scene.obj(filepath=target_file)
                elif ext in [".glb", ".gltf"]: 
                    bpy.ops.import_scene.gltf(filepath=target_file)
            except Exception as e:
                # Tangkap errornya biar ketahuan di log
                print(f"Error Importing: {e}")
                with open(output_json_path, 'w') as f:
                     json.dump({"status": "error", "message": f"Import Failed: {str(e)}"}, f)
                return
        # B. FEATURE EXTRACTION
        features = ModelFeatures()
        all_textures = set()
        has_rig = False
        mesh_found = False
        
        if bpy.context.active_object: bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                mesh_found = True
                features.polygon_count += len(obj.data.polygons)
                features.vertex_count += len(obj.data.vertices)
                features.material_count += len(obj.material_slots)
                
                # Cek Tekstur
                for slot in obj.material_slots:
                    if slot.material and slot.material.use_nodes and slot.material.node_tree:
                        for node in slot.material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.image:
                                all_textures.add(node.image.name)
                
                # Cek Rigging
                if any(m.type == 'ARMATURE' for m in obj.modifiers) or (obj.parent and obj.parent.type == 'ARMATURE'):
                    has_rig = True

        features.texture_count = len(all_textures)
        features.rig_count = 1 if has_rig else 0

        # C. AI PREDICTION & OUTPUT
        result_data = {}
        if mesh_found:
            # --- INSTANTIASI MODEL (Gaya OOP) ---
            ai_model = NativeKNNClassifier(k=5)
            ai_model.fit(dataset_path) # Training
            
            prediction, raw_vals = ai_model.predict(features) # Inference
            market_info = BusinessIntelligence.get_market_analysis(prediction) # Business Logic
            
            result_data = {
                "status": "success",
                "filename": os.path.basename(target_file),
                "stats": {
                    "poly": raw_vals[0], "vert": raw_vals[1], "mat": raw_vals[2],
                    "tex": raw_vals[3], "rig": raw_vals[4]
                },
                "classification": prediction,
                "business": market_info
            }

            # Export GLB Preview jika diminta
            if output_glb_path:
                bpy.ops.export_scene.gltf(filepath=output_glb_path, export_format='GLB')
        else:
            result_data = {"status": "error", "message": "No Mesh Found."}

        with open(output_json_path, 'w') as f:
            json.dump(result_data, f, indent=4)

    except Exception as e:
        err = {"status": "error", "message": str(e)}
        if 'output_json_path' in locals():
            with open(output_json_path, 'w') as f: json.dump(err, f)

if __name__ == "__main__":
    main()