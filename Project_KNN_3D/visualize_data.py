import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- KONFIGURASI ---
DATASET_FILE = "train_dataset.json"

def main():
    try:
        with open(DATASET_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Dataset tidak ditemukan!")
        return

    # Siapkan List untuk menampung data per kategori
    # Struktur data: [Poly, Vert, Mat, Tex, Rig, Label]
    groups = {
        "Low-Poly": {"x": [], "y": [], "z": [], "c": "green", "m": "o"},
        "Medium-Poly": {"x": [], "y": [], "z": [], "c": "orange", "m": "^"},
        "High-Poly": {"x": [], "y": [], "z": [], "c": "red", "m": "x"}
    }

    print(f"Memvisualisasikan {len(data)} titik data...")

    for row in data:
        label = row[-1]
        if label in groups:
            # Sumbu X: Polygon Count (Dibagi 1000 biar angkanya kecil di grafik)
            groups[label]["x"].append(row[0]) 
            # Sumbu Y: Vertex Count
            groups[label]["y"].append(row[1])
            # Sumbu Z: Material Count
            groups[label]["z"].append(row[2])

    # Bikin Plot 3D
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    for label, grp in groups.items():
        ax.scatter(grp["x"], grp["y"], grp["z"], 
                   c=grp["c"], marker=grp["m"], label=label, alpha=0.6)

    ax.set_xlabel('Polygon Count')
    ax.set_ylabel('Vertex Count')
    ax.set_zlabel('Material Count')
    ax.set_title('Distribusi Data 3D: Clustering Low vs Med vs High')
    ax.legend()

    print("Grafik berhasil dibuat. Simpan gambar yang muncul untuk Laporan Bab 4.")
    plt.show()

if __name__ == "__main__":
    main()