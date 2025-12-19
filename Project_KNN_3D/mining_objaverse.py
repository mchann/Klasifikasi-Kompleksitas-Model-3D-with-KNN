import objaverse
import trimesh
import random
import json
import os
import shutil

# --- KONFIGURASI ---
TOTAL_SAMPLES = 500 
OUTPUT_FILE = "objaverse_dataset.json"

def get_smart_label_and_price(poly_count):
    """
    Logika pelabelan otomatis berdasarkan jumlah polygon.
    Ini adalah 'Ground Truth' heuristik.
    """
  
    noise = random.randint(-5, 5)
    
    if poly_count < 5000:
        price = max(5, 10 + noise)
        return "Low-Poly", price
    elif poly_count < 50000:
        price = 30 + noise
        return "Medium-Poly", price
    else:
        price = 60 + noise * 2
        return "High-Poly", price

def main():
    print("1. Mengambil list UID dari Objaverse...")
    uids = objaverse.load_uids()
    
    # Ambil sampel acak
    selected_uids = random.sample(uids, TOTAL_SAMPLES)
    print(f"2. Mendownload & Memproses {TOTAL_SAMPLES} model...")

    dataset = []
    
    # Kita download batch kecil agar tidak memakan RAM
    objects = objaverse.load_objects(selected_uids)
    
    success_count = 0
    
    for uid, path in objects.items():
        try:
            # Load mesh menggunakan trimesh (Cepat & Ringan)
            mesh = trimesh.load(path, force='mesh')
            
            # Jika scene (banyak objek), gabungkan
            if isinstance(mesh, trimesh.Scene):
                # Dump semua geometry di scene menjadi satu mesh
                geometries = list(mesh.geometry.values())
                if not geometries: continue
                mesh = trimesh.util.concatenate(geometries)

            # Ekstrak Data
            poly = len(mesh.faces)
            vert = len(mesh.vertices)
            
            # sm: makin kompleks mesh, makin banyak material
            mat = max(1, int(poly / 5000)) + random.randint(0, 2)
            
            # Buat Label
            label, price = get_smart_label_and_price(poly)
            
            # Format Data untuk KNN Anda: [Poly, Vert, Mat, Tex, Rig, Label]
            tex = random.randint(1, 5) if label != "Low-Poly" else 1
            rig = 1 if label == "High-Poly" and random.random() > 0.5 else 0
            
            entry = [poly, vert, mat, tex, rig, label]
            dataset.append(entry)
            
            success_count += 1
            print(f"[{success_count}/{TOTAL_SAMPLES}] {uid[:8]}... -> P:{poly} ({label})")

        except Exception as e:
            print(f"Error processing {uid}: {e}")
            continue
            
    # Simpan JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(dataset, f, indent=2)
        
    print(f"\nSUKSES! {len(dataset)} data tersimpan di {OUTPUT_FILE}")
    print("PENTING: Cek folder user directory anda (misal C:/Users/Name/.objaverse) dan hapus isinya jika sudah selesai.")

if __name__ == "__main__":
    main()