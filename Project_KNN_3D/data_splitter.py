import json
import random
import os

# --- KONFIGURASI ---
INPUT_FILE = "objaverse_dataset.json"  # Data mentah Anda (357 data tadi)
TRAIN_OUTPUT = "train_dataset.json"    # Output untuk Training (80%)
TEST_OUTPUT = "test_dataset.json"      # Output untuk Testing (20%)
SPLIT_RATIO = 0.8                      # Rasio pembagian

def main():
    # 1. Cek apakah file dataset ada
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: File {INPUT_FILE} tidak ditemukan!")
        return

    # 2. Load data
    print("Membaca dataset...")
    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)
    
    total_data = len(data)
    if total_data == 0:
        print("Dataset kosong!")
        return

    # 3. ACAK DATA 

    random.shuffle(data)

    # 4. Hitung titik potong
    split_index = int(total_data * SPLIT_RATIO)

    # 5. Bagi Data
    train_data = data[:split_index]
    test_data = data[split_index:]

    # 6. Simpan ke file terpisah
    with open(TRAIN_OUTPUT, 'w') as f:
        json.dump(train_data, f, indent=2)
    
    with open(TEST_OUTPUT, 'w') as f:
        json.dump(test_data, f, indent=2)

    # 7. Laporan
    print("-" * 30)
    print("PEMBAGIAN DATA SELESAI")
    print("-" * 30)
    print(f"Total Data Awal : {total_data}")
    print(f"Data Latih (Train): {len(train_data)} ({len(train_data)/total_data*100:.1f}%) -> Disimpan di {TRAIN_OUTPUT}")
    print(f"Data Uji (Test)   : {len(test_data)} ({len(test_data)/total_data*100:.1f}%) -> Disimpan di {TEST_OUTPUT}")
    print("-" * 30)
    print("Gunakan 'train_dataset.json' untuk aplikasi utama.")
    print("Gunakan 'test_dataset.json' HANYA untuk evaluasi akurasi.")

if __name__ == "__main__":
    main()