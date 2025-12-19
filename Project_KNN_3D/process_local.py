import os
import json
import trimesh
import random

# --- KONFIGURASI KRITIS ---
# GANTI PATH INI dengan lokasi folder tempat 357 file Anda berada
# Contoh: r"C:\Users\echaa\.objaverse\hf-objaverse-v1\glbs"
SOURCE_FOLDER = r"E:\Project_KNN_3D\Project_KNN_3D\.objaverse\hf-objaverse-v1\glbs" 

OUTPUT_FILE = "objaverse_dataset.json"

def get_smart_label_and_price(poly_count):
    # Logika pelabelan otomatis (Heuristik)
    noise = random.randint(-5, 5)
    if poly_count < 5000:
        return "Low-Poly", max(5, 10 + noise)
    elif poly_count < 50000:
        return "Medium-Poly", 30 + noise
    else:
        return "High-Poly", 60 + noise * 2

def main():
    if "GANTI_DENGAN" in SOURCE_FOLDER:
        print("ERROR: Yang Mulia, Anda belum mengganti SOURCE_FOLDER di dalam script!")
        return

    print(f"Membaca file dari: {SOURCE_FOLDER}")
    
    # Cari semua file GLB/OBJ/GLTF secara rekursif
    all_files = []
    for root, dirs, files in os.walk(SOURCE_FOLDER):
        for file in files:
            if file.lower().endswith(('.glb', '.gltf', '.obj')):
                all_files.append(os.path.join(root, file))

    total_files = len(all_files)
    print(f"Ditemukan {total_files} file 3D. Memulai ekstraksi...")

    if total_files == 0:
        print("GAGAL: Tidak ada file 3D ditemukan di folder tersebut. Cek path-nya lagi.")
        return

    dataset = []
    success_count = 0

    for i, file_path in enumerate(all_files):
        try:
            # Load mesh
            mesh = trimesh.load(file_path, force='mesh')
            
            # Handle Scene (jika file berisi banyak objek)
            if isinstance(mesh, trimesh.Scene):
                geoms = list(mesh.geometry.values())
                if not geoms: continue
                mesh = trimesh.util.concatenate(geoms)

            poly = len(mesh.faces)
            vert = len(mesh.vertices)
            
            # Skip file kosong/rusak
            if poly == 0: continue

            # Estimasi Material & Label
            mat = max(1, int(poly / 5000)) + random.randint(0, 2)
            label, price = get_smart_label_and_price(poly)
            
            # Simulasi Texture & Rig (karena trimesh terbatas bacanya)
            tex = random.randint(1, 5) if label != "Low-Poly" else 1
            rig = 1 if label == "High-Poly" and random.random() > 0.5 else 0
            
            # [Poly, Vert, Mat, Tex, Rig, Label]
            entry = [poly, vert, mat, tex, rig, label]
            dataset.append(entry)
            
            success_count += 1
            print(f"[{success_count}/{total_files}] OK: {os.path.basename(file_path)} -> {label}")

        except Exception as e:
            print(f"[SKIP] Error membaca {os.path.basename(file_path)}")

    # Simpan JSON
    if len(dataset) > 0:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(dataset, f, indent=2)
        print("\n" + "="*40)
        print(f"SELESAI! {len(dataset)} data berhasil diekstrak ke {OUTPUT_FILE}")
        print("Pindahkan file JSON ini ke folder backend Anda.")
        print("="*40)
    else:
        print("GAGAL TOTAL: Tidak ada data yang berhasil diekstrak.")

if __name__ == "__main__":
    main()