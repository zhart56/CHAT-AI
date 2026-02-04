import gradio as gr
from .components import create_web_chat_tab, create_roleplay_tab, create_config_tab, create_vtuber_tab
from .event_handlers import register_event_handlers
from backend_logic import load_memory
from config import MEMORY_WEB_DIR, MEMORY_RP_DIR


def create_ui():
    """Fungsi utama untuk membangun dan merakit seluruh antarmuka."""
    
    with gr.Blocks(
        title="Advanced AI Chat",
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky")
    ) as demo:
        gr.Markdown("# 🤖 Advanced AI Chat Interface")
        gr.Markdown("Multimodal AI Assistant dengan Pencarian Web dan Fitur Roleplay")
        
        all_components = {}
        
        with gr.Tabs():
            # Tab "Chat + Akses Web" yang asli tetap ada
            with gr.TabItem("💬 Chat + Akses Web"):
                web_components = create_web_chat_tab()
                all_components.update(web_components)
            
            with gr.TabItem("🎭 Chat Roleplay"):
                rp_components = create_roleplay_tab()
                all_components.update(rp_components)

            with gr.TabItem("🎥 VTuber Live Chat (Beta)"):
                vtuber_components = create_vtuber_tab()
                all_components.update(vtuber_components)
            
            with gr.TabItem("⚙️ Konfigurasi"):
                config_components = create_config_tab()
                all_components.update(config_components)
        
        # Kumpulkan semua state yang sudah ada
        all_states = {
            "web_memory_state": gr.State(load_memory(MEMORY_WEB_DIR, "web_default.txt")),
            "rp_memory_state": gr.State(load_memory(MEMORY_RP_DIR, "rp_default.txt")),
            "vtuber_thread_state": gr.State(None),
            "vtuber_stop_event_state": gr.State(None),
            "vtuber_message_queue_state": gr.State([]),
            "vts_plugin_state": gr.State(None),
            "live_observer_thread_state": gr.State(None),
            "live_observer_stop_event_state": gr.State(None),
        }
        
        # Daftarkan semua event handler yang ada dan yang baru
        register_event_handlers(demo, all_components, all_states)
        
    
    return demo
