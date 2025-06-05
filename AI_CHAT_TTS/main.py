import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk # Added ttk for Combobox, or Radiobutton
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

# --- Configuration Parameters ---

# 1. Environment and API Keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. Gemini Model Configuration
gemini_model = None
if not GEMINI_API_KEY:
    print("错误：GEMINI_API_KEY 未在 .env 文件中正确设置，或者 .env 文件未加载。Gemini 功能将不可用。")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("Gemini API Key成功从 .env 文件加载并配置。")
    except ImportError:
        print("错误: google-generativeai 模块未安装。请运行 'pip install google-generativeai'")
    except Exception as e:
        print(f"Gemini 配置错误 (.env): {e}")

SYSTEM_PROMPT = """
あなたは日本語の会話シスタントです。
私との会話は日本語で行います。私の日本語の間違いをメーセージの最後に()の中に指摘する。回答は50内でお願いします。
私は録音で会話していますので、その音声の識別問題を気にしないで。
"""
conversation_history = [{"role": "user", "parts": [SYSTEM_PROMPT]}, {"role": "model", "parts": ["はい、わかりました。どのようなご用件でしょうか？"]}]

# 3. GPT-SoVITS API Configuration
GPT_SOVITS_API_URL = "http://localhost:9880/tts" # GPT-SoVITS API URL
REFERENCE_AUDIO_PATH = "D:\GPT-SoVITS_\GPT-SoVITS-v4-20250422fix\output\slicer_opt\RJ01370779_恋鈴桃歌\8.wav_0004233600_0004380480.wav" # For GPT-SoVITS
PROMPT_TEXT = "メスを楼落して従える力、まあ。" # For GPT-SoVITS
PROMPT_LANGUAGE = "日文" # For GPT-SoVITS
TEXT_LANGUAGE = "日文" # For GPT-SoVITS & VOICEVOX text
GPT_SOVITS_SPEED_FACTOR = 1.0       # api_v2.py の 'speed_factor' に対応
GPT_SOVITS_TOP_K = 10               # 以前のapi.pyで指定していた値を維持
GPT_SOVITS_TOP_P = 0.6              # 以前のapi.pyで指定していた値を維持
GPT_SOVITS_TEMPERATURE = 0.6        # 以前のapi.pyで指定していた値を維持
GPT_SOVITS_TEXT_SPLIT_METHOD = "cut5" # api_v2.py の TTS_Request モデルでのデフォルト

# 4. VOICEVOX API Configuration (from srt_to_zundamon.py)
VOICEVOX_API_URL = "http://localhost:50021" # Default address for VOICEVOX
VOICEVOX_SPEAKER_ID = 1  # Default speaker ID (e.g., 1 for Zundamon)
# VOICEVOX Audio Parameters
VOICEVOX_PRE_PHONEME_LENGTH = 0.0
VOICEVOX_POST_PHONEME_LENGTH = 0.0
VOICEVOX_SPEED_SCALE = 1.2
VOICEVOX_PITCH_SCALE = 0.01
VOICEVOX_INTONATION_SCALE = 1.1
VOICEVOX_VOLUME_SCALE = 1

# 5. Speech Recognition Configuration
LANGUAGE_FOR_STT = "ja-JP"

# 6. General Configuration
OUTPUT_AUDIO_DIR = "D:\TEMP\generated_audio"
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)

# --- GUI Global Variables ---
root = None
conversation_display = None
status_label = None
user_input_entry = None
always_on_top_button = None
is_always_on_top = False
record_button = None
send_button = None
tts_engine_var = None # To store the selected TTS engine (StringVar)

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
    return text
    if not text:
        return ""
    text = text.replace('　', ' ')
    # 包括常见的中文、日文句号、逗号、感叹号、问号、省略号等
    punctuation_to_space = r"[。、！？…,｡､！？…]" # 您可以根据需要添加更多符号
    # text = re.sub(punctuation_to_space, ' ', text)
    # symbols_to_remove = r"[「」『』【】（）《》“”‘’<>＜＞￥＃＠＊＋＝＿〜※・]" # 您可以根据需要添加更多符号
    symbols_to_remove = r"[「」『』【】《》“”‘’<>＜＞￥＃＠＊＋＝＿〜※・]" # 您可以根据需要添加更多符号
    text = re.sub(symbols_to_remove, '', text)
    # text = re.sub(r'\s+', ' ', text).strip()
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
            if root: root.after(0, update_status_label, "準備完了") # STT failed
    else:
        if root: root.after(0, update_status_label, "準備完了") # Recording failed

def speech_to_text(audio_data):
    if audio_data is None: return None
    r = sr.Recognizer()
    try: return r.recognize_google(audio_data, language=LANGUAGE_FOR_STT)
    except sr.UnknownValueError:
        if root: root.after(0, update_status_label, "音声を理解できませんでした。")
    except sr.RequestError as e:
        if root: root.after(0, update_status_label, f"STTサービスエラー: {e}")
    return None

def get_gemini_response_thread(user_text):
    global conversation_history
    if not gemini_model:
        if root: root.after(0, update_status_label, "Gemini APIが設定されていません。")
        ai_text = "Gemini APIが未設定か初期化に失敗しました。"
        if root:
            root.after(0, update_conversation_display, "AIアシスタント", ai_text)
            root.after(0, update_status_label, "準備完了")
        return

    update_status_label("AIが応答を考えています...")
    current_context = [{"role": "user", "parts": [SYSTEM_PROMPT]}]
    history_to_send = [msg for msg in conversation_history if msg["parts"] != [SYSTEM_PROMPT]]
    current_context.extend(history_to_send[-10:])
    current_context.append({"role": "user", "parts": [user_text]})
    try:
        response = gemini_model.generate_content(current_context)
        ai_text = response.text.strip()
        conversation_history.append({"role": "user", "parts": [user_text]})
        conversation_history.append({"role": "model", "parts": [ai_text]})
        if root: root.after(0, update_conversation_display, "AI", ai_text)

        if ai_text:
            selected_engine = tts_engine_var.get() if tts_engine_var else "GPT-SoVITS" # Default if var not ready
            if selected_engine == "VOICEVOX":
                threading.Thread(target=text_to_speech_voicevox_thread, args=(ai_text,), daemon=True).start()
            elif selected_engine == "GPT-SoVITS":
                threading.Thread(target=text_to_speech_gpt_sovits_thread, args=(ai_text,), daemon=True).start()
            else: # Fallback or if no TTS
                if root: root.after(0, update_status_label, "準備完了 (TTSエンジン未選択)")
        else: # No AI text
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
    output_path = os.path.join(OUTPUT_AUDIO_DIR, output_filename)

    try:
        # Step 1: Get audio_query
        query_url = f"{VOICEVOX_API_URL}/audio_query"
        params_query = {"text": text_to_synthesize, "speaker": VOICEVOX_SPEAKER_ID}
        response_query = requests.post(query_url, params=params_query, timeout=10)
        response_query.raise_for_status()
        audio_query = response_query.json()

        # Modify audio parameters
        audio_query["prePhonemeLength"] = VOICEVOX_PRE_PHONEME_LENGTH
        audio_query["postPhonemeLength"] = VOICEVOX_POST_PHONEME_LENGTH
        audio_query["speedScale"] = VOICEVOX_SPEED_SCALE
        audio_query["pitchScale"] = VOICEVOX_PITCH_SCALE
        audio_query["intonationScale"] = VOICEVOX_INTONATION_SCALE
        audio_query["volumeScale"] = VOICEVOX_VOLUME_SCALE

        # Step 2: Synthesize audio
        synthesis_url = f"{VOICEVOX_API_URL}/synthesis"
        headers_synthesis = {"Content-Type": "application/json"}
        params_synthesis = {"speaker": VOICEVOX_SPEAKER_ID}
        response_synthesis = requests.post(
            synthesis_url, json=audio_query, headers=headers_synthesis,
            params=params_synthesis, timeout=30 # Increased timeout for synthesis
        )
        response_synthesis.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response_synthesis.content)
        
        update_status_label("VOICEVOX音声を再生中...")
        normalized_output_path = os.path.normpath(os.path.abspath(output_path))  # Get absolute path for playsound
        playsound(normalized_output_path)
        update_status_label("準備完了")

    except requests.exceptions.ConnectionError:
        handle_tts_error("VOICEVOX", f"VOICEVOXエンジン({VOICEVOX_API_URL})に接続できません。起動していますか？")
    except requests.exceptions.RequestException as e:
        details = f"{e.response.status_code} - {e.response.text}" if e.response is not None else ""
        handle_tts_error("VOICEVOX", f"APIエラー: {e}", details)
    except Exception as e:
        handle_tts_error("VOICEVOX", f"処理エラー: {e}")

def text_to_speech_gpt_sovits_thread(text_to_synthesize):
    """
    Synthesizes speech using the GPT-SoVITS API (api_v2.py) and plays it.
    """
    cleaned_text = clean_text_for_tts(text_to_synthesize)
    if not cleaned_text:
        if root: root.after(0, update_status_label, "TTS Error: No text for GPT-SoVITS after cleaning.")
        return

    update_status_label("GPT-SoVITS音声を合成中 (api_v2)...")
    output_filename = f"gpt_sovits_output_{uuid.uuid4().hex}.wav"
    output_path = os.path.join(OUTPUT_AUDIO_DIR, output_filename)

    # Language mapping from your display names to api_v2.py's expected language codes
    lang_map = {
        "日文": "ja",
        "中文": "zh", # 必要であれば追加
        "英文": "en", # 必要であれば追加
        # 他の言語マッピングが必要な場合はここに追加
    }
    api_prompt_lang = lang_map.get(PROMPT_LANGUAGE, PROMPT_LANGUAGE.lower())
    api_text_lang = lang_map.get(TEXT_LANGUAGE, TEXT_LANGUAGE.lower())

    payload = {
        "text": cleaned_text,
        "text_lang": api_text_lang,               # 例: "ja"
        "ref_audio_path": REFERENCE_AUDIO_PATH,
        "prompt_text": PROMPT_TEXT,               # api_v2.pyではオプションだが、あれば含める
        "prompt_lang": api_prompt_lang,           # 例: "ja"
        "top_k": GPT_SOVITS_TOP_K,                #
        "top_p": GPT_SOVITS_TOP_P,                #
        "temperature": GPT_SOVITS_TEMPERATURE,    #
        "text_split_method": GPT_SOVITS_TEXT_SPLIT_METHOD, #
        "speed_factor": GPT_SOVITS_SPEED_FACTOR,  #
        "streaming_mode": False,                  # main.pyは完全なファイルを期待するためFalse
        "media_type": "wav",                      # wav形式を期待
        # 必要に応じてapi_v2.pyのTTS_Requestモデルから他のオプションパラメータを追加可能
        # "batch_size": 1,
        # "seed": -1,
        # "parallel_infer": True,
        # "repetition_penalty": 1.35,
        # "sample_steps": 32,
        # "super_sampling": False,
    }

    print(f"GPT-SoVITS API (v2) URL: {GPT_SOVITS_API_URL}")
    print(f"GPT-SoVITS (v2) Payload: {payload}")

    try:
        response = requests.post(GPT_SOVITS_API_URL, json=payload, timeout=90) # タイムアウト値を調整可能

        if response.status_code == 200:
            # api_v2.py は成功時に直接wavオーディオストリームを返す
            if 'audio/wav' in response.headers.get('Content-Type', '').lower():
                with open(output_path, "wb") as f:
                    f.write(response.content)
                update_status_label("GPT-SoVITS音声(v2)を再生中...")
                normalized_output_path = os.path.normpath(os.path.abspath(output_path))
                playsound(normalized_output_path)
                update_status_label("準備完了")
            else:
                # 200 OKだがコンテントタイプが期待通りでない場合
                error_detail = (f"API returned 200 but Content-Type is not audio/wav: "
                                f"{response.headers.get('Content-Type', '')}. "
                                f"Response text: {response.text[:200]}")
                handle_tts_error("GPT-SoVITS (v2)", error_detail)

        elif response.status_code == 400: # api_v2.py は400エラー時にJSONを返す
            try:
                error_data = response.json()
                error_detail = error_data.get("message", response.text)
                # api_v2.py のエラーレスポンスには "Exception" フィールドが含まれることがある
                if "Exception" in error_data:
                    error_detail += f" (Exception: {error_data['Exception']})"
            except ValueError: # JSONデコードに失敗した場合
                error_detail = response.text[:200]
            handle_tts_error("GPT-SoVITS (v2)", f"APIエラー: Status {response.status_code}", error_detail)
        else: # その他のエラーコード
            error_detail = response.text[:200]
            handle_tts_error("GPT-SoVITS (v2)", f"APIエラー: Status {response.status_code}", error_detail)

    except requests.exceptions.ConnectionError:
        handle_tts_error("GPT-SoVITS (v2)",
                         f"GPT-SoVITSエンジン({GPT_SOVITS_API_URL})に接続できません。"
                         f"api_v2.py を起動していますか？ 設定ファイル (-cオプション) は正しいですか？")
    except requests.exceptions.Timeout:
        handle_tts_error("GPT-SoVITS (v2)",
                         f"GPT-SoVITSエンジン({GPT_SOVITS_API_URL})への接続がタイムアウトしました。")
    except Exception as e:
        import traceback
        print(traceback.format_exc()) # デバッグ用に完全なトレースバックを出力
        handle_tts_error("GPT-SoVITS (v2)", f"処理エラー: {str(e)}")

def handle_tts_error(engine_name, message, details=""):
    print(f"{engine_name} TTS Error: {message}")
    if details: print(f"Details: {details}")
    if root:
        root.after(0, update_status_label, f"{engine_name} TTSエラー (詳細はコンソール)")
        root.after(0, update_status_label, "準備完了") # Reset status after error

# --- GUI Event Handlers ---
def actual_record_action():
    if not root or not record_button or not send_button:
        print("GUI元素尚未初始化，无法执行录音操作。")
        return
    if record_button['state'] == tk.DISABLED: return
    record_button.config(state=tk.DISABLED)
    send_button.config(state=tk.DISABLED)
    threading.Thread(target=record_audio_from_mic_thread_wrapper, daemon=True).start()

def handle_global_record_hotkey():
    print("Alt+Q 全局快捷键触发")
    if root: root.after(0, actual_record_action)
    else: print("root 窗口未初始化，无法通过全局快捷键启动录音。")

def record_audio_from_mic_thread_wrapper():
    record_audio_from_mic_thread()
    if root: root.after(0, enable_buttons)

def enable_buttons():
    if record_button and send_button:
        record_button.config(state=tk.NORMAL)
        send_button.config(state=tk.NORMAL)

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

# --- GUI Initialization ---
def create_gui():
    global root, conversation_display, status_label, user_input_entry, record_button, send_button
    global always_on_top_button, tts_engine_var # Declare tts_engine_var as global

    root = tk.Tk()
    root.title("日本語文法アシスタント")

    # --- Top Control Frame (TTS Engine, Always on Top) ---
    top_control_frame = tk.Frame(root)
    top_control_frame.pack(padx=10, pady=(10,0), fill=tk.X)

    # TTS Engine Selection
    tts_engine_label = tk.Label(top_control_frame, text="TTSエンジン:")
    tts_engine_label.pack(side=tk.LEFT, padx=(0,5))

    tts_engine_var = tk.StringVar(value="GPT-SoVITS") # Default TTS engine
    
    # Using Radiobuttons for TTS selection
    gpt_sovits_radio = tk.Radiobutton(top_control_frame, text="GPT-SoVITS", variable=tts_engine_var, value="GPT-SoVITS")
    gpt_sovits_radio.pack(side=tk.LEFT)
    voicevox_radio = tk.Radiobutton(top_control_frame, text="VOICEVOX", variable=tts_engine_var, value="VOICEVOX")
    voicevox_radio.pack(side=tk.LEFT, padx=(5,10))
    
    always_on_top_button = tk.Button(top_control_frame, text="常に前面表示", command=toggle_always_on_top)
    always_on_top_button.pack(side=tk.LEFT) # Or side=tk.RIGHT if preferred

    # --- Conversation Display ---
    conversation_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, height=15, width=70)
    conversation_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # --- Status Label ---
    status_label = tk.Label(root, text="準備完了", anchor="w")
    status_label.pack(padx=10, pady=(0,5), fill=tk.X)

    # --- Input Frame ---
    input_frame = tk.Frame(root)
    input_frame.pack(padx=10, pady=(0,10), fill=tk.X)
    user_input_entry = tk.Entry(input_frame, width=50)
    user_input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    user_input_entry.bind("<Return>", lambda event: handle_send_button())
    send_button = tk.Button(input_frame, text="送信", command=handle_send_button)
    send_button.pack(side=tk.LEFT, padx=(5,0))
    record_button = tk.Button(input_frame, text="録音 (Alt+Q)", command=actual_record_action)
    record_button.pack(side=tk.LEFT, padx=(5,0))
    
    if not gemini_model:
         messagebox.showwarning("設定不足", "Gemini APIキーが未設定またはモデルの初期化に失敗しました。AIの応答機能は利用できません。詳細はコンソール出力を確認してください。")

    initial_ai_message = conversation_history[1]['parts'][0]
    update_conversation_display("AIアシスタント", initial_ai_message)
    if initial_ai_message and gemini_model:
        selected_engine = tts_engine_var.get()
        if selected_engine == "VOICEVOX":
            threading.Thread(target=text_to_speech_voicevox_thread, args=(initial_ai_message,), daemon=True).start()
        elif selected_engine == "GPT-SoVITS":
            threading.Thread(target=text_to_speech_gpt_sovits_thread, args=(initial_ai_message,), daemon=True).start()
    
# --- Main Program ---
if __name__ == "__main__":
    if not GEMINI_API_KEY: print("关键警告: Gemini APIキーが .env ファイルから読み込めませんでした。")
    if REFERENCE_AUDIO_PATH == "path/to/your/reference_audio.wav":
         print("启动警告: GPT-SoVITS の REFERENCE_AUDIO_PATH がデフォルトのままです。GPT-SoVITS機能のために設定してください。")
    print(f"VOICEVOX API URL: {VOICEVOX_API_URL}, Speaker ID: {VOICEVOX_SPEAKER_ID}")
    print(f"GPT-SoVITS API URL: {GPT_SOVITS_API_URL}")


    create_gui()
    try:
        keyboard.add_hotkey('alt+q', handle_global_record_hotkey)
        print("全局快捷键 Alt+Q 已注册，用于启动录音。")
    except Exception as e:
        print(f"无法注册全局快捷键 Alt+Q: {e}")
        print("这可能是因为权限不足 (尝试以管理员身份运行脚本)，或者其他程序占用了该快捷键，或者 keyboard 库未能正确初始化。")
        if root: messagebox.showwarning("快捷键错误", f"无法注册全局快捷键 Alt+Q: {e}\n请检查权限或是否有其他程序冲突。")

    if root: root.mainloop()
    else: print("错误: GUI未能成功初始化。")