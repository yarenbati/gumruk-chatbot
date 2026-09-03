# Gümrük Mevzuatı Chatbot

Türk gümrük mevzuatına dayanan, kaynak gösteren RAG tabanlı soru-cevap chatbotu.

## Kurulum

### Gereksinimler

Python 3.10+ ile bir sanal ortam oluşturup etkinleştirin:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Ortam Değişkenleri

`.env.example` dosyasını `.env` olarak kopyalayın ve `OPENAI_API_KEY`
değerini kendi anahtarınızla yapılandırın. Anahtarı kaynak koda eklemeyin.

### Veri Hazırlama (Ingest)

### Çalıştırma

Mevzuat corpus'unun yerel Chroma koleksiyonuna önceden indekslendiğinden
emin olduktan sonra arayüzü başlatın:

```powershell
python -m streamlit run app.py
```

### Deploy (Streamlit Community Cloud)
