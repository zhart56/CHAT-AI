import gradio as gr
import logging
import os
from config import (
    WEB_CHATS_DIR, RP_CHATS_DIR, CHARACTERS_DIR, DEFAULT_SYSTEM_PROMPT,
    MEMORY_WEB_DIR, MEMORY_RP_DIR, DATA_DIR, VTUBER_CHATS_DIR
)
from file_utils import (
    save_chat_history, load_chat_history, delete_chat_history, save_character,
    load_character, delete_character, add_to_memory, load_memory, clear_memory,
    save_settings, list_files_in_dir, load_settings, get_memory_list, delete_memory_file
)
# Fungsi-fungsi yang BENAR-BENAR ada di backend_logic.py
from backend_logic import (
    speech_to_text,
    get_ai_response_stream,
    build_prompt_with_memory,
    build_roleplay_prompt,
    process_user_web_search,
    process_chat_with_file,
    update_memory_automatically,
    live_chat_listener,
    process_chat_for_vtuber,
    text_to_speech,
    initialize_vts_plugin,
    disconnect_vts_plugin,
    control_mouth_with_audio,
    trigger_vts_hotkey,
    process_vtuber_response,
    capture_screen_to_base64, 
    capture_camera_to_base64, 
    process_vision_for_vtuber,
    live_screen_observer,
    list_gemini_files
)
import threading # Sudah ada dari langkah sebelumnya, pastikan ada
from urllib.parse import urlparse, parse_qs
import asyncio

logger = logging.getLogger(__name__)
# --- TAMBAHKAN VARIABEL GLOBAL DI SINI ---
VTS_PLUGIN_INSTANCE = None

# -- FUNGSI PEMBANTU & WRAPPERS --
def get_last_ai_response(chat_history):
    """Mendapatkan konten dari respons terakhir AI dalam riwayat obrolan."""
    if not chat_history:
        return ""
    
    last_entry = chat_history[-1]
    if last_entry and last_entry.get('role') == 'assistant':
        return last_entry.get('content', '')
    
    return ""

# -- FUNGSI PEMBANTU UI BARU --
def on_stop_generating_web():
    """Mengaktifkan kembali UI untuk tab Web dengan benar."""
    return (
        gr.update(),
        gr.update(),
        gr.update(interactive=True),
        gr.update(value="", interactive=True),
        gr.update(visible=True, interactive=True, value="Kirim Pesan"), # <-- TEKS TOMBOL DITAMBAHKAN
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(interactive=True, value="🔍 Cari di Web")
    )

def on_stop_generating_rp():
    """Mengaktifkan kembali UI untuk tab Roleplay."""
    return (
        gr.update(interactive=True),  # user_input
        gr.update(interactive=True, value="Kirim Pesan"),  # send_button
        gr.update(visible=False),  # stop_button
        gr.update(interactive=True),  # file_upload
        gr.update(interactive=True)  # audio_input_rp
    )

# -- WRAPPERS STREAMING --
def web_chat_wrapper(user_input, history, memory, auto_mem, memory_filename):
        if not user_input or not user_input.strip():
            # Yield 10 item, cocok dengan WEB_UI_OUTPUTS
            yield history, memory, None, user_input, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            return

        # Nonaktifkan UI (yield 10 item)
        yield (history, memory, None, gr.update(interactive=False),
            gr.update(interactive=False, value="⏳ Sedang mengerjakan..."),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(interactive=False))
        
        # Proses streaming...
        new_history = history + [{"role": "user", "content": user_input}]
        new_history.append({"role": "assistant", "content": ""})
        final_system_prompt = build_prompt_with_memory(DEFAULT_SYSTEM_PROMPT, memory)
        stream = get_ai_response_stream(new_history[:-1], final_system_prompt)
        
        full_response = ""
        for chunk in stream:
            if isinstance(chunk, str) and not chunk.startswith("__ERROR__:"):
                full_response += chunk
                new_history[-1]['content'] = full_response
                yield (
                    new_history, 
                    gr.update(), gr.update(), gr.update(), gr.update(), 
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            )
    
        
        final_history = new_history
        memory_update = memory
        if auto_mem:
            memory_update = update_memory_automatically(final_history, MEMORY_WEB_DIR, memory_filename)
        
        # Aktifkan kembali UI (yield 10 item)
        yield (final_history, memory_update, None, gr.update(value="", interactive=True),
            gr.update(visible=True, interactive=True, value="Kirim Pesan"),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(interactive=True))



def rp_chat_wrapper(user_input, history, ai_persona, user_persona, pov, memory_content, auto_mem, auto_tts, memory_filename):
    if not user_input or not user_input.strip():
        yield history, None, memory_content, user_input, gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        return

    yield (history, None, memory_content, gr.update(interactive=False),
        gr.update(interactive=False, value="⏳ AI sedang berpikir..."),
        gr.update(visible=True), gr.update(interactive=False), gr.update(interactive=False),
        gr.update()) 



    # Siapkan data dan panggil fungsi backend baru
    new_history = history + [{"role": "user", "content": user_input}]
    final_system_prompt, _ = build_roleplay_prompt(ai_persona, user_persona, pov, memory_content)

    # Menjalankan fungsi async
    try:
        text_response, audio_path, emotion = asyncio.run(
            process_vtuber_response(new_history, final_system_prompt)
        )
        final_history = new_history + [{"role": "assistant", "content": text_response}]

        # Update memori jika diaktifkan
        memory_update = memory_content
        if auto_mem and memory_filename:
            # Memanggil fungsi update memori yang sudah dimodifikasi
            update_memory_automatically(final_history, MEMORY_RP_DIR, memory_filename)
            memory_update = load_memory(MEMORY_RP_DIR, memory_filename)
        else:
            memory_update = memory_content

    except Exception as e:
        logger.error(f"Error besar di rp_chat_wrapper: {e}")
        error_message = f"Terjadi error: {e}"
        final_history = new_history + [{"role": "assistant", "content": error_message}]
        audio_path, memory_update = None, memory_content

    # Yield terakhir untuk mengaktifkan kembali UI (8 item)
    final_ui_updates = on_stop_generating_rp() # Ini mengembalikan 5 item
    yield (
        final_history,           # 1. chatbot
        audio_path,              # 2. audio_output
        memory_update,           # 3. memory_box
        final_ui_updates[0],     # 4. rp_user_input
        final_ui_updates[1],     # 5. rp_send_button
        final_ui_updates[2],     # 6. rp_stop_button
        final_ui_updates[3],     # 7. rp_file_upload
        final_ui_updates[4],     # 8. audio_input_rp
        gr.update()              # 9. character_name (tidak diubah)
    )

def web_search_wrapper(user_input, history, search_engine, memory, auto_mem, memory_filename):
    # 1. Nonaktifkan UI dan UBAH TEKS TOMBOL menjadi "Sedang mengerjakan..."
    yield (history, memory, None, gr.update(interactive=False), 
        gr.update(interactive=False, value="⏳ Sedang mengerjakan..."), # <-- PERUBAHAN DI SINI
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), 
        gr.update(visible=True), gr.update(interactive=False))

    final_history = history
    try:
        gen = process_user_web_search(user_input, history, search_engine, memory)
        for chat_update, _ in gen:
            final_history = chat_update
            # 2. PERBAIKAN PENTING: Gunakan gr.update() agar tombol tidak berubah menjadi "None"
            # Yield ini hanya akan mengubah chatbot, komponen lain dibiarkan apa adanya.
            yield (final_history, gr.update(), gr.update(), gr.update(), gr.update(), 
                gr.update(), gr.update(), gr.update(), gr.update(), gr.update())
    finally:
        # 3. Update memori setelah selesai
        memory_update = memory
        if auto_mem and final_history and memory_filename:
            memory_update = update_memory_automatically(final_history, MEMORY_WEB_DIR, memory_filename)

        # 4. Aktifkan kembali UI dan KEMBALIKAN TEKS TOMBOL ke "Kirim Pesan"
        yield (final_history, memory_update, None, 
            gr.update(value="", interactive=True), 
            gr.update(visible=True, interactive=True, value="Kirim Pesan"), # <-- PERUBAHAN DI SINI
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), 
            gr.update(visible=False), gr.update(interactive=True))

def web_file_wrapper_base(user_input, history, file_objs, mode, memory, auto_mem, memory_filename):
    """Wrapper dasar untuk menangani file, KINI MENERUSKAN SEMUA FILE SEKALIGUS."""
    
    # file_objs sekarang adalah sebuah LIST
    if not file_objs:
        yield history, memory, None, user_input, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        return

    # Tidak ada lagi loop di sini. Langsung panggil backend dengan seluruh daftar file.
    gen = process_chat_with_file(user_input, history, file_objs, mode, DEFAULT_SYSTEM_PROMPT, memory)
    
    final_history = history # Inisialisasi
    for outputs in gen:
        # Langsung yield semua output dari backend
        final_history = outputs[0]
        yield outputs
    
    # Update memori sekali saja setelah semua proses selesai
    memory_update = memory
    if auto_mem:
        memory_update = update_memory_automatically(final_history, MEMORY_WEB_DIR, memory_filename)
    
    # Kirim update terakhir untuk memori jika ada perubahan
    yield final_history, memory_update, gr.update(value=None), gr.update(value="", interactive=True), gr.update(visible=True, interactive=True, value="Kirim Pesan"), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(interactive=True)


def web_vision_wrapper(user_input, history, file_obj, memory, auto_mem, memory_filename):
    yield from web_file_wrapper_base(user_input, history, file_obj, "vision", memory, auto_mem, memory_filename)

def web_ocr_wrapper(user_input, history, file_obj, memory, auto_mem, memory_filename):
    yield from web_file_wrapper_base(user_input, history, file_obj, "ocr", memory, auto_mem, memory_filename)

def web_doc_wrapper(user_input, history, file_obj, memory, auto_mem, memory_filename):
    yield from web_file_wrapper_base(user_input, history, file_obj, "doc", memory, auto_mem, memory_filename)


def rp_file_wrapper_base(user_input, history, file_obj, mode, ai_persona, user_persona, pov, memory, auto_mem, auto_tts, memory_filename):
    final_system_prompt, _ = build_roleplay_prompt(ai_persona, user_persona, pov, memory)
    
    # Panggil backend yang sudah pintar
    gen = process_chat_with_file(user_input, history, file_obj, mode, final_system_prompt, memory)
    
    final_history = history
    final_outputs = None
    for outputs in gen:
        # Langsung teruskan semua 10 output dari backend
        final_history = outputs[0]
        final_outputs = outputs
        # Untuk Roleplay, kita hanya butuh 9 output, jadi kita potong yang terakhir
        yield outputs[:-1] 

    # Update memori setelah selesai
    memory_update = memory
    if auto_mem and memory_filename:
        memory_update = update_memory_automatically(final_history, MEMORY_RP_DIR, memory_filename)

    # Dapatkan respons teks terakhir untuk TTS
    last_response = get_last_ai_response(final_history)
    audio_path = text_to_speech(last_response) if auto_tts else None

    # Kirim update terakhir untuk memori dan audio
    if final_outputs:
        final_outputs = list(final_outputs)
        final_outputs[1] = memory_update  # Update memory_rp_box
        final_outputs[7] = audio_path     # Update audio_output_rp
        yield tuple(final_outputs[:-1])

def rp_vision_wrapper(user_input, history, file_obj, ai_persona, user_persona, pov, memory, auto_mem, auto_tts, memory_filename):
    yield from rp_file_wrapper_base(user_input, history, file_obj, "vision", ai_persona, user_persona, pov, memory, auto_mem, auto_tts, memory_filename)

def rp_ocr_wrapper(user_input, history, file_obj, ai_persona, user_persona, pov, memory, auto_mem, auto_tts, memory_filename):
    yield from rp_file_wrapper_base(user_input, history, file_obj, "ocr", ai_persona, user_persona, pov, memory, auto_mem, auto_tts, memory_filename)

def rp_doc_wrapper(user_input, history, file_obj, ai_persona, user_persona, pov, memory, auto_mem, auto_tts, memory_filename):
    yield from rp_file_wrapper_base(user_input, history, file_obj, "doc", ai_persona, user_persona, pov, memory, auto_mem, auto_tts, memory_filename)

def load_chat_wrapper(chat_name, directory):
    history, status = load_chat_history(chat_name, directory)
    return history, status, chat_name

def delete_chat_wrapper(chat_name, directory):
    status, chat_list_update = delete_chat_history(chat_name, directory)
    return status, chat_list_update, ""

def toggle_api_provider_ui(provider):
    # Tuple berisi 6 boolean untuk grup provider
    vis_groups = [False] * 6 
    if provider == "DeepSeek": vis_groups[1] = True
    elif provider == "A4F": vis_groups[2] = True
    elif provider == "LM Studio": vis_groups[3] = True
    elif provider == "Blackbox AI": vis_groups[4] = True
    elif provider == "Google Gemini": vis_groups[5] = True
    else: vis_groups[0] = True # Default ke OpenRouter

    # Tentukan visibilitas untuk model_name_box secara terpisah
    # Tampil hanya jika providernya butuh input model
    vis_model_box = provider in ["OpenRouter", "Google Gemini", "A4F"]

    # Gabungkan semua update menjadi satu tuple
    return tuple(gr.update(visible=v) for v in vis_groups) + (gr.update(visible=vis_model_box),)

def on_load(web_memory_state, rp_memory_state):
    settings = load_settings()
    api_provider = settings.get("api_provider", "OpenRouter")
    or_key = settings.get("openrouter_api_key", "")
    ds_key = settings.get("deepseek_api_key", "")
    a4f_key = settings.get("a4f_api_key", "") # <-- BARU
    bb_key = settings.get("blackbox_api_key", "")
    bb_model = settings.get("blackbox_model_name", "blackboxai/openai/gpt-4")
    lm_url = settings.get("lmstudio_api_url", "http://localhost:1234/v1")
    model = settings.get("model_name", "google/gemini-flash-1.5")
    search_count = settings.get("search_results_count", 5)
    gemini_key = settings.get("gemini_api_key", "")
    short_term_limit = settings.get("short_term_memory_limit", 20)
    max_articles = settings.get("max_articles_to_read", 5)

    web_chats = list_files_in_dir(WEB_CHATS_DIR)
    rp_chats = list_files_in_dir(RP_CHATS_DIR)
    chars = list_files_in_dir(CHARACTERS_DIR)
    vtuber_chats = list_files_in_dir(VTUBER_CHATS_DIR)
    web_memories = get_memory_list(MEMORY_WEB_DIR)
    rp_memories = get_memory_list(MEMORY_RP_DIR)
    vtuber_memory_content = load_memory(DATA_DIR, "vtuber_filter.txt")

    return (
        api_provider, or_key, ds_key, a4f_key, # <-- BARU
        bb_key, bb_model, lm_url, model, search_count,
        gr.update(choices=web_chats), gr.update(choices=rp_chats),
        gr.update(choices=chars), gr.update(choices=vtuber_chats),
        web_memory_state, rp_memory_state, gr.update(choices=web_memories),
        gr.update(choices=rp_memories), settings.get("google_api_key", ""),  
        settings.get("google_cse_id", ""), gemini_key, short_term_limit,
        max_articles, vtuber_memory_content
    )

def handle_file_upload(files):
    """
    Menangani visibilitas tombol berdasarkan tipe file yang diunggah.
    Mendukung multi-file dan mempertahankan 'value' untuk mencegah bug.
    """
    # Jika tidak ada file (None) atau daftar file kosong
    if not files:
        return (
            gr.update(visible=True, interactive=True, value="Kirim Pesan"), 
            gr.update(visible=False, value="🖼️ Vision"), 
            gr.update(visible=False, value="📄 OCR"), 
            gr.update(visible=False, value="📄 Dokumen")
        )
    
    # Ambil file pertama dari daftar untuk menentukan tipe
    first_file = files[0] if isinstance(files, list) else files
    filename = first_file.name.lower()
    
    if filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
        # File gambar: Tombol Vision dan OCR muncul
        return (
            gr.update(visible=False, value="Kirim Pesan"), 
            gr.update(visible=True, interactive=True, value="🖼️ Vision"), 
            gr.update(visible=True, interactive=True, value="📄 OCR"), 
            gr.update(visible=False, value="📄 Dokumen")
        )
        
    elif filename.endswith(('.pdf', '.docx', '.txt')):
        # File dokumen: Tombol Dokumen muncul
        return (
            gr.update(visible=False, value="Kirim Pesan"), 
            gr.update(visible=False, value="🖼️ Vision"), 
            gr.update(visible=False, value="📄 OCR"), 
            gr.update(visible=True, interactive=True, value="📄 Dokumen")
        )
        
    else:
        # Tipe file lain: Kembali ke keadaan default
        return (
            gr.update(visible=True, interactive=True, value="Kirim Pesan"), 
            gr.update(visible=False, value="🖼️ Vision"), 
            gr.update(visible=False, value="📄 OCR"), 
            gr.update(visible=False, value="📄 Dokumen")
        )

def extract_video_id(url):
    """Mengekstrak ID video dari berbagai format URL YouTube."""
    try:
        parsed_url = urlparse(url)
        if "youtube.com" in parsed_url.hostname:
            if parsed_url.path == "/watch":
                return parse_qs(parsed_url.query)['v'][0]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]
        elif "youtu.be" in parsed_url.hostname:
            return parsed_url.path[1:]
    except Exception as e:
        logger.error(f"Gagal mengekstrak video ID: {e}")
        return None
    return None

def connect_to_youtube(url, current_thread, current_stop_event, message_queue):
    """Fungsi yang dipanggil saat tombol 'Hubungkan' ditekan."""
    if current_thread and current_thread.is_alive():
        return "Sudah terhubung.", current_thread, current_stop_event, gr.update(interactive=False), gr.update(interactive=True)

    video_id = extract_video_id(url)
    if not video_id:
        return "URL YouTube tidak valid.", None, None, gr.update(interactive=True), gr.update(interactive=False)

    message_queue.clear() # Bersihkan antrian pesan lama
    stop_event = threading.Event()
    thread = threading.Thread(
        target=live_chat_listener,
        args=(video_id, stop_event, message_queue)
    )
    thread.start()

    status_update = f"Terhubung ke video ID: {video_id}. Mendengarkan chat..."
    return status_update, thread, stop_event, gr.update(interactive=False), gr.update(interactive=True)

def disconnect_from_youtube(thread, stop_event):
    """Fungsi yang dipanggil saat tombol 'Putuskan' ditekan."""
    if thread and thread.is_alive() and stop_event:
        stop_event.set() # Kirim sinyal berhenti
        thread.join(timeout=5) # Tunggu thread selesai
        return "Koneksi diputus.", None, None, gr.update(interactive=True), gr.update(interactive=False)
    return "Tidak ada koneksi aktif.", None, None, gr.update(interactive=True), gr.update(interactive=False)

# Di file ui/event_handlers.py

# Di ui/event_handlers.py

# Kembalikan ke 4 parameter
def update_vtuber_ui(message_queue, chat_history, ai_persona, user_persona, memory_content):
    """Fungsi yang berjalan periodik untuk update UI dan memicu AI."""
    if not message_queue:
        return gr.update(), gr.update(), gr.update()

    new_messages = list(message_queue)
    display_text = "\n".join(new_messages)
    message_queue.clear()

    if new_messages and new_messages[0].startswith("__ERROR__:"):
        return display_text, chat_history, None

    ai_response_text, audio_path = process_chat_for_vtuber(
        new_messages, chat_history, ai_persona, user_persona, memory_content)

    # --- Gunakan VARIABEL GLOBAL di sini ---
    if audio_path and VTS_PLUGIN_INSTANCE: # <-- Gunakan VTS_PLUGIN_INSTANCE
        try:
            logger.info("Memicu animasi mulut VTube Studio...")
            asyncio.run(control_mouth_with_audio(audio_path))
        except Exception as e:
            logger.error(f"Gagal menjalankan control_mouth_with_audio: {e}")
    # --- AKHIR PERUBAHAN ---

    if not ai_response_text.startswith("__ERROR__:"):
        chat_history.append({"role": "user", "content": f"[Konteks dari live chat: {len(new_messages)} pesan baru]"})
        chat_history.append({"role": "assistant", "content": ai_response_text})

    return display_text, chat_history, audio_path

# Di dalam event_handlers.py, sebelum register_event_handlers()

# Di ui/event_handlers.py

def vts_connect_wrapper():
    """Wrapper untuk menjalankan fungsi async initialize_vts_plugin."""
    global VTS_PLUGIN_INSTANCE # <-- Tambahkan ini
    try:
        status, plugin = asyncio.run(initialize_vts_plugin())
        VTS_PLUGIN_INSTANCE = plugin # <-- Simpan plugin ke variabel global
        return status
    except Exception as e:
        VTS_PLUGIN_INSTANCE = None # <-- Pastikan None jika gagal
        return f"Error: {e}"

def vts_disconnect_wrapper():
    """Wrapper untuk menjalankan fungsi async disconnect_vts_plugin."""
    global VTS_PLUGIN_INSTANCE # <-- Tambahkan ini
    try:
        status = asyncio.run(disconnect_vts_plugin())
        VTS_PLUGIN_INSTANCE = None # <-- Set ke None saat disconnect
        return status
    except Exception as e:
        VTS_PLUGIN_INSTANCE = None # <-- Pastikan None jika error
        return f"Error: {e}"


def register_event_handlers(demo, comps, states):
    """Fungsi sentral untuk mendaftarkan semua event handler."""
    
    demo.load(
        lambda: on_load(states['web_memory_state'].value, states['rp_memory_state'].value),
        None,
        [
            comps['api_provider_selector'], comps['openrouter_api_key_box'],
            comps['deepseek_api_key_box'], comps['a4f_api_key_box'], # <-- BARU
            comps['blackbox_api_key_box'], comps['blackbox_model_name_box'],
            comps['lmstudio_api_url_box'], comps['model_name_box'],
            comps['search_results_slider'], comps['chat_list_web'],
            comps['chat_list_rp'], comps['character_list'],
            comps['vtuber_chat_list'], comps['memory_web_box'],
            comps['memory_rp_box'], comps['memory_web_list'],
            comps['memory_rp_list'], comps['google_api_key_box'],     
            comps['google_cse_id_box'], comps['gemini_api_key_box'],
            comps['short_term_memory_slider'], comps['max_articles_slider'],
            comps['vtuber_memory_box']
        ]
    ).then( # <-- TAMBAHKAN .THEN() DI SINI UNTUK MEMULAI LOOP VTUBER
        fn=None,
        inputs=None,
        outputs=None,
        js="""
        () => {
            setTimeout(() => {
                document.getElementById('vtuber_refresh_btn_id').click();
            }, 5000);
        }
        """
    )
    
    save_inputs = [
        comps['api_provider_selector'],     # provider
        comps['openrouter_api_key_box'],    # or_key
        comps['deepseek_api_key_box'],      # ds_key
        comps['a4f_api_key_box'],           # a4f_key
        comps['blackbox_api_key_box'],      # bb_key
        comps['blackbox_model_name_box'],   # bb_model
        comps['lmstudio_api_url_box'],      # lm_url
        comps['model_name_box'],            # model_name
        comps['search_results_slider'],     # search_count
        comps['google_api_key_box'],        # google_key
        comps['google_cse_id_box'],         # google_cx
        comps['gemini_api_key_box'],        # gemini_key
        comps['short_term_memory_slider'],  # short_term_limit
        comps['max_articles_slider']        # max_articles
    ]
    
    comps['save_settings_btn'].click(
        save_settings,
        save_inputs,
        [comps['status_settings']]
    )
    
    comps['api_provider_selector'].change(
    toggle_api_provider_ui,
    comps['api_provider_selector'],
    [
        comps['openrouter_group'],      
        comps['deepseek_group'],        
        comps['a4f_group'],             
        comps['lmstudio_group'],        
        comps['blackbox_group'],       
        comps['gemini_group'],          
        comps['model_name_box']         
    ]
    )
    
    # -- Event Handlers untuk Chat Web --
    WEB_UI_OUTPUTS = [
        comps['chatbot_web'], comps['memory_web_box'], comps['web_file_upload'],
        comps['web_user_input'], comps['web_send_button'], comps['web_send_vision'],
        comps['web_send_ocr'], comps['web_send_doc'], comps['web_stop_button'],
        comps['search_button_web']
    ]
    
    web_file_buttons_only = [
        comps['web_send_button'],
        comps['web_send_vision'],
        comps['web_send_ocr'],
        comps['web_send_doc']
    ]
    
    comps['web_file_upload'].upload(
        handle_file_upload,
        comps['web_file_upload'],
        web_file_buttons_only,
        show_progress="hidden"
    )
    
    comps['web_file_upload'].clear(
        handle_file_upload,
        comps['web_file_upload'],
        web_file_buttons_only,
        show_progress="hidden"
    )
    
    web_chat_inputs = [
        comps['web_user_input'],
        comps['chatbot_web'],
        comps['memory_web_box'],      
        comps['auto_mem_web_check'],
        comps['memory_web_list']  
    ] 
    
    web_send_event = comps['web_send_button'].click(
        fn=lambda: gr.update(value=None), inputs=None, outputs=[comps['web_file_upload']], queue=False
    ).then(fn=web_chat_wrapper, inputs=web_chat_inputs, outputs=WEB_UI_OUTPUTS)

    web_submit_event = comps['web_user_input'].submit(
        fn=lambda: gr.update(value=None), inputs=None, outputs=[comps['web_file_upload']], queue=False
    ).then(fn=web_chat_wrapper, inputs=web_chat_inputs, outputs=WEB_UI_OUTPUTS)
    
    web_search_inputs = [
        comps['web_user_input'],
        comps['chatbot_web'],
        comps['search_engine_web'],
        comps['memory_web_box'],      
        comps['auto_mem_web_check'],
        comps['memory_web_list']       
    ]
    
    web_search_event = comps['search_button_web'].click(
        web_search_wrapper,
        web_search_inputs,
        WEB_UI_OUTPUTS
    )
    
    web_file_inputs = [
        comps['web_user_input'],
        comps['chatbot_web'],
        comps['web_file_upload'],
        comps['memory_web_box'],      
        comps['auto_mem_web_check'],
        comps['memory_web_list']
    ]
    
    web_vision_event = comps['web_send_vision'].click(
        web_vision_wrapper,
        web_file_inputs,
        WEB_UI_OUTPUTS
    )
    
    web_ocr_event = comps['web_send_ocr'].click(
        web_ocr_wrapper,
        web_file_inputs,
        WEB_UI_OUTPUTS
    )
    
    web_doc_event = comps['web_send_doc'].click(
        web_doc_wrapper,
        web_file_inputs,
        WEB_UI_OUTPUTS
    )
    
    web_stoppable_ui_controls = [
        comps['web_user_input'],
        comps['web_send_button'],
        comps['web_send_vision'],
        comps['web_send_ocr'],
        comps['web_send_doc'],
        comps['web_stop_button'],
        comps['web_file_upload'],
        comps['search_button_web']
    ]

    comps['web_stop_button'].click(
    fn=on_stop_generating_web, # <-- Hubungkan ke fungsi reset
    inputs=None,
    outputs=WEB_UI_OUTPUTS, # Gunakan daftar output yang lengkap
    cancels=[web_send_event, web_submit_event, web_search_event, web_vision_event, web_ocr_event, web_doc_event]
    )
    
    comps['save_chat_web'].click(
        lambda h, n: save_chat_history(h, n, WEB_CHATS_DIR, "web_chat"),
        [comps['chatbot_web'], comps['chat_name_web']],
        [comps['status_web'], comps['chat_list_web']],
        preprocess=False
    )
    
    comps['chat_list_web'].select(
        fn=lambda chat_name: chat_name, # Cukup pindahkan nama file yang dipilih
        inputs=comps['chat_list_web'],
        outputs=comps['chat_name_web']
    )
    
    comps['load_chat_web'].click(
        lambda n: load_chat_history(n, WEB_CHATS_DIR) + (n,),
        comps['chat_name_web'],
        [comps['chatbot_web'], comps['status_web'], comps['chat_name_web']]
    )
    
    comps['delete_chat_web'].click(
        lambda n: delete_chat_history(n, WEB_CHATS_DIR) + ("",),
        comps['chat_list_web'],
        [comps['status_web'], comps['chat_list_web'], comps['chat_name_web']]
    )
    
    comps['add_mem_web_btn'].click(
        fn=add_to_memory, # Langsung panggil fungsi aslinya
        inputs=[gr.State(MEMORY_WEB_DIR), comps['memory_web_list'], comps['memory_web_input']], # Berikan direktori sebagai state
        outputs=[comps['status_web'], comps['memory_web_box']]
    ).then(lambda: "", None, comps['memory_web_input'])

# Event untuk tombol kosongkan memori web
    comps['clear_mem_web_btn'].click(
        fn=lambda filename: (
            clear_memory(MEMORY_WEB_DIR, filename),
            "" # Langsung kosongkan box
        ),
        inputs=[comps['memory_web_list']], # Cukup ambil nama file yang dipilih
        outputs=[comps['status_web'], comps['memory_web_box']]
    )
    
    comps['vtuber_audio_input'].change(
        speech_to_text,
        comps['vtuber_audio_input'],
        comps['vtuber_user_input']
    )

    # Definisikan input untuk chat VTuber
    vtuber_chat_inputs = [
        comps['vtuber_user_input'],
        comps['vtuber_chatbot'],
        comps['vtuber_ai_persona'],
        comps['vtuber_user_persona'],
        # Tambahkan komponen lain jika dibutuhkan di masa depan
    ]
    
    # Definisikan output untuk chat VTuber
    vtuber_chat_outputs = [
        comps['vtuber_chatbot'],
        comps['vtuber_audio_output'],
        comps['vtuber_user_input'] 
    ]

    vision_inputs = [
        comps['vtuber_chatbot'],
        comps['vtuber_ai_persona'],
        comps['vtuber_user_persona'],
        comps['vtuber_memory_box']
    ]
    vision_outputs = [
        comps['vtuber_chatbot'],
        comps['vtuber_audio_output']
    ]

    comps['screen_vision_button'].click(
        fn=screen_vision_wrapper,
        inputs=vision_inputs,
        outputs=vision_outputs
    )

    comps['camera_vision_button'].click(
        fn=camera_vision_wrapper,
        inputs=vision_inputs,
        outputs=vision_outputs
    )
    
    comps['live_vision_toggle_button'].click(
    fn=toggle_live_observation_wrapper,
    inputs=[
        states['live_observer_thread_state'],
        states['live_observer_stop_event_state'],
        states['vtuber_message_queue_state'] # Kita bisa gunakan message queue yang sama
    ],
    outputs=[
        comps['live_vision_toggle_button'],
        states['live_observer_thread_state'],
        states['live_observer_stop_event_state']
    ]
    )

    comps['memory_rp_list'].select(
        fn=lambda filename: load_memory(MEMORY_RP_DIR, filename),
        inputs=[comps['memory_rp_list']],
        outputs=[comps['memory_rp_box']]
    )

    comps['add_mem_rp_btn'].click(
        fn=add_to_memory, # Langsung panggil fungsi aslinya
        inputs=[gr.State(MEMORY_RP_DIR), comps['memory_rp_list'], comps['memory_rp_input']], # Berikan direktori sebagai state
        outputs=[comps['status_rp'], comps['memory_rp_box']]
    ).then(lambda: "", None, comps['memory_rp_input'])

    comps['clear_mem_rp_btn'].click(
        fn=lambda filename: clear_memory(MEMORY_RP_DIR, filename),
        inputs=[comps['memory_rp_list']],
        outputs=[comps['status_rp'], comps['memory_rp_box']]
    )

    comps['memory_rp_delete_btn'].click(
        fn=lambda filename: delete_memory_file(MEMORY_RP_DIR, filename),
        inputs=[comps['memory_rp_list']],
        outputs=[comps['status_rp'], comps['memory_rp_list']]
    )

    RP_UNIFIED_OUTPUTS = [
    comps['chatbot_rp'],         # 1. Chatbot
    comps['rp_user_input'],      # 2. Kotak input pengguna
    comps['rp_file_upload'],     # 3. Tombol upload file
    comps['rp_send_button'],     # 4. Tombol kirim
    comps['rp_send_vision'],     # 5. Tombol vision
    comps['rp_send_ocr'],        # 6. Tombol ocr
    comps['rp_send_doc'],        # 7. Tombol doc
    comps['audio_output_rp'],    # 8. Output audio
    comps['memory_rp_box']       # 9. Kotak memori
    ]

    comps['memory_web_list'].select(
        fn=lambda filename: load_memory(MEMORY_WEB_DIR, filename),
        inputs=[comps['memory_web_list']],
        outputs=[comps['memory_web_box']]
    )

    comps['clear_mem_web_btn'].click(
        fn=lambda filename: (
            clear_memory(MEMORY_WEB_DIR, filename),
            "" # Langsung kosongkan box
        ),
        inputs=[comps['memory_web_list']],
        outputs=[comps['status_web'], comps['memory_web_box']]
    )

    comps['memory_web_delete_btn'].click(
        fn=lambda filename: delete_memory_file(MEMORY_WEB_DIR, filename),
        inputs=[comps['memory_web_list']],
        outputs=[comps['status_web'], comps['memory_web_list']]
    )

    comps['gemini_list_files_btn'].click(
        fn=list_gemini_files,
        inputs=[comps['gemini_api_key_box']],
        outputs=[comps['gemini_file_list_box']]
    )

    # Kita buat fungsi wrapper sederhana untuk chat langsung (belum termasuk logika YouTube)
    def vtuber_chat_wrapper(user_input, history, ai_persona, user_persona):
        if not user_input or not user_input.strip():
            yield history, None, user_input
            return
        
        # Tambahkan input ke history
        new_history = history + [{"role": "user", "content": user_input}]
        yield new_history, None, gr.update(interactive=False)
        
        # Buat system prompt dari persona
        # Kita bisa gunakan fungsi build_roleplay_prompt yang sudah ada
        system_prompt, _ = build_roleplay_prompt(ai_persona, user_persona, "Sudut Pandang Kedua (Interaktif)", "")
        
        # Dapatkan respons AI
        stream = get_ai_response_stream(new_history, system_prompt)
        ai_response = ""
        new_history.append({"role": "assistant", "content": ""})
        for chunk in stream:
            if isinstance(chunk, str) and not chunk.startswith("__ERROR__:"):
                ai_response += chunk
                new_history[-1]['content'] = ai_response
                yield new_history, None, gr.update(interactive=False)
        
        # Buat audio dari respons
        audio_path = text_to_speech(ai_response)
        
        # Hasil akhir
        yield new_history, audio_path, gr.update(interactive=True, value="")

    # Daftarkan event untuk tombol kirim pesan
    comps['vtuber_send_button'].click(
        vtuber_chat_wrapper,
        vtuber_chat_inputs,
        vtuber_chat_outputs
    )

    # -- Event Handlers untuk Chat Roleplay --
    rp_ui_controls = [
        comps['rp_user_input'],
        comps['rp_send_button'],
        comps['rp_stop_button'],
        comps['rp_file_upload'],
        comps['audio_input_rp']
    ]
    
    chat_outputs_rp = [
        comps['chatbot_rp'], comps['audio_output_rp'], comps['memory_rp_box'],
        comps['rp_user_input'], comps['rp_send_button'], comps['rp_stop_button'],
        comps['rp_file_upload'], comps['audio_input_rp'],
        comps['character_name']
    ]

    
    rp_file_buttons_only = [
        comps['rp_send_button'],
        comps['rp_send_vision'],
        comps['rp_send_ocr'],
        comps['rp_send_doc']
    ]
    
    comps['rp_file_upload'].upload(
        handle_file_upload,
        comps['rp_file_upload'],
        rp_file_buttons_only,
        show_progress="hidden"
    )
    
    comps['rp_file_upload'].clear(
        handle_file_upload,
        comps['rp_file_upload'],
        rp_file_buttons_only,
        show_progress="hidden"
    )
    
    chat_inputs_rp = [
        comps['rp_user_input'], comps['chatbot_rp'], comps['ai_persona_box'], comps['user_persona_box'],
        comps['pov_mode_rp'], comps['memory_rp_box'], comps['auto_mem_rp_check'],
        comps['auto_tts_rp_check'], comps['memory_rp_list']
    ]
    
    rp_send_event = comps['rp_send_button'].click(
        rp_chat_wrapper,
        chat_inputs_rp,
        chat_outputs_rp
    )
    
    rp_submit_event = comps['rp_user_input'].submit(
        rp_chat_wrapper,
        chat_inputs_rp,
        chat_outputs_rp
    )
    
    outputs_rp_file = [
        comps['chatbot_rp'],
        comps['rp_user_input'],
        comps['rp_file_upload']
    ] + rp_file_buttons_only + [comps['audio_output_rp'], comps['memory_rp_box']]
    
    rp_file_inputs = [
        comps['rp_user_input'], comps['chatbot_rp'], comps['rp_file_upload'],
        comps['ai_persona_box'], comps['user_persona_box'], comps['pov_mode_rp'],
        comps['memory_rp_box'], comps['auto_mem_rp_check'],
        comps['auto_tts_rp_check'], comps['memory_rp_list']
    ]
    
    rp_vision_event = comps['rp_send_vision'].click(
        rp_vision_wrapper,
        rp_file_inputs,
        RP_UNIFIED_OUTPUTS
    )
    
    rp_ocr_event = comps['rp_send_ocr'].click(
        rp_ocr_wrapper,
        rp_file_inputs,
        RP_UNIFIED_OUTPUTS # Pastikan menggunakan output yang terpadu
    )
    
    rp_doc_event = comps['rp_send_doc'].click(
        rp_doc_wrapper,
        rp_file_inputs,
        RP_UNIFIED_OUTPUTS # Pastikan menggunakan output yang terpadu
    )
    
    comps['rp_stop_button'].click(
        fn=on_stop_generating_rp,
        inputs=None,
        outputs=rp_ui_controls,
        cancels=[rp_send_event, rp_submit_event, rp_vision_event, rp_ocr_event, rp_doc_event]
    )
    
    comps['save_char_btn'].click(
        save_character,
        [comps['ai_persona_box'], comps['user_persona_box'], comps['character_name']],
        [comps['status_char'], comps['character_list'], comps['character_name']]
    )
    
    comps['character_list'].select(
        load_character,
        comps['character_list'],
        [comps['ai_persona_box'], comps['user_persona_box'], comps['status_char'], comps['character_name']]
    )
    
    comps['delete_char_btn'].click(
        delete_character,
        comps['character_list'],
        [comps['status_char'], comps['character_list'], comps['character_name'], comps['ai_persona_box'], comps['user_persona_box']]
    )
    
    comps['save_chat_rp'].click(
        lambda h, n: save_chat_history(h, n, RP_CHATS_DIR, "rp_chat"),
        [comps['chatbot_rp'], comps['chat_name_rp']],
        [comps['status_rp'], comps['chat_list_rp']],
        preprocess=False
    )
    
    comps['chat_list_rp'].select(
        lambda n: load_chat_wrapper(n, RP_CHATS_DIR),
        comps['chat_list_rp'],
        [comps['chatbot_rp'], comps['status_rp'], comps['chat_name_rp']]
    )
    
    comps['load_chat_rp'].click(
        lambda n: load_chat_history(n, RP_CHATS_DIR) + (n,),
        comps['chat_name_rp'],
        [comps['chatbot_rp'], comps['status_rp'], comps['chat_name_rp']]
    )
    
    comps['delete_chat_rp'].click(
        lambda n: delete_chat_history(n, RP_CHATS_DIR) + ("",),
        comps['chat_list_rp'],
        [comps['status_rp'], comps['chat_list_rp'], comps['chat_name_rp']]
    )
    
    comps['audio_input_rp'].change(
        speech_to_text,
        comps['audio_input_rp'],
        comps['rp_user_input']
    )

    # Event untuk tombol Hubungkan
    comps['connect_button'].click(
        connect_to_youtube,
        inputs=[
            comps['youtube_url_input'],
            states['vtuber_thread_state'],
            states['vtuber_stop_event_state'],
            states['vtuber_message_queue_state']
        ],
        outputs=[
            comps['status_vtuber'],
            states['vtuber_thread_state'],
            states['vtuber_stop_event_state'],
            comps['connect_button'],
            comps['disconnect_button']
        ]
    )

    # Event untuk tombol Putuskan Koneksi
    comps['disconnect_button'].click(
        disconnect_from_youtube,
        inputs=[states['vtuber_thread_state'], states['vtuber_stop_event_state']],
        outputs=[
            comps['status_vtuber'],
            states['vtuber_thread_state'],
            states['vtuber_stop_event_state'],
            comps['connect_button'],
            comps['disconnect_button']
        ]
    )

    # --- Event Handlers untuk VTube Studio ---
    comps['vts_connect_button'].click(
        vts_connect_wrapper,
        inputs=None,
        outputs=[comps['status_vts']]
    )

    comps['vts_disconnect_button'].click(
        vts_disconnect_wrapper,
        inputs=None,
        outputs=[comps['status_vts']]
    )

    comps['vtuber_refresh_button'].click(
        fn=update_vtuber_ui,
        inputs=[
            states['vtuber_message_queue_state'],
            comps['vtuber_chatbot'],
            comps['vtuber_ai_persona'],
            comps['vtuber_user_persona'],
            comps['vtuber_memory_box']
        ],
        outputs=[
            comps['live_chat_display'],
            comps['vtuber_chatbot'],
            comps['vtuber_audio_output']
        ]
    ).then(
        fn=None, inputs=None, outputs=None,
        js="""
        () => {
            setTimeout(() => {
                document.getElementById('vtuber_refresh_btn_id').click();
            }, 5000);
        }
        """
    )

    comps['vtuber_save_button'].click(
        lambda h, n: save_chat_history(h, n, VTUBER_CHATS_DIR, "vtuber_chat"),
        [comps['vtuber_chatbot'], comps['vtuber_chat_name']],
        [comps['status_simpan_vtuber'], comps['vtuber_chat_list']],
        preprocess=False
    )

    # Event Muat Sesi
    comps['vtuber_load_button'].click(
        lambda n: load_chat_history(n, VTUBER_CHATS_DIR) + (n,),
        comps['vtuber_chat_list'],
        [comps['vtuber_chatbot'], comps['status_simpan_vtuber'], comps['vtuber_chat_name']]
    )

    comps['add_mem_vtuber_btn'].click(
        fn=lambda fact: add_to_memory(DATA_DIR, "vtuber_filter.txt", fact),
        inputs=comps['vtuber_memory_input'],
        outputs=[comps['status_simpan_vtuber'], comps['vtuber_memory_box']]
    ).then(
        lambda: "", None, comps['vtuber_memory_input']
    )

    comps['clear_mem_vtuber_btn'].click(
        fn=lambda: clear_memory(DATA_DIR, "vtuber_filter.txt"),
        inputs=None,
        outputs=[comps['status_simpan_vtuber'], comps['vtuber_memory_box']]
    )

    comps['vtuber_delete_button'].click(
        lambda n: delete_chat_history(n, VTUBER_CHATS_DIR) + ("",),
        inputs=[comps['vtuber_chat_list']],
        outputs=[
            comps['status_simpan_vtuber'],
            comps['vtuber_chat_list'],
            comps['vtuber_chat_name']
        ]
    )

def screen_vision_wrapper(history, ai_persona, user_persona, memory_content):
    """Wrapper untuk alur kerja analisis layar."""
    yield history + [{"role": "assistant", "content": "📸 Menganalisis layar..."}], None

    base64_img, status = capture_screen_to_base64()
    if not base64_img:
        yield history + [{"role": "assistant", "content": status}], None
        return

    response, audio = process_vision_for_vtuber(base64_img, history, ai_persona, user_persona, memory_content)

    new_history = history + [
        {"role": "user", "content": "[Menganalisis tangkapan layar]"},
        {"role": "assistant", "content": response}
    ]
    yield new_history, audio

def camera_vision_wrapper(history, ai_persona, user_persona, memory_content):
    """Wrapper untuk alur kerja analisis kamera."""
    yield history + [{"role": "assistant", "content": "📸 Menganalisis kamera..."}], None

    base64_img, status = capture_camera_to_base64()
    if not base64_img:
        yield history + [{"role": "assistant", "content": status}], None
        return

    response, audio = process_vision_for_vtuber(base64_img, history, ai_persona, user_persona, memory_content)

    new_history = history + [
        {"role": "user", "content": "[Menganalisis gambar dari kamera]"},
        {"role": "assistant", "content": response}
    ]
    yield new_history, audio

def toggle_live_observation_wrapper(current_thread, current_stop_event, message_queue):
    """Memulai atau menghentikan thread pengamatan layar."""
    # Jika ada thread yang berjalan, hentikan
    if current_thread and current_thread.is_alive():
        logger.info("Mengirim sinyal berhenti ke thread pengamat...")
        current_stop_event.set()
        current_thread.join(timeout=5)
        return "🔴 Mulai Pengamatan Live", None, None
    
    # Jika tidak ada thread, mulai yang baru
    else:
        logger.info("Memulai thread pengamat baru...")
        stop_event = threading.Event()
        # Kita bisa membuat target object dinamis dari input UI nanti
        target_object = "person" 
        thread = threading.Thread(
            target=live_screen_observer,
            args=(stop_event, message_queue, target_object)
        )
        thread.start()
        return "⏹️ Hentikan Pengamatan Live", thread, stop_event


