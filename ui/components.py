import gradio as gr
from config import global_settings, DEFAULT_SYSTEM_PROMPT, DEFAULT_RP_SYSTEM_PROMPT, DATA_DIR
from file_utils import list_files_in_dir

def create_chat_input_interface(placeholder="Ketik pesan Anda atau unggah file..."):
    """Menciptakan komponen input chat yang dapat digunakan kembali."""
    with gr.Row():
        user_input = gr.Textbox(
            show_label=False,
            placeholder=placeholder,
            container=False
        )
        file_upload = gr.File(
            label="📁 Unggah File (Bisa Banyak)",
            file_count="multiple",
            file_types=["image", ".pdf", ".txt", ".docx"],
        )
    
    with gr.Row():
        send_button = gr.Button("Kirim Pesan", variant="primary", visible=True)
        send_vision = gr.Button("🖼️ Vision", variant="secondary", visible=False)
        send_ocr = gr.Button("📄 OCR", variant="secondary", visible=False)
        send_doc = gr.Button("📄 Dokumen", variant="secondary", visible=False)
        stop_button = gr.Button("⏹️ Stop", variant="stop", visible=False)
    
    return {
        "user_input": user_input,
        "file_upload": file_upload,
        "send_button": send_button,
        "send_vision": send_vision,
        "send_ocr": send_ocr,
        "send_doc": send_doc,
        "stop_button": stop_button
    }

def create_web_chat_tab():
    """Menciptakan semua komponen untuk tab Chat + Akses Web."""
    with gr.Row():
        with gr.Column(scale=1):
            # --- BAGIAN YANG HILANG DIMULAI DI SINI ---
            gr.Markdown("#### Manajemen Sesi")
            chat_name_web = gr.Textbox(
                label="Nama Sesi",
                placeholder="Otomatis..."
            )
            with gr.Row():
                save_chat_web = gr.Button("💾 Simpan")
                load_chat_web = gr.Button("📂 Muat")
                delete_chat_web = gr.Button("🗑️ Hapus")

            chat_list_web = gr.Dropdown( # INI KOMPONEN YANG MENYEBABKAN ERROR
                label="Pilih Sesi Tersimpan",
                choices=[],
                allow_custom_value=False
            )
            status_web = gr.Markdown("")

            with gr.Accordion(" 🧠  Memori Jangka Panjang", open=False):
                gr.Markdown("Pilih atau buat topik memori untuk sesi ini.")
                with gr.Row():
                    memory_web_list = gr.Dropdown(
                        label="Pilih Topik Memori",
                        choices=[], # Akan diisi saat aplikasi dimuat
                        interactive=True
                )
                memory_web_delete_btn = gr.Button("🗑️ Hapus Topik")

                memory_web_box = gr.Textbox(
                    label="Isi Memori (dari topik yang dipilih)",
                    lines=6,
                    interactive=False
                )
                memory_web_input = gr.Textbox(
                    label="Tambah Fakta ke Memori (topik terpilih)",
                    placeholder="misal: proyek riset saya tentang energi terbarukan"
                )
                with gr.Row():
                    add_mem_web_btn = gr.Button("Simpan Fakta")
                    clear_mem_web_btn = gr.Button("Kosongkan Isi Topik")

                auto_mem_web_check = gr.Checkbox(
                    label="Update Memori Otomatis",
                    info="AI akan menyimpan fakta penting ke topik memori yang sedang aktif."
                )

        with gr.Column(scale=3):
            chatbot_web = gr.Chatbot(
                            height=500, 
                            label="Chat Web", 
                            type="messages",
                            latex_delimiters=[{"left": "$$", "right": "$$", "display": True},
                                {"left": "$", "right": "$", "display": False},
                                {"left": "\\(", "right": "\\)", "display": False},
                                {"left": "\\[", "right": "\\]", "display": True},]
                        )
            chat_input_components = create_chat_input_interface(
                placeholder="Ketik topik pencarian atau tempel URL YouTube..."
            )

            with gr.Row():
                search_engine_web = gr.Radio(
                    ["DuckDuckGo", "Google"],
                    label="Mesin Pencari",
                    value="DuckDuckGo"
                )
                search_button_web = gr.Button("🔍 Cari di Web", variant="secondary")

    components = {
        "chat_name_web": chat_name_web,
        "save_chat_web": save_chat_web,
        "load_chat_web": load_chat_web,
        "delete_chat_web": delete_chat_web,
        "chat_list_web": chat_list_web,
        "status_web": status_web,
        "memory_web_box": memory_web_box,
        "memory_web_input": memory_web_input,
        "add_mem_web_btn": add_mem_web_btn,
        "clear_mem_web_btn": clear_mem_web_btn,
        "auto_mem_web_check": auto_mem_web_check,
        "chatbot_web": chatbot_web,
        "search_engine_web": search_engine_web,
        "search_button_web": search_button_web,
        "memory_web_list": memory_web_list,
        "memory_web_delete_btn": memory_web_delete_btn,
    }
    
    components.update({"web_" + k: v for k, v in chat_input_components.items()})
    
    return components

def create_roleplay_tab():
    """Menciptakan semua komponen untuk tab Chat Roleplay."""
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("#### Manajemen Karakter")
            character_name = gr.Textbox(
                label="Nama Karakter",
                placeholder="misal: luna"
            )
            
            character_list = gr.Dropdown(
                label="Pilih Karakter",
                choices=[],
                allow_custom_value=True
            )
            
            ai_persona_box = gr.Textbox(
                label="Karakter yang Diperankan AI",
                lines=4,
                placeholder="Anda adalah AI yang..."
            )
            
            user_persona_box = gr.Textbox(
                label="Karakter yang Diperankan Saya (User)",
                lines=3,
                placeholder="Saya adalah seorang petualang..."
            )
            
            with gr.Row():
                save_char_btn = gr.Button("💾 Simpan Karakter")
                delete_char_btn = gr.Button("🗑️ Hapus Karakter")
            
            status_char = gr.Markdown("")
            
            pov_mode_rp = gr.Radio(
                ["Sudut Pandang Kedua (Interaktif)", "Sudut Pandang Ketiga (Naratif)"],
                label="Gaya Sudut Pandang",
                value="Sudut Pandang Kedua (Interaktif)"
            )
            
            gr.Markdown("#### Manajemen Sesi")
            chat_name_rp = gr.Textbox(
                label="Nama Sesi",
                placeholder="Otomatis..."
            )
            
            with gr.Row():
                save_chat_rp = gr.Button("💾 Simpan")
                load_chat_rp = gr.Button("📂 Muat")
                delete_chat_rp = gr.Button("🗑️ Hapus")
            
            chat_list_rp = gr.Dropdown(
                label="Pilih Sesi Tersimpan",
                choices=[],
                allow_custom_value=True
            )
            
            status_rp = gr.Markdown("")
            
            with gr.Accordion(" 🧠  Memori Jangka Panjang", open=False):
                gr.Markdown("Pilih atau buat topik memori untuk sesi ini.")
                with gr.Row():
                    memory_rp_list = gr.Dropdown(
                    label="Pilih Topik Memori",
                    choices=[], # Akan diisi saat aplikasi dimuat
                    interactive=True
                )
                memory_rp_delete_btn = gr.Button("🗑️ Hapus Topik")

                memory_rp_box = gr.Textbox(
                    label="Isi Memori (dari topik yang dipilih)",
                    lines=6,
                    interactive=False # Hanya menampilkan, tidak untuk diedit langsung
                )
                memory_rp_input = gr.Textbox(
                    label="Tambah Fakta ke Memori (topik terpilih)",
                    placeholder="misal: nama karakter saya adalah Elara"
                )
                with gr.Row():
                    add_mem_rp_btn = gr.Button("Simpan Fakta")
                    clear_mem_rp_btn = gr.Button("Kosongkan Isi Topik")

                auto_mem_rp_check = gr.Checkbox(
                    label="Update Memori Otomatis",
                    info="AI akan menyimpan fakta penting ke topik memori yang sedang aktif."
                )

        
        with gr.Column(scale=3):
            chatbot_rp = gr.Chatbot(height=500, 
                label="Chat Roleplay", 
                type="messages",
                latex_delimiters=[{"left": "$$", "right": "$$", "display": True},
                    {"left": "$", "right": "$", "display": False},
                    {"left": "\\(", "right": "\\)", "display": False},
                    {"left": "\\[", "right": "\\]", "display": True},]
            )  
            chat_input_components_rp = create_chat_input_interface()
            
            with gr.Accordion("🎙️ Kontrol Suara (Eksperimental)", open=False):
                with gr.Row():
                    audio_input_rp = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="Kirim Pesan Suara"
                    )
                    
                    auto_tts_rp_check = gr.Checkbox(
                        label="Putar Suara Otomatis",
                        info="Baca respons AI secara otomatis setelah dibuat."
                    )
                
                audio_output_rp = gr.Audio(
                    label="Respons Suara AI",
                    autoplay=True,
                    visible=True,
                    interactive=False
                )
    
    components = {
        "character_name": character_name,
        "character_list": character_list,
        "ai_persona_box": ai_persona_box,
        "user_persona_box": user_persona_box,
        "save_char_btn": save_char_btn,
        "delete_char_btn": delete_char_btn,
        "status_char": status_char,
        "pov_mode_rp": pov_mode_rp,
        "chat_name_rp": chat_name_rp,
        "save_chat_rp": save_chat_rp,
        "load_chat_rp": load_chat_rp,
        "delete_chat_rp": delete_chat_rp,
        "chat_list_rp": chat_list_rp,
        "status_rp": status_rp,
        "memory_rp_box": memory_rp_box,
        "memory_rp_input": memory_rp_input,
        "add_mem_rp_btn": add_mem_rp_btn,
        "clear_mem_rp_btn": clear_mem_rp_btn,
        "auto_mem_rp_check": auto_mem_rp_check,
        "chatbot_rp": chatbot_rp,
        "audio_input_rp": audio_input_rp,
        "auto_tts_rp_check": auto_tts_rp_check,
        "audio_output_rp": audio_output_rp,
        "memory_rp_list": memory_rp_list,
        "memory_rp_delete_btn": memory_rp_delete_btn,
    }
    
    components.update({"rp_" + k: v for k, v in chat_input_components_rp.items()})
    return components

def create_config_tab():
    """Menciptakan semua komponen untuk tab Konfigurasi."""
    with gr.Accordion("Pengaturan API & Fitur", open=True):
        api_provider_selector = gr.Radio(
            ["OpenRouter", "DeepSeek", "A4F", "LM Studio", "Blackbox AI", "Google Gemini"], # <-- "A4F" DITAMBAHKAN
            label="Pilih Penyedia API",
            value=global_settings.get("api_provider", "OpenRouter"),
            info="Pilih layanan yang ingin Anda gunakan."
        )
        
        with gr.Group(visible=global_settings.get("api_provider") == "OpenRouter") as openrouter_group:
            openrouter_api_key_box = gr.Textbox(
                label="OpenRouter API Key",
                type="password",
                value=global_settings.get("openrouter_api_key", "")
            )
        
        with gr.Group(visible=global_settings.get("api_provider") == "DeepSeek") as deepseek_group:
            deepseek_api_key_box = gr.Textbox(
                label="DeepSeek API Key",
                type="password",
                value=global_settings.get("deepseek_api_key", "")
            )
            gr.Markdown("Model yang digunakan adalah `deepseek-chat` (otomatis).")

        # --- GRUP BARU UNTUK A4F ---
        with gr.Group(visible=global_settings.get("api_provider") == "A4F") as a4f_group:
            a4f_api_key_box = gr.Textbox(
                label="A4F API Key",
                type="password",
                value=global_settings.get("a4f_api_key", "")
            )
            gr.Markdown("Pastikan Anda mengisi **Nama Model** di bawah (misal: `provider-1/gpt-4o`).")
        # --- AKHIR GRUP BARU ---
        
        with gr.Group(visible=global_settings.get("api_provider") == "LM Studio") as lmstudio_group:
            lmstudio_api_url_box = gr.Textbox(
                label="LM Studio API URL (Endpoint)",
                value=global_settings.get("lmstudio_api_url", "http://localhost:1234/v1"),
                info="Contoh: http://localhost:1234/v1"
            )
            gr.Markdown("Pastikan server lokal LM Studio Anda sedang berjalan.")
        
        with gr.Group(visible=global_settings.get("api_provider") == "Blackbox AI") as blackbox_group:
            blackbox_api_key_box = gr.Textbox(
                label="Blackbox AI API Key",
                type="password",
                value=global_settings.get("blackbox_api_key", "")
            )
            blackbox_model_name_box = gr.Textbox(
                label="Nama Model di Blackbox AI",
                value=global_settings.get("blackbox_model_name", "blackboxai/openai/gpt-4"),
                info="Contoh: blackboxai/openai/gpt-4"
            )

        with gr.Group() as google_search_group:
            gr.Markdown("#### Pengaturan Google Search API")
            google_api_key_box = gr.Textbox(label="Google API Key", type="password")
            google_cse_id_box = gr.Textbox(label="Google Search Engine ID (CX)", type="password")

        with gr.Group(visible=global_settings.get("api_provider") == "Google Gemini") as gemini_group:
            gemini_api_key_box = gr.Textbox(label="Google Gemini API Key", type="password")

            gemini_list_files_btn = gr.Button("📂 Daftar File di Server Gemini")
            gemini_file_list_box = gr.Textbox(
                label="File yang Tersimpan di Gemini (Otomatis terhapus setelah 48 jam)",
                interactive=False,
                lines=5
            )

        short_term_memory_slider = gr.Slider(minimum=2, maximum=50, value=20, step=2, label="Batas Memori Jangka Pendek (Jumlah Pesan)")

        model_name_box = gr.Textbox(
            label="Nama Model (OpenRouter/A4F/Gemini)", # <-- Label diubah
            value=global_settings.get("model_name", "google/gemini-flash-1.5"),
            info="Contoh A4F: provider-1/gpt-4o. Contoh OpenRouter: google/gemini-flash-1.5",
            visible=True # <-- Dibuat selalu terlihat karena A4F juga butuh
        )

        search_results_slider = gr.Slider(minimum=1, maximum=50, value=5, step=1, label="Jumlah Hasil Pencarian Web")
        max_articles_slider = gr.Slider(minimum=1, maximum=50, value=5, step=1, label="Maksimal Artikel Web yang Dibaca per Pencarian")
        
        save_settings_btn = gr.Button("💾 Simpan Pengaturan", variant="primary")
        status_settings = gr.Markdown("")
    
    with gr.Accordion("Pengaturan Tampilan", open=True):
        gr.Markdown("""
        ### Pilih Tema Tampilan
        - <a href="?__theme=soft" style="text-decoration: none;">⚪ Tema Terang (Soft)</a>
        - <a href="?__theme=dark" style="text-decoration: none;">⚫ Tema Gelap (Dark)</a>
        """)
    
    return {
        "api_provider_selector": api_provider_selector,
        "openrouter_group": openrouter_group,
        "deepseek_group": deepseek_group,
        "a4f_group": a4f_group, 
        "lmstudio_group": lmstudio_group,
        "blackbox_group": blackbox_group,
        "gemini_group": gemini_group,
        "a4f_api_key_box": a4f_api_key_box, 
        "blackbox_api_key_box": blackbox_api_key_box,
        "blackbox_model_name_box": blackbox_model_name_box,
        "openrouter_api_key_box": openrouter_api_key_box,
        "gemini_api_key_box": gemini_api_key_box,
        "model_name_box": model_name_box,
        "deepseek_api_key_box": deepseek_api_key_box,
        "lmstudio_api_url_box": lmstudio_api_url_box,
        "google_api_key_box": google_api_key_box, 
        "google_cse_id_box": google_cse_id_box,
        "search_results_slider": search_results_slider,
        "short_term_memory_slider": short_term_memory_slider,
        "max_articles_slider": max_articles_slider,
        "save_settings_btn": save_settings_btn,
        "status_settings": status_settings,
        "gemini_list_files_btn": gemini_list_files_btn,
        "gemini_file_list_box": gemini_file_list_box
    }

from backend_logic import load_memory # Pastikan Anda menambahkan import ini di bagian atas file jika belum ada

def create_vtuber_tab():
    """Menciptakan semua komponen untuk tab VTuber Live Chat."""
    with gr.Blocks() as vtuber_tab:
        gr.Markdown("### 🤖 VTuber Live Chat (Beta)")
        gr.Markdown("Hubungkan AI ke siaran langsung YouTube dan biarkan ia berinteraksi dengan penonton.")

        with gr.Row():
            # --- KOLOM KIRI (PENGATURAN) ---
            with gr.Column(scale=1):
                gr.Markdown("#### Pengaturan Karakter")
                vtuber_ai_persona = gr.Textbox(
                    label="Karakter yang Diperankan AI",
                    lines=8,
                    placeholder="Deskripsikan persona VTuber AI di sini..."
                )
                vtuber_user_persona = gr.Textbox(
                    label="Karakter yang Diperankan Saya (Streamer)",
                    lines=4,
                    placeholder="Deskripsikan peran Anda sebagai 'streamer' atau 'moderator'..."
                )
                auto_tts_vtuber_check = gr.Checkbox(
                    label="Putar Suara Otomatis",
                    value=True,
                    info="Baca respons AI secara otomatis."
                )
                status_vtuber = gr.Markdown("Status: Tidak Terhubung")

                gr.Markdown("#### Koneksi VTube Studio")
                vts_connect_button = gr.Button("🔌 Hubungkan ke VTS")
                vts_disconnect_button = gr.Button("❌ Putuskan dari VTS")
                status_vts = gr.Markdown("Status VTS: Tidak Terhubung")

                with gr.Accordion("Manajemen Sesi VTuber (Catatan)", open=False):
                    vtuber_chat_name = gr.Textbox(label="Nama Sesi", placeholder="Otomatis...")
                    with gr.Row():
                        vtuber_save_button = gr.Button("💾 Simpan")
                        vtuber_load_button = gr.Button("📂 Muat")
                        vtuber_delete_button = gr.Button("🗑️ Hapus")
                    vtuber_chat_list = gr.Dropdown(label="Pilih Sesi Tersimpan", choices=[], allow_custom_value=True)
                    status_simpan_vtuber = gr.Markdown("")
                
                with gr.Accordion("🧠 Filter Kata & Kepribadian (Memori)", open=True):
                    vtuber_memory_box = gr.Textbox(
                        label="Daftar Kata/Frasa yang Diblokir (satu per baris)",
                        lines=6,
                        interactive=False,
                        
                    )
                    vtuber_memory_input = gr.Textbox(
                        label="Tambah Kata/Frasa untuk Diblokir",
                        placeholder="misal: politik, sara, dll."
                    )
                    with gr.Row():
                        add_mem_vtuber_btn = gr.Button("Tambah ke Filter")
                        clear_mem_vtuber_btn = gr.Button("Kosongkan Filter")

            # --- KOLOM KANAN (KONTROL & TAMPILAN CHAT) ---
            with gr.Column(scale=3):
                gr.Markdown("#### Kontrol Siaran Langsung")
                youtube_url_input = gr.Textbox(
                    label="URL Live Stream YouTube",
                    placeholder="Tempel URL video siaran langsung di sini..."
                )
                with gr.Row():
                    connect_button = gr.Button("Hubungkan ke Live Chat", variant="primary")
                    disconnect_button = gr.Button("Putuskan Koneksi")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("##### 📥 Obrolan Masuk dari YouTube")
                        live_chat_display = gr.Textbox(
                            label="Live Chat", lines=10, interactive=False, autoscroll=True
                        )
                    with gr.Column():
                        gr.Markdown("##### 🤖 Respons AI VTuber")
                        vtuber_chatbot = gr.Chatbot(
                            label="Percakapan AI", 
                            height=300, 
                            type="messages",
                            latex_delimiters=[{"left": "$$", "right": "$$", "display": True},
                                {"left": "$", "right": "$", "display": False},
                                {"left": "\\(", "right": "\\)", "display": False},
                                {"left": "\\[", "right": "\\]", "display": True},]
                        )
                        vtuber_audio_output = gr.Audio(
                            label="Suara AI", autoplay=True, interactive=False
                        )
                
                gr.Markdown("---")
                gr.Markdown("#### Input Anda (Streamer)")
                with gr.Row():
                    vtuber_audio_input = gr.Audio(
                        sources=["microphone"], type="filepath", label="Kirim Pesan Suara"
                    )
                vtuber_user_input = gr.Textbox(
                    label="Ketik pesan untuk AI", placeholder="Ketik di sini untuk berinteraksi langsung dengan AI..."
                )
                vtuber_send_button = gr.Button("Kirim Pesan ke AI", variant="secondary")
                with gr.Row():
                    screen_vision_button = gr.Button("👁️ Analisis Layar", variant="secondary")
                    camera_vision_button = gr.Button("📸 Analisis Kamera (Prototipe)", variant="secondary")
                    live_vision_toggle_button = gr.Button("🔴 Mulai Pengamatan Live", variant="stop")
                vtuber_refresh_button = gr.Button("Refresh Internal", visible=False, elem_id="vtuber_refresh_btn_id")

    # --- DICTIONARY LENGKAP UNTUK DIKEMBALIKAN (RETURN) ---
    return {
        # Komponen Awal
        "vtuber_ai_persona": vtuber_ai_persona,
        "vtuber_user_persona": vtuber_user_persona,
        "auto_tts_vtuber_check": auto_tts_vtuber_check,
        "status_vtuber": status_vtuber,
        "youtube_url_input": youtube_url_input,
        "connect_button": connect_button,
        "disconnect_button": disconnect_button,
        "live_chat_display": live_chat_display,
        "vtuber_chatbot": vtuber_chatbot,
        "vtuber_audio_output": vtuber_audio_output,
        "vtuber_audio_input": vtuber_audio_input,
        "vtuber_user_input": vtuber_user_input,
        "vtuber_send_button": vtuber_send_button,
        "vtuber_refresh_button": vtuber_refresh_button,
        "vts_connect_button": vts_connect_button,
        "vts_disconnect_button": vts_disconnect_button,
        "status_vts": status_vts,
        "vtuber_chat_name": vtuber_chat_name,
        "vtuber_save_button": vtuber_save_button,
        "vtuber_load_button": vtuber_load_button,
        "vtuber_chat_list": vtuber_chat_list,
        "status_simpan_vtuber": status_simpan_vtuber,
        "vtuber_memory_box": vtuber_memory_box,
        "vtuber_memory_input": vtuber_memory_input,
        "add_mem_vtuber_btn": add_mem_vtuber_btn,
        "clear_mem_vtuber_btn": clear_mem_vtuber_btn,
        "vtuber_delete_button": vtuber_delete_button,
        "screen_vision_button": screen_vision_button,
        "camera_vision_button": camera_vision_button,
        "live_vision_toggle_button": live_vision_toggle_button,
    }

