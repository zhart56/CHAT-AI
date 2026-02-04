import os
import json
import re
import logging
import gradio as gr
import shutil
import uuid
from config import WEB_CHATS_DIR, RP_CHATS_DIR, CHARACTERS_DIR, SETTINGS_FILE, MEMORY_WEB_DIR, MEMORY_RP_DIR, global_settings,CHAT_IMAGES_DIR

logger = logging.getLogger(__name__)

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding='utf-8') as f:
                global_settings.update(json.load(f))
            logger.info("Pengaturan berhasil dimuat dari file.")
    except Exception as e:
        logger.error(f"Gagal memuat pengaturan: {e}")
    return global_settings

def save_settings(provider, or_key, ds_key, a4f_key, bb_key, bb_model, lm_url, model_name, search_count, google_key, google_cx, gemini_key, short_term_limit, max_articles):
    try:
        settings_to_save = {
            "api_provider": provider, "openrouter_api_key": or_key, "deepseek_api_key": ds_key,
            "a4f_api_key": a4f_key, # <-- BARU
            "blackbox_api_key": bb_key, "blackbox_model_name": bb_model, "lmstudio_api_url": lm_url,
            "model_name": model_name, 
            "search_results_count": int(search_count),
            "google_api_key": google_key,   
            "google_cse_id": google_cx,
            "gemini_api_key": gemini_key,
            "short_term_memory_limit": int(short_term_limit),
            "max_articles_to_read": int(max_articles)      
        }
        global_settings.update(settings_to_save)
        with open(SETTINGS_FILE, "w", encoding='utf-8') as f:
            json.dump(settings_to_save, f, indent=4, ensure_ascii=False)
        logger.info("Pengaturan berhasil disimpan.")
        return "Pengaturan berhasil disimpan!"
    except Exception as e:
        return f"Error menyimpan pengaturan: {e}"

def list_files_in_dir(directory):
    if not os.path.isdir(directory): return []
    try:
        return sorted([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    except Exception as e:
        logger.error(f"Gagal membaca direktori {directory}: {e}")
        return []


def get_next_chat_filename(directory, prefix="chat"):
    """Mendapatkan nama file chat berikutnya berdasarkan nomor."""
    try:
        files = list_files_in_dir(directory)
        numeric_files = []
        
        for f in files:
            match = re.search(r'_(\d+)\.json$', f)
            if match:
                numeric_files.append(int(match.group(1)))
        
        next_num = max(numeric_files) + 1 if numeric_files else 1
        return f"{prefix}_{next_num}.json"
    except Exception as e:
        logger.error(f"Gagal menghasilkan nama file: {e}")
        return f"{prefix}_1.json"

def save_chat_history(history, chat_name, directory, prefix):
    """Menyimpan riwayat obrolan, dengan penanganan format gambar internal Gradio."""
    try:
        if not chat_name or not chat_name.strip():
            chat_name = get_next_chat_filename(directory, prefix)
        
        file_name = f"{chat_name}.json" if not chat_name.endswith(".json") else chat_name
        file_path = os.path.join(directory, file_name)
        
        history_to_save = []
        for message in history:
            new_message = message.copy()
            content = new_message.get("content")
            
            # --- LOGIKA BARU YANG LEBIH PINTAR ---
            # Cek jika konten adalah format dictionary gambar internal Gradio
            if isinstance(content, dict) and 'file' in content and 'alt_text' in content:
                # Ekstrak path temporer dari dictionary
                temp_path = content['file']['path']
                alt_text = content['alt_text']
                
                if os.path.exists(temp_path):
                    _, extension = os.path.splitext(temp_path)
                    permanent_filename = f"{uuid.uuid4()}{extension}"
                    permanent_path = os.path.join(CHAT_IMAGES_DIR, permanent_filename)
                    
                    shutil.copy2(temp_path, permanent_path)
                    logger.info(f"Menyalin gambar dari {temp_path} ke {permanent_path}")
                    
                    # Simpan sebagai TUPLE sederhana yang bersih di file JSON
                    new_message["content"] = (permanent_path, alt_text)
                else:
                    # Jika path tidak ada, simpan sebagai teks biasa
                    new_message["content"] = f"[Gambar tidak ditemukan di path: {temp_path}]"

            # Cek juga untuk format tuple lama (untuk keamanan)
            elif isinstance(content, tuple) and isinstance(content[0], str) and os.path.exists(content[0]):
                temp_path = content[0]
                alt_text = content[1]
                _, extension = os.path.splitext(temp_path)
                permanent_filename = f"{uuid.uuid4()}{extension}"
                permanent_path = os.path.join(CHAT_IMAGES_DIR, permanent_filename)
                
                shutil.copy2(temp_path, permanent_path)
                logger.info(f"Menyalin gambar (format tuple) dari {temp_path} ke {permanent_path}")
                
                new_message["content"] = (permanent_path, alt_text)
            
            history_to_save.append(new_message)
        # --- AKHIR LOGIKA BARU ---
            
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(history_to_save, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Chat '{file_name}' disimpan di {directory}.")
        return f"Chat '{file_name}' disimpan!", gr.update(choices=list_files_in_dir(directory), value=file_name)
    except Exception as e:
        logger.error(f"Gagal menyimpan chat: {e}", exc_info=True)
        return f"Error menyimpan chat: {e}", gr.update()

def load_chat_history(chat_name, directory):
    """Memuat riwayat obrolan, dengan kemampuan memperbaiki format tuple dari JSON."""
    try:
        if not chat_name or not chat_name.strip():
            return [], "Pilih chat untuk dimuat."
        
        file_path = os.path.join(directory, chat_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                history_from_json = json.load(f)
            
            history_to_display = []
            for message in history_from_json:
                new_message = message.copy()
                content = new_message.get("content")
                
                # JSON menyimpan tuple sebagai list, jadi kita ubah kembali ke tuple
                if isinstance(content, list) and len(content) == 2:
                    # Pastikan path file gambar masih ada sebelum menampilkannya
                    img_path = content[0]
                    if os.path.exists(img_path):
                        new_message["content"] = tuple(content)
                    else:
                        new_message["content"] = f"[Gambar yang disimpan di {os.path.basename(img_path)} tidak ditemukan]"
                
                history_to_display.append(new_message)

            logger.info(f"Chat '{chat_name}' dimuat dari {directory}.")
            return history_to_display, f"Chat '{chat_name}' dimuat!"
        else:
            logger.warning(f"File '{chat_name}' tidak ditemukan di {directory}.")
            return [], f"Error: File '{chat_name}' tidak ditemukan."
    except Exception as e:
        logger.error(f"Gagal memuat chat: {e}", exc_info=True)
        return [], f"Error memuat chat: {e}"

def delete_chat_history(chat_name, directory):
    """Menghapus file riwayat obrolan."""
    try:
        if not chat_name or not chat_name.strip():
            return "Pilih chat untuk dihapus.", gr.update()
        
        file_path = os.path.join(directory, chat_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Chat '{chat_name}' dihapus dari {directory}.")
            return f"Chat '{chat_name}' dihapus.", gr.update(choices=list_files_in_dir(directory), value=None)
        else:
            logger.warning(f"File '{chat_name}' tidak ditemukan di {directory}.")
            return f"Error: File '{chat_name}' tidak ditemukan.", gr.update()
    except Exception as e:
        logger.error(f"Gagal menghapus chat: {e}")
        return f"Error menghapus chat: {e}", gr.update()

def save_character(ai_persona, user_persona, name):
    """Menyimpan deskripsi karakter AI dan pengguna ke file JSON."""
    try:
        if not name or not name.strip():
            return "Nama karakter tidak boleh kosong.", gr.update(), name
        
        file_name = f"{name}.json" if not name.endswith(".json") else name
        file_path = os.path.join(CHARACTERS_DIR, file_name)
        
        char_data = {
            "ai_persona": ai_persona, 
            "user_persona": user_persona
        }
        
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(char_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Karakter '{file_name}' disimpan.")
        return f"Karakter '{file_name}' disimpan!", gr.update(choices=list_files_in_dir(CHARACTERS_DIR), value=file_name), name
    except Exception as e:
        logger.error(f"Gagal menyimpan karakter: {e}")
        return f"Error menyimpan karakter: {e}", gr.update(), name

def load_character(name):
    """Memuat deskripsi karakter dari file JSON."""
    try:
        if not name or not name.strip():
            return "", "", "Pilih karakter untuk dimuat.", name
        
        file_path = os.path.join(CHARACTERS_DIR, name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                char_data = json.load(f)
            
            ai_persona = char_data.get("ai_persona", "")
            user_persona = char_data.get("user_persona", "")
            file_name_without_ext = os.path.splitext(name)[0]
            
            logger.info(f"Karakter '{name}' dimuat.")
            return ai_persona, user_persona, f"Karakter '{name}' dimuat!", file_name_without_ext
        else:
            logger.warning(f"File karakter '{name}' tidak ditemukan.")
            return "", "", f"Error: Karakter '{name}' tidak ditemukan.", name
    except Exception as e:
        logger.error(f"Gagal memuat karakter: {e}")
        return "", "", f"Error memuat karakter: {e}", name

def delete_character(name):
    """Menghapus file karakter."""
    try:
        if not name or not name.strip():
            return "Pilih karakter untuk dihapus.", gr.update(), "", "", ""
        
        file_path = os.path.join(CHARACTERS_DIR, name)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Karakter '{name}' dihapus.")
            return f"Karakter '{name}' dihapus.", gr.update(choices=list_files_in_dir(CHARACTERS_DIR), value=None), "", "", ""
        else:
            logger.warning(f"File karakter '{name}' tidak ditemukan.")
            return f"Error: Karakter '{name}' tidak ditemukan.", gr.update(), "", "", ""
    except Exception as e:
        logger.error(f"Gagal menghapus karakter: {e}")
        return f"Error menghapus karakter: {e}", gr.update(), "", "", ""

def get_memory_list(directory):
    """Mendapatkan daftar file memori .txt dari sebuah direktori."""
    if not os.path.isdir(directory): return []
    try:
        return sorted([f for f in os.listdir(directory) if f.endswith('.txt')])
    except Exception as e:
        logger.error(f"Gagal membaca direktori memori {directory}: {e}")
        return []

def load_memory(directory, filename):
    """Memuat konten memori dari file yang spesifik."""
    if not filename or not directory:
        return ""
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Gagal memuat file memori {filepath}: {e}")
            return ""
    return ""

def add_to_memory(directory, filename, new_fact):
    """Menambahkan fakta baru ke file memori yang spesifik."""
    if not filename or not new_fact or not new_fact.strip():
        return "Nama file atau fakta tidak boleh kosong.", load_memory(directory, filename)
    
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, "a", encoding='utf-8') as f:
            f.write(f"- {new_fact}\n")
        
        status = f"Fakta ditambahkan ke memori '{filename}'."
        logger.info(status)
        return status, load_memory(directory, filename)
    except Exception as e:
        error_msg = f"Error menambahkan ke memori: {e}"
        logger.error(error_msg)
        return error_msg, load_memory(directory, filename)

def clear_memory(directory, filename):
    """Menghapus semua konten dari file memori yang spesifik."""
    if not filename:
        return "Pilih file memori untuk dibersihkan.", ""
    
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "w", encoding='utf-8') as f:
                f.write("")
            status = f"Memori '{filename}' dibersihkan."
            logger.info(status)
            return status, ""
        except Exception as e:
            error_msg = f"Error membersihkan memori: {e}"
            logger.error(error_msg)
            return error_msg, load_memory(directory, filename)
    return f"File '{filename}' tidak ditemukan.", ""

def delete_memory_file(directory, filename):
    """Menghapus file memori yang spesifik."""
    if not filename:
        return "Pilih file memori untuk dihapus.", gr.update()
    
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            status = f"File memori '{filename}' dihapus."
            logger.info(status)
            return status, gr.update(choices=get_memory_list(directory), value=None)
        except Exception as e:
            error_msg = f"Error menghapus file memori: {e}"
            logger.error(error_msg)
            return error_msg, gr.update()
    return f"File '{filename}' tidak ditemukan.", gr.update()