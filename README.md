# 🤖 Advanced AI Chat Interface

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Gradio](https://img.shields.io/badge/Frontend-Gradio-orange?style=for-the-badge&logo=gradio)
![Status](https://img.shields.io/badge/Status-Active-green?style=for-the-badge)

**Advanced AI Chat** adalah asisten AI multimodal berbasis Python yang dirancang untuk memberikan pengalaman interaksi yang kaya dan fleksibel. Aplikasi ini mengintegrasikan berbagai provider AI terkemuka, kemampuan analisis dokumen/gambar (OCR), akses internet real-time, hingga fitur unik untuk roleplay dan integrasi VTuber.

## ✨ Fitur Unggulan

* **🧠 Multi-Provider Support**: Dukungan penuh untuk **Google Gemini**, **DeepSeek**, **OpenRouter**, **Blackbox AI**, dan **LM Studio** (Local LLM).
* **👀 Multimodal Vision & OCR**:
    * Analisis gambar cerdas menggunakan model Vision.
    * Ekstraksi teks dari gambar (OCR) menggunakan **EasyOCR**.
* **📄 Analisis Dokumen**: Mampu membaca dan memahami isi file PDF, DOCX, dan TXT.
* **🌐 Web Access**: Terintegrasi dengan **DuckDuckGo Search** untuk memberikan jawaban berbasis data terkini dari internet.
* **🗣️ Voice Interaction**:
    * **Speech-to-Text**: Bicara langsung dengan AI menggunakan Whisper/Google Speech.
    * **Text-to-Speech**: AI merespons dengan suara natural (gTTS).
* **🎭 Roleplay Mode**: Tab khusus untuk bermain peran dengan karakter AI yang memiliki memori jangka panjang.
* **🎥 VTuber Integration (Beta)**: Fitur eksperimental untuk menghubungkan chat AI dengan **VTube Studio** dan **Live Chat Youtube**.

## 🛠️ Tech Stack

Project ini dibangun menggunakan teknologi open-source yang powerful:

* **Frontend**: [Gradio](https://www.gradio.app/) (UI Modern & Responsif)
* **Core AI**: `google-genai`, `openai`, `duckduckgo_search`
* **Vision/OCR**: `easyocr`, `Pillow`, `opencv-python`
* **Audio**: `gtts`, `speech_recognition`, `openai-whisper`
* **Document**: `pypdf`, `python-docx`
* **VTuber**: `pyvts`, `pytchat`

## 🚀 Cara Instalasi

Pastikan kamu sudah menginstall **Python 3.10** atau lebih baru.

1.  **Clone Repository**
    ```bash
    git clone [https://github.com/zhart56/CHAT-AI.git](https://github.com/zhart56/CHAT-AI.git)
    cd CHAT-AI
    ```

2.  **Install Dependencies**
    Sangat disarankan menggunakan virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup API Key**
    Jalankan aplikasi dan masuk ke tab **Konfigurasi** untuk memasukkan API Key (Gemini, OpenRouter, atau DeepSeek) sesuai kebutuhan.

## 💻 Cara Penggunaan

1.  Jalankan aplikasi dengan perintah:
    ```bash
    python app.py
    ```
2.  Buka browser dan akses alamat lokal yang muncul (biasanya `http://127.0.0.1:7860`).
3.  Pilih tab yang diinginkan:
    * **Chat + Akses Web**: Untuk tanya jawab umum dan riset.
    * **Chat Roleplay**: Untuk simulasi karakter.
    * **Konfigurasi**: Untuk mengatur model dan API Key.

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan _fork_ repository ini dan buat _Pull Request_ jika kamu punya ide fitur baru atau perbaikan bug.

## 📝 Lisensi

Project ini dilisensikan di bawah [MIT License](LICENSE).