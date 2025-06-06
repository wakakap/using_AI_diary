import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk, filedialog
import speech_recognition as sr
import requests
import google.generativeai as genai
import os
import time
import uuid
from playsound import playsound
import threading
from dotenv import load_dotenv
import keyboard
import re
import subprocess
import sys

# Try to import yaml, prompt user to install if not found
try:
    import yaml
except ImportError:
    root = tk.Tk()
    root.withdraw() 
    messagebox.showerror("依赖缺失", "PyYAML 模块未找到。\n请在终端运行 'pip install PyYAML' 来安装它。")
    sys.exit(1)


# --- Application Settings Class ---
class AppSettings:
    """A class to hold all application settings and Tkinter variables."""
    def __init__(self):
        # --- Environment and API Keys ---
        load_dotenv()
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

        # --- Gemini Model Configuration ---
        self.gemini_model = None
        if not self.GEMINI_API_KEY:
            print("错误：GEMINI_API_KEY 未在 .env 文件中正确设置，或者 .env 文件未加载。Gemini 功能将不可用。")
        else:
            try:
                genai.configure(api_key=self.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                print("Gemini API Key成功从 .env 文件加载并配置。")
            except ImportError:
                print("错误: google-generativeai 模块未安装。请运行 'pip install google-generativeai'")
            except Exception as e:
                print(f"Gemini 配置错误 (.env): {e}")

        # --- System Prompt & History ---
        self.SYSTEM_PROMPT = """
        あなたは女性日本語アシスタント。会話しながら、文の最後（私の話に対して文法や自然度の間違いを指摘する）毎回30文字以内。
        """
        self.conversation_history = []

        # --- GPT-SoVITS API Configuration (with Tkinter variables) ---
        self.USE_REFERENCE_AUDIO = tk.BooleanVar(value=True) #默认开启
        self.GPT_SOVITS_API_URL = tk.StringVar(value="http://localhost:9880/tts")
        self.REFERENCE_AUDIO_PATH = tk.StringVar(value="D:\\GPT-SoVITS_\\GPT-SoVITS-v4-20250422fix\\output\\slicer_opt\\RJ01370779_恋鈴桃歌\\8.wav_0004233600_0004380480.wav")
        self.PROMPT_TEXT = tk.StringVar(value="メスを楼落して従える力、まあ。")
        self.PROMPT_LANGUAGE = tk.StringVar(value="日文")
        self.TEXT_LANGUAGE = tk.StringVar(value="日文")
        self.GPT_SOVITS_SPEED_FACTOR = tk.DoubleVar(value=1.0)
        self.GPT_SOVITS_TOP_K = tk.IntVar(value=5)
        self.GPT_SOVITS_TOP_P = tk.DoubleVar(value=1)
        self.GPT_SOVITS_TEMPERATURE = tk.DoubleVar(value=1)
        self.GPT_SOVITS_TEXT_SPLIT_METHOD = tk.StringVar(value="cut5")
        self.GPT_SOVITS_BATCH_SIZE = tk.IntVar(value=1)
        self.GPT_SOVITS_SEED = tk.IntVar(value=-1)
        self.GPT_SOVITS_PARALLEL_INFER = tk.BooleanVar(value=False)
        self.GPT_SOVITS_REPETITION_PENALTY = tk.DoubleVar(value=1.35)
        self.GPT_SOVITS_SAMPLE_STEPS = tk.IntVar(value=32)
        self.GPT_SOVITS_SUPER_SAMPLING = tk.BooleanVar(value=False)
        
        self.TTS_INFER_YAML_PATH = tk.StringVar(value="D:\\GPT-SoVITS_\\GPT-SoVITS-v4-20250422fix\\GPT_SoVITS\\configs\\tts_infer.yaml")
        self.MODEL_BASE_PATH = "D:\\GPT-SoVITS_\\GPT-SoVITS-v4-20250422fix"
        self.T2S_WEIGHTS_PATH_FOR_YAML = tk.StringVar(value="")
        self.VITS_WEIGHTS_PATH_FOR_YAML = tk.StringVar(value="")

        # --- VOICEVOX API Configuration (with Tkinter variables) ---
        self.VOICEVOX_API_URL = tk.StringVar(value="http://localhost:50021")
        self.VOICEVOX_SPEAKER_ID = tk.IntVar(value=1)
        self.VOICEVOX_PRE_PHONEME_LENGTH = tk.DoubleVar(value=0.0)
        self.VOICEVOX_POST_PHONEME_LENGTH = tk.DoubleVar(value=0.0)
        self.VOICEVOX_SPEED_SCALE = tk.DoubleVar(value=1.2)
        self.VOICEVOX_PITCH_SCALE = tk.DoubleVar(value=0.01)
        self.VOICEVOX_INTONATION_SCALE = tk.DoubleVar(value=1.1)
        self.VOICEVOX_VOLUME_SCALE = tk.DoubleVar(value=1.0)

        # --- Speech Recognition Configuration ---
        self.LANGUAGE_FOR_STT = tk.StringVar(value="ja-JP") # 改为StringVar并设置默认值为日语

        # --- General Configuration ---
        self.OUTPUT_AUDIO_DIR = "D:\\TEMP\\generated_audio"
        os.makedirs(self.OUTPUT_AUDIO_DIR, exist_ok=True)

# Instantiate settings globally, will be properly initialized in create_gui
app_settings = None

# --- GUI Global Variables ---
root = None
conversation_display = None
status_label = None
user_input_entry = None
always_on_top_button = None
is_always_on_top = False
record_button = None
send_button = None
tts_engine_var = None
system_prompt_text_widget = None # For the system prompt text widget

# --- GUI Update Functions (Thread-safe) ---
def update_conversation_display(speaker, text):
    if conversation_display and root:
        def _update():
            conversation_display.config(state=tk.NORMAL)
            conversation_display.insert(tk.END, f"{speaker}: {text}\n")
            conversation_display.config(state=tk.DISABLED)
            conversation_display.see(tk.END)
        if threading.current_thread() is not threading.main_thread():
            root.after(0, _update)
        else:
            _update()

def update_status_label(message):
    if status_label and root:
        def _update():
            status_label.config(text=message)
        if threading.current_thread() is not threading.main_thread():
             root.after(0, _update)
        else:
            _update()

# --- Text Cleaning Function for TTS ---
def clean_text_for_tts(text):
    # if not text:
    #     return ""
    # text = text.replace('　', ' ')
    # symbols_to_remove = r"[「」『』【】《》“”‘’<>＜＞￥＃＠＊＋＝＿〜※・]"
    # text = re.sub(symbols_to_remove, '', text)
    return text

# --- Core Logic Functions ---
def record_audio_from_mic_thread():
    update_status_label("どうぞ話してください...")
    r = sr.Recognizer()
    audio = None
    with sr.Microphone() as source:
        r.pause_threshold = 1
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=12, phrase_time_limit=15)
        except sr.WaitTimeoutError:
            if root: root.after(0, update_status_label, "何も聞こえませんでした。")
            return None
        except Exception as e:
            if root: root.after(0, update_status_label, f"録音エラー: {e}")
            return None
    if audio:
        if root: root.after(0, update_status_label, "音声を処理中...")
        user_text = speech_to_text(audio)
        if user_text:
            if root: root.after(0, lambda: process_user_input(user_text, "You (Voice)"))
        else:
            if root: root.after(0, update_status_label, "準備完了")
    else:
        if root: root.after(0, update_status_label, "準備完了")

def speech_to_text(audio_data):
    if audio_data is None: return None
    r = sr.Recognizer()
    try: 
        selected_language = app_settings.LANGUAGE_FOR_STT.get()
        return r.recognize_google(audio_data, language=selected_language)
    except sr.UnknownValueError:
        if root: root.after(0, update_status_label, "音声を理解できませんでした。")
    except sr.RequestError as e:
        if root: root.after(0, update_status_label, f"STTサービスエラー: {e}")
    return None

def get_gemini_response_thread(user_text):
    if not app_settings.gemini_model:
        if root: root.after(0, update_status_label, "Gemini APIが設定されていません。")
        ai_text = "Gemini APIが未設定か初期化に失敗しました。"
        if root:
            root.after(0, update_conversation_display, "AIアシスタント", ai_text)
            root.after(0, update_status_label, "準備完了")
        return

    update_status_label("AIが応答を考えています...")
    
    current_context = [{"role": "user", "parts": [app_settings.SYSTEM_PROMPT]}]
    history_to_send = [msg for msg in app_settings.conversation_history if msg["parts"] != [app_settings.SYSTEM_PROMPT]]
    current_context.extend(history_to_send[-10:])
    current_context.append({"role": "user", "parts": [user_text]})
    
    try:
        response = app_settings.gemini_model.generate_content(current_context)
        ai_text = response.text.strip()
        
        app_settings.conversation_history.append({"role": "user", "parts": [user_text]})
        app_settings.conversation_history.append({"role": "model", "parts": [ai_text]})
        
        if root: root.after(0, update_conversation_display, "AI", ai_text)

        if ai_text:
            selected_engine = tts_engine_var.get() if tts_engine_var else "GPT-SoVITS"
            if selected_engine == "VOICEVOX":
                threading.Thread(target=text_to_speech_voicevox_thread, args=(ai_text,), daemon=True).start()
            elif selected_engine == "GPT-SoVITS":
                threading.Thread(target=text_to_speech_gpt_sovits_thread, args=(ai_text,), daemon=True).start()
            else:
                if root: root.after(0, update_status_label, "準備完了 (TTSエンジン未選択)")
        else:
            if root: root.after(0, update_status_label, "準備完了")
    except Exception as e:
        error_message = f"Gemini APIエラー: {e}"
        if root:
            root.after(0, update_status_label, error_message)
            root.after(0, update_conversation_display, "AIアシスタント", "すみません、エラーが発生しました。")
            root.after(0, update_status_label, "準備完了")

# --- TTS Engine Functions ---
def text_to_speech_voicevox_thread(text_to_synthesize):
    update_status_label("VOICEVOX音声を合成中...")
    output_filename = f"voicevox_output_{uuid.uuid4().hex}.wav"
    output_path = os.path.join(app_settings.OUTPUT_AUDIO_DIR, output_filename)
    api_url = app_settings.VOICEVOX_API_URL.get()
    try:
        query_url = f"{api_url}/audio_query"
        params_query = {"text": text_to_synthesize, "speaker": app_settings.VOICEVOX_SPEAKER_ID.get()}
        response_query = requests.post(query_url, params=params_query, timeout=10)
        response_query.raise_for_status()
        audio_query = response_query.json()
        audio_query["prePhonemeLength"] = app_settings.VOICEVOX_PRE_PHONEME_LENGTH.get()
        audio_query["postPhonemeLength"] = app_settings.VOICEVOX_POST_PHONEME_LENGTH.get()
        audio_query["speedScale"] = app_settings.VOICEVOX_SPEED_SCALE.get()
        audio_query["pitchScale"] = app_settings.VOICEVOX_PITCH_SCALE.get()
        audio_query["intonationScale"] = app_settings.VOICEVOX_INTONATION_SCALE.get()
        audio_query["volumeScale"] = app_settings.VOICEVOX_VOLUME_SCALE.get()
        synthesis_url = f"{api_url}/synthesis"
        headers_synthesis = {"Content-Type": "application/json"}
        params_synthesis = {"speaker": app_settings.VOICEVOX_SPEAKER_ID.get()}
        response_synthesis = requests.post(
            synthesis_url, json=audio_query, headers=headers_synthesis,
            params=params_synthesis, timeout=30
        )
        response_synthesis.raise_for_status()
        with open(output_path, "wb") as f: f.write(response_synthesis.content)
        update_status_label("VOICEVOX音声を再生中...")
        playsound(os.path.normpath(os.path.abspath(output_path)))
        update_status_label("準備完了")
    except requests.exceptions.RequestException as e:
        details = f"{e.response.status_code} - {e.response.text}" if e.response is not None else ""
        handle_tts_error("VOICEVOX", f"APIエラー({e.request.url}): {e}", details)
    except Exception as e: handle_tts_error("VOICEVOX", f"处理时发生错误: {e}")

def text_to_speech_gpt_sovits_thread(text_to_synthesize):
    cleaned_text = clean_text_for_tts(text_to_synthesize)
    if not cleaned_text:
        if root: root.after(0, update_status_label, "TTS Error: No text for GPT-SoVITS after cleaning.")
        return
    update_status_label("GPT-SoVITS音声を合成中...")
    output_path = os.path.join(app_settings.OUTPUT_AUDIO_DIR, f"gpt_sovits_output_{uuid.uuid4().hex}.wav")
    lang_map = {"日文": "ja", "中文": "zh", "英文": "en"}
    api_url = app_settings.GPT_SOVITS_API_URL.get()
    payload = {
        "text": cleaned_text,
        "text_lang": lang_map.get(app_settings.TEXT_LANGUAGE.get(), app_settings.TEXT_LANGUAGE.get().lower()),
        "top_k": app_settings.GPT_SOVITS_TOP_K.get(),
        "top_p": app_settings.GPT_SOVITS_TOP_P.get(),
        "temperature": app_settings.GPT_SOVITS_TEMPERATURE.get(),
        "text_split_method": app_settings.GPT_SOVITS_TEXT_SPLIT_METHOD.get(),
        "speed_factor": app_settings.GPT_SOVITS_SPEED_FACTOR.get(),
        "batch_size": app_settings.GPT_SOVITS_BATCH_SIZE.get(),
        "seed": app_settings.GPT_SOVITS_SEED.get(),
        "parallel_infer": app_settings.GPT_SOVITS_PARALLEL_INFER.get(),
        "repetition_penalty": app_settings.GPT_SOVITS_REPETITION_PENALTY.get(),
        "sample_steps": app_settings.GPT_SOVITS_SAMPLE_STEPS.get(),
        "super_sampling": app_settings.GPT_SOVITS_SUPER_SAMPLING.get(),
        "streaming_mode": False, "media_type": "wav",
    }

    # 2. 从UI获取参考相关参数的值，并去除首尾空格
    if app_settings.USE_REFERENCE_AUDIO.get():
        # 如果勾选了，才添加参考相关的参数
        ref_audio_path = app_settings.REFERENCE_AUDIO_PATH.get().strip()
        prompt_text = app_settings.PROMPT_TEXT.get().strip()
        prompt_lang_str = app_settings.PROMPT_LANGUAGE.get().strip()

        # 只要有值就添加，增加灵活性
        if ref_audio_path:
            payload['ref_audio_path'] = ref_audio_path
        if prompt_text:
            payload['prompt_text'] = prompt_text
        if prompt_lang_str:
            payload['prompt_lang'] = lang_map.get(prompt_lang_str, prompt_lang_str.lower())
    else:
        payload['ref_audio_path'] = None
        payload['prompt_text'] = None
        payload['prompt_lang'] = None
    try:
        response = requests.post(api_url, json=payload, timeout=90)
        if response.ok and 'audio/wav' in response.headers.get('Content-Type', ''):
            with open(output_path, "wb") as f: f.write(response.content)
            update_status_label("GPT-SoVITS音声を再生中...")
            playsound(os.path.normpath(os.path.abspath(output_path)))
            update_status_label("準備完了")
        else:
            handle_tts_error("GPT-SoVITS", f"API返回错误 (Status: {response.status_code})", response.text[:250])
    except Exception as e: handle_tts_error("GPT-SoVITS", f"请求时发生错误: {e}")

def handle_tts_error(engine_name, message, details=""):
    print(f"{engine_name} TTS Error: {message}")
    if details: print(f"Details: {details}")
    if root:
        root.after(0, update_status_label, f"{engine_name} TTSエラー (詳細はコンソール)")
        root.after(0, update_status_label, "準備完了")

# --- GUI Event Handlers & Helpers ---

def actual_record_action():
    if not root or not record_button or not send_button: return
    if record_button['state'] == tk.DISABLED: return
    record_button.config(state=tk.DISABLED)
    send_button.config(state=tk.DISABLED)
    threading.Thread(target=record_audio_from_mic_thread_wrapper, daemon=True).start()

def handle_global_record_hotkey():
    if root: root.after(0, actual_record_action)

def record_audio_from_mic_thread_wrapper():
    record_audio_from_mic_thread()
    if root: root.after(0, lambda: enable_buttons(True))

def enable_buttons(is_enabled):
    """Enable or disable input widgets."""
    state = tk.NORMAL if is_enabled else tk.DISABLED
    if record_button: record_button.config(state=state)
    if send_button: send_button.config(state=state)
    if user_input_entry: user_input_entry.config(state=state)

def handle_send_button():
    user_text = user_input_entry.get()
    if user_text.strip():
        user_input_entry.delete(0, tk.END)
        process_user_input(user_text, "You (Text)")

def process_user_input(user_text, speaker_name="You"):
    update_conversation_display(speaker_name, user_text)
    threading.Thread(target=get_gemini_response_thread, args=(user_text,), daemon=True).start()

def toggle_always_on_top():
    global is_always_on_top
    is_always_on_top = not is_always_on_top
    if root: root.attributes("-topmost", is_always_on_top)
    if always_on_top_button:
        always_on_top_button.config(text="常に前面解除" if is_always_on_top else "常に前面表示")

def browse_file(string_var, title, filetypes):
    file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    if file_path: string_var.set(file_path)

def open_yaml_file():
    path = app_settings.TTS_INFER_YAML_PATH.get()
    try:
        if sys.platform == "win32": os.startfile(path)
        elif sys.platform == "darwin": subprocess.run(['open', path], check=True)
        else: subprocess.run(['xdg-open', path], check=True)
    except Exception as e: messagebox.showerror("文件打开错误", f"无法打开文件: {path}\n错误: {e}")

# --- GUI Initialization ---
def create_main_page(parent):
    global conversation_display, status_label, user_input_entry, record_button, send_button
    
    conversation_display = scrolledtext.ScrolledText(parent, wrap=tk.WORD, state=tk.DISABLED, height=15, width=70)
    conversation_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # <<< 修改：将初始文本改为更明确的指示 >>>
    status_label = tk.Label(parent, text="アプリケーションを初期化中...", anchor="w")
    status_label.pack(padx=10, pady=(0,5), fill=tk.X)

    # --- Control and Input Frame ---
    control_frame = ttk.Frame(parent)
    control_frame.pack(padx=10, pady=(0,5), fill=tk.X)

    main_control_frame = ttk.Frame(parent)
    main_control_frame.pack(padx=10, pady=(0, 5), fill=tk.X)

    # 1. 创建第一行的框架 (用于输入框和按钮)
    top_line_frame = ttk.Frame(main_control_frame)
    top_line_frame.pack(fill=tk.X, pady=(0, 5)) # pady在两行之间增加一点垂直间距

    user_input_entry = ttk.Entry(top_line_frame, width=50)
    user_input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    user_input_entry.bind("<Return>", lambda event: handle_send_button())
    
    send_button = ttk.Button(top_line_frame, text="送信", command=handle_send_button)
    send_button.pack(side=tk.LEFT, padx=(5,0))
    
    record_button = ttk.Button(top_line_frame, text="録音 (Alt+Q)", command=actual_record_action)
    record_button.pack(side=tk.LEFT, padx=(5,0))

    bottom_line_frame = ttk.Frame(main_control_frame)
    bottom_line_frame.pack(fill=tk.X)

    lang_label = ttk.Label(bottom_line_frame, text="识别语言:")
    lang_label.pack(side=tk.LEFT) # 这里不再需要复杂的padx

    language_map = {
        "日语": "ja-JP",
        "中文 (普通话)": "cmn-Hans-CN",
        "English (US)": "en-US"
    }
    def on_language_select(event):
        selected_display_name = lang_combobox.get()
        language_code = language_map.get(selected_display_name)
        if language_code:
            app_settings.LANGUAGE_FOR_STT.set(language_code)
            print(f"识别语言已切换为: {language_code}")

    lang_combobox = ttk.Combobox(
        bottom_line_frame, 
        values=list(language_map.keys()),
        width=15, # 可以适当调整宽度
        state="readonly"
    )
    lang_combobox.set("日语")
    lang_combobox.bind("<<ComboboxSelected>>", on_language_select)
    lang_combobox.pack(side=tk.LEFT, padx=(5, 0))
    
    enable_buttons(False)

def create_gpt_sovits_settings_page(parent):
    global system_prompt_text_widget

    # --- Gemini Settings Frame ---
    gemini_frame = ttk.LabelFrame(parent, text="Gemini 设置", padding=(10, 5))
    gemini_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(gemini_frame, text="系统提示词 (System Prompt):").pack(anchor="w")
    system_prompt_text_widget = scrolledtext.ScrolledText(gemini_frame, wrap=tk.WORD, height=8)
    system_prompt_text_widget.pack(fill=tk.X, expand=True, pady=(2, 5))
    system_prompt_text_widget.insert(tk.END, app_settings.SYSTEM_PROMPT.strip())
    
    # <<< 新增：重置对话按钮 >>>
    reset_button = ttk.Button(gemini_frame, text="重置对话 (Reset Conversation)", command=handle_reset_conversation_button_click, style="Accent.TButton")
    reset_button.pack(pady=5)


    # --- Basic API Settings ---
    api_frame = ttk.LabelFrame(parent, text="GPT-SoVITS API 基本设置", padding=(10, 5))
    api_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(api_frame, text="API URL:").grid(row=0, column=0, sticky="w", pady=2)
    ttk.Entry(api_frame, textvariable=app_settings.GPT_SOVITS_API_URL, width=60).grid(row=0, column=1, sticky="ew", pady=2)

    # --- Other frames remain the same...
    ref_frame = ttk.LabelFrame(parent, text="参考音频设置", padding=(10, 5))
    ref_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Button(ref_frame, text="浏览...", command=lambda: browse_file(app_settings.REFERENCE_AUDIO_PATH, "选择参考音频", [("Audio Files", "*.wav"), ("All files", "*.*")])).grid(row=0, column=0, padx=5)
    ttk.Label(ref_frame, text="参考音频路径:").grid(row=0, column=1, sticky="w", pady=2)
    ttk.Entry(ref_frame, textvariable=app_settings.REFERENCE_AUDIO_PATH, width=60).grid(row=0, column=2, sticky="ew", pady=2)
    ttk.Label(ref_frame, text="参考文本:").grid(row=1, column=0, sticky="w", pady=2)
    ttk.Entry(ref_frame, textvariable=app_settings.PROMPT_TEXT, width=60).grid(row=1, column=1, columnspan=2, sticky="ew", pady=2)
    lang_options = ["日文", "中文", "英文"]
    ttk.Label(ref_frame, text="参考文本语言:").grid(row=2, column=0, sticky="w", pady=2)
    ttk.Combobox(ref_frame, textvariable=app_settings.PROMPT_LANGUAGE, values=lang_options).grid(row=2, column=1, columnspan=2, sticky="w", pady=2)
    ttk.Checkbutton(ref_frame,text="勾选此项以启用参考音频",variable=app_settings.USE_REFERENCE_AUDIO).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 5))
    params_frame = ttk.LabelFrame(parent, text="合成参数", padding=(10, 5))
    params_frame.pack(fill=tk.X, padx=10, pady=5)
    param_labels = ["合成文本语言:", "分割方法:", "速度(speed):", "Top K:", "Top P:", "温度(temp):", "Batch Size:", "Seed:", "重复惩罚:", "采样步数:"]
    param_vars = [app_settings.TEXT_LANGUAGE, app_settings.GPT_SOVITS_TEXT_SPLIT_METHOD, app_settings.GPT_SOVITS_SPEED_FACTOR, app_settings.GPT_SOVITS_TOP_K, app_settings.GPT_SOVITS_TOP_P, app_settings.GPT_SOVITS_TEMPERATURE, app_settings.GPT_SOVITS_BATCH_SIZE, app_settings.GPT_SOVITS_SEED, app_settings.GPT_SOVITS_REPETITION_PENALTY, app_settings.GPT_SOVITS_SAMPLE_STEPS]
    for i, label in enumerate(param_labels):
        row, col = divmod(i, 2)
        ttk.Label(params_frame, text=label).grid(row=row, column=col*2, sticky="w", padx=5, pady=2)
        if isinstance(param_vars[i], tk.StringVar) and label == "合成文本语言:": ttk.Combobox(params_frame, textvariable=param_vars[i], values=lang_options, width=12).grid(row=row, column=col*2+1, sticky="w", pady=2)
        else: ttk.Entry(params_frame, textvariable=param_vars[i], width=15).grid(row=row, column=col*2+1, sticky="w", pady=2)
    ttk.Checkbutton(params_frame, text="并行推理", variable=app_settings.GPT_SOVITS_PARALLEL_INFER).grid(row=3, column=0, sticky="w", padx=5, pady=5)
    ttk.Checkbutton(params_frame, text="超级采样", variable=app_settings.GPT_SOVITS_SUPER_SAMPLING).grid(row=3, column=2, sticky="w", padx=5, pady=5)
    
    # --- 模型权重与YAML配置 ---
    yaml_frame = ttk.LabelFrame(parent, text="模型权重与YAML配置", padding=(10, 5))
    yaml_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # ... (保留这部分，但我们会修改下面的按钮)
    
    # <<< 修改：这部分只保留路径选择和文件操作，切换功能由新按钮完成 >>>
    ttk.Button(yaml_frame, text="打开文件", command=open_yaml_file).grid(row=0, column=0)
    ttk.Label(yaml_frame, text="tts_infer.yaml 路径:").grid(row=0, column=1, sticky="w", pady=2)
    ttk.Entry(yaml_frame, textvariable=app_settings.TTS_INFER_YAML_PATH, width=70).grid(row=0, column=2, sticky="ew")

    ttk.Button(yaml_frame, text="浏览...", command=lambda: browse_file(app_settings.T2S_WEIGHTS_PATH_FOR_YAML, "选择 GPT(t2s) 模型", [("Model Files", "*.ckpt *.pth")])).grid(row=1, column=0, padx=5, columnspan=1)
    ttk.Label(yaml_frame, text="GPT模型(t2s)路径:").grid(row=1, column=1, sticky="w", pady=2)
    ttk.Entry(yaml_frame, textvariable=app_settings.T2S_WEIGHTS_PATH_FOR_YAML, width=70).grid(row=1, column=2, sticky="ew")
    
    ttk.Button(yaml_frame, text="浏览...", command=lambda: browse_file(app_settings.VITS_WEIGHTS_PATH_FOR_YAML, "选择 VITS(vits) 模型", [("Model Files", "*.ckpt *.pth")])).grid(row=2, column=0, padx=5, columnspan=1)
    ttk.Label(yaml_frame, text="VITS模型(vits)路径:").grid(row=2, column=1, sticky="w", pady=2)
    ttk.Entry(yaml_frame, textvariable=app_settings.VITS_WEIGHTS_PATH_FOR_YAML, width=70).grid(row=2, column=2, sticky="ew")
    
    # <<< 新增：切换并加载模型按钮 >>>
    switch_button = ttk.Button(yaml_frame, text="切换并加载模型 (Switch & Load Models)", command=handle_model_switch_button_click)
    switch_button.grid(row=3, column=0, columnspan=2, pady=10)

def create_voicevox_settings_page(parent):
    settings_frame = ttk.LabelFrame(parent, text="VOICEVOX 设置", padding=(10, 5))
    settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    labels = ["API URL:", "声源ID:", "前置静音(秒):", "后置静音(秒):", "语速:", "音调:", "抑扬:", "音量:"]
    variables = [app_settings.VOICEVOX_API_URL, app_settings.VOICEVOX_SPEAKER_ID, app_settings.VOICEVOX_PRE_PHONEME_LENGTH, app_settings.VOICEVOX_POST_PHONEME_LENGTH, app_settings.VOICEVOX_SPEED_SCALE, app_settings.VOICEVOX_PITCH_SCALE, app_settings.VOICEVOX_INTONATION_SCALE, app_settings.VOICEVOX_VOLUME_SCALE]
    for i, label_text in enumerate(labels):
        ttk.Label(settings_frame, text=label_text).grid(row=i, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=variables[i], width=50).grid(row=i, column=1, sticky="ew", padx=5, pady=5)
    settings_frame.columnconfigure(1, weight=1)

def switch_models(gpt_path, sovits_path):
    print("\n--- 🔄 Attempting to switch models ---")
    
    # Switch GPT Model
    if gpt_path:
        print(f"  Switching GPT model to: {gpt_path}")
        try:
            # This logic is based on the /set_gpt_weights endpoint in api_v2.py
            response_gpt = requests.get(f"http://127.0.0.1:9880//set_gpt_weights", params={"weights_path": gpt_path}, timeout=20)
            if response_gpt.status_code == 200 and response_gpt.json().get("message") == "success":
                print("  ✔️ GPT model switched successfully.")
            else:
                print(f"  ❌ Failed to switch GPT model. Status: {response_gpt.status_code}, Response: {response_gpt.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Network error while switching GPT model: {e}")
            return False
    else:
        print("  - Skipping GPT model switch (no path provided).")

    # Switch SoVITS Model
    if sovits_path:
        print(f"  Switching SoVITS model to: {sovits_path}")
        try:
            # This logic is based on the /set_sovits_weights endpoint in api_v2.py
            response_sovits = requests.get(f"http://127.0.0.1:9880//set_sovits_weights", params={"weights_path": sovits_path}, timeout=20)
            if response_sovits.status_code == 200 and response_sovits.json().get("message") == "success":
                print("  ✔️ SoVITS model switched successfully.")
            else:
                print(f"  ❌ Failed to switch SoVITS model. Status: {response_sovits.status_code}, Response: {response_sovits.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Network error while switching SoVITS model: {e}")
            return False
    else:
        print("  - Skipping SoVITS model switch (no path provided).")

    print("--- ✅ Model switching complete ---\n")
    return True


def handle_reset_conversation_button_click():
    """
    仅重置Gemini对话。由设置页的“重置对话”按钮调用。
    """
    if not system_prompt_text_widget:
        messagebox.showerror("错误", "UI尚未完全初始化。")
        return

    # 1. 从GUI获取最新的系统提示词
    new_prompt = system_prompt_text_widget.get("1.0", tk.END).strip()
    if not new_prompt:
        messagebox.showwarning("提示", "系统提示词(System Prompt)不能为空。")
        return
    app_settings.SYSTEM_PROMPT = new_prompt
    
    # 2. 重置对话历史
    initial_ai_message = "こんにちは！新しい対話を開始します。"
    app_settings.conversation_history = [
        {"role": "user", "parts": [app_settings.SYSTEM_PROMPT]},
        {"role": "model", "parts": [initial_ai_message]}
    ]

    # 3. 清空对话显示区并显示初始消息
    if conversation_display:
        conversation_display.config(state=tk.NORMAL)
        conversation_display.delete("1.0", tk.END)
        conversation_display.config(state=tk.DISABLED)
    update_conversation_display("AIアシスタント", initial_ai_message)

    # 4. 激活主页的输入组件
    enable_buttons(True)
    update_status_label("新对话已开始，请开始提问。")
    messagebox.showinfo("成功", "对话已重置！")

    # 5. 播放初始问候语音
    threading.Thread(target=lambda: (
        time.sleep(0.5), # 等待UI绘制
        (tts_engine_var.get() == "VOICEVOX" and text_to_speech_voicevox_thread(initial_ai_message)) or
        (tts_engine_var.get() == "GPT-SoVITS" and text_to_speech_gpt_sovits_thread(initial_ai_message))
    ), daemon=True).start()

def handle_model_switch_button_click():
    """
    切换GPT-SoVITS模型。由设置页的“切换模型”按钮调用。
    """
    gpt_path = app_settings.T2S_WEIGHTS_PATH_FOR_YAML.get().strip()
    sovits_path = app_settings.VITS_WEIGHTS_PATH_FOR_YAML.get().strip()

    if not gpt_path and not sovits_path:
        messagebox.showwarning("提示", "请先在上方选择至少一个模型文件的路径。")
        return

    update_status_label("正在通过API切换模型...")
    
    def switch_task():
        # 在后台线程中执行网络请求
        success = switch_models(gpt_path, sovits_path)
        if success:
            root.after(0, lambda: messagebox.showinfo("成功", "模型切换成功！"))
            root.after(0, update_status_label, "模型切换成功，准备就绪。")
        else:
            root.after(0, lambda: messagebox.showerror("切换失败", "模型切换失败，请检查GPT-SoVITS服务和模型路径。"))
            root.after(0, update_status_label, "模型切换失败。")
            
    threading.Thread(target=switch_task, daemon=True).start()

def create_gui():
    global root, always_on_top_button, tts_engine_var, app_settings
    root = tk.Tk()
    app_settings = AppSettings()
    root.title("日本語文法アシスタント")
    root.geometry("500x900") # Increased height slightly for the new button
    
    # Add a style for the accent button
    style = ttk.Style(root)
    style.configure("Accent.TButton", foreground="white", background="#0078D4")

    top_control_frame = ttk.Frame(root)
    top_control_frame.pack(padx=10, pady=(10, 5), fill=tk.X)
    tts_engine_label = ttk.Label(top_control_frame, text="TTSエンジン:")
    tts_engine_label.pack(side=tk.LEFT, padx=(0,5))
    tts_engine_var = tk.StringVar(value="GPT-SoVITS")
    gpt_sovits_radio = ttk.Radiobutton(top_control_frame, text="GPT-SoVITS", variable=tts_engine_var, value="GPT-SoVITS")
    gpt_sovits_radio.pack(side=tk.LEFT)
    voicevox_radio = ttk.Radiobutton(top_control_frame, text="VOICEVOX", variable=tts_engine_var, value="VOICEVOX")
    voicevox_radio.pack(side=tk.LEFT, padx=(5,10))
    always_on_top_button = ttk.Button(top_control_frame, text="常に前面表示", command=toggle_always_on_top)
    always_on_top_button.pack(side=tk.LEFT)

    notebook = ttk.Notebook(root)
    notebook.pack(pady=5, padx=10, fill="both", expand=True)
    main_page, gpt_sovits_page, voicevox_page = ttk.Frame(notebook), ttk.Frame(notebook), ttk.Frame(notebook)
    notebook.add(main_page, text='主页')
    notebook.add(gpt_sovits_page, text='模型与设定')
    notebook.add(voicevox_page, text='VOICEVOX 设置')
    
    create_main_page(main_page)
    create_gpt_sovits_settings_page(gpt_sovits_page)
    create_voicevox_settings_page(voicevox_page)

    if not app_settings.gemini_model:
         messagebox.showwarning("設定不足", "Gemini APIキーが未設定です。AI応答機能は利用できません。")

def initialize_default_conversation():
    """
    在程序启动时自动初始化第一个对话会话。
    """
    if not system_prompt_text_widget:
        print("错误：UI尚未完全初始化，无法开始自动对话。")
        return

    # 1. 使用默认的系统提示词开始
    # 注意：这里我们直接使用app_settings中的默认值，而不是从UI读取，因为UI可能还没完全就绪
    initial_ai_message = "こんにちは！アシスタントの準備ができました。どうぞ話してください。"
    app_settings.conversation_history = [
        {"role": "user", "parts": [app_settings.SYSTEM_PROMPT]},
        {"role": "model", "parts": [initial_ai_message]}
    ]

    # 2. 更新对话显示区
    update_conversation_display("AIアシスタント", initial_ai_message)

    # 3. 激活主页的输入组件
    enable_buttons(True)
    update_status_label("準備完了")

    # 4. 在后台播放初始问候语音
    threading.Thread(target=lambda: (
        time.sleep(0.5), # 稍作等待，确保声音不会过早播放
        (tts_engine_var.get() == "VOICEVOX" and text_to_speech_voicevox_thread(initial_ai_message)) or
        (tts_engine_var.get() == "GPT-SoVITS" and text_to_speech_gpt_sovits_thread(initial_ai_message))
    ), daemon=True).start()
# --- Main Program ---
if __name__ == "__main__":
    create_gui()
    try:
        keyboard.add_hotkey('alt+q', handle_global_record_hotkey)
        print("全局快捷键 Alt+Q 已注册。")
    except Exception as e:
        print(f"无法注册全局快捷键 Alt+Q: {e}")
        if root: messagebox.showwarning("快捷键错误", f"无法注册全局快捷键 Alt+Q: {e}")
    
    if root:
        # <<< 新增：在GUI启动后，延迟一小段时间自动开始对话 >>>
        # 使用 root.after() 可以确保在执行初始化之前，主窗口已经完全创建并显示
        root.after(200, initialize_default_conversation) 
        
        root.mainloop()
    else:
        print("错误: GUI未能成功初始化。")