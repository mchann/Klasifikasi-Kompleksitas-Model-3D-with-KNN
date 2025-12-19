import json
import math
import sys

# --- KONFIGURASI ---
TRAIN_FILE = "train_dataset.json"
TEST_FILE = "test_dataset.json"

# --- FUNGSI MATEMATIKA (Sama persis dengan backend Anda) ---
def get_min_max(dataset):
    min_vals = [float('inf')] * 5
    max_vals = [float('-inf')] * 5
    for row in dataset:
        for i in range(5):
            val = float(row[i])
            if val < min_vals[i]: min_vals[i] = val
            if val > max_vals[i]: max_vals[i] = val
    return min_vals, max_vals

def normalize(raw_values, min_vals, max_vals):
    norm = []
    for i in range(5):
        denom = max_vals[i] - min_vals[i]
        if denom == 0: norm.append(0.0)
        else: norm.append((raw_values[i] - min_vals[i]) / denom)
    return norm

def predict_knn_single(input_row, training_data, min_v, max_v, k=5):
    # Input row: [Poly, Vert, Mat, Tex, Rig, ActualLabel]
    # Kita hanya ambil 5 fitur pertama untuk prediksi
    input_feats = [float(x) for x in input_row[:5]]
    norm_input = normalize(input_feats, min_v, max_v)
    
    distances = []
    for row in training_data:
        train_feats = [float(x) for x in row[:5]]
        norm_train = normalize(train_feats, min_v, max_v)
        
        # Euclidean Distance
        dist = math.sqrt(sum((norm_input[i] - norm_train[i])**2 for i in range(5)))
        distances.append((row[-1], dist)) # Simpan (Label, Jarak)
    
    # Sort jarak terdekat
    distances.sort(key=lambda x: x[1])
    
    # Ambil K tetangga
    k = min(k, len(training_data))
    neighbors = [d[0] for d in distances[:k]]
    
    # Voting
    prediction = max(set(neighbors), key=neighbors.count)
    return prediction

# --- MAIN EVALUATION ---
def main():
    print("--- MEMULAI EVALUASI MODEL ---")
    
    # 1. Load Data
    try:
        with open(TRAIN_FILE, 'r') as f: train_data = json.load(f)
        with open(TEST_FILE, 'r') as f: test_data = json.load(f)
    except FileNotFoundError:
        print("ERROR: File dataset tidak ditemukan. Pastikan sudah menjalankan splitting.")
        return

    print(f"Data Latih : {len(train_data)} sampel")
    print(f"Data Uji   : {len(test_data)} sampel")
    print("-" * 40)

    # 2. Pre-calculation (Min-Max) dari Training Data
    min_v, max_v = get_min_max(train_data)

    # 3. Proses Pengujian
    correct = 0
    total = len(test_data)
    
    # Untuk Confusion Matrix
    labels = ["Low-Poly", "Medium-Poly", "High-Poly"]
    matrix = {l: {l2: 0 for l2 in labels} for l in labels}
    
    print("Sedang menguji...", end="")
    
    for row in test_data:
        actual = row[-1] # Label asli ada di kolom terakhir
        predicted = predict_knn_single(row, train_data, min_v, max_v, k=5)
        
        if predicted == actual:
            correct += 1
            
        # Isi Matrix [Actual][Predicted]
        if actual in labels and predicted in labels:
            matrix[actual][predicted] += 1
            
    print(" Selesai.\n")

    # 4. Tampilkan Hasil Statistik
    accuracy = (correct / total) * 100
    print("=" * 40)
    print(f"HASIL AKHIR (METODE KNN, K=5)")
    print("=" * 40)
    print(f"Akurasi Model : {accuracy:.2f}%")
    print(f"Jumlah Benar  : {correct} dari {total}")
    print("-" * 40)
    
    print("\nCONFUSION MATRIX (Baris=Asli, Kolom=Prediksi):")
    print(f"{'':<12} | {'Low':<8} | {'Med':<8} | {'High':<8}")
    print("-" * 46)
    for l in labels:
        row_str = f"{l:<12} | "
        for l2 in labels:
            val = matrix[l][l2]
            row_str += f"{val:<8} | "
        print(row_str)
    print("-" * 46)

if __name__ == "__main__":
    main()