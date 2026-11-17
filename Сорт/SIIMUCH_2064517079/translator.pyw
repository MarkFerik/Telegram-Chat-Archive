import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import sys

try:
    from PIL import ImageGrab, ImageOps, ImageEnhance
    import pytesseract
    from deep_translator import MyMemoryTranslator
    import keyboard
    import threading
    import ctypes
except Exception as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Ошибка импорта", f"Не удалось загрузить библиотеку:\n{e}\n\nУстанови через терминал:\npip install Pillow pytesseract deep-translator keyboard")
    sys.exit(1)

# Исправление масштабирования Windows (DPI-awareness)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Расширенный список языков мира
LANGUAGES = {
    "Авто / Eng": ("eng", "en-US"),
    "English": ("eng", "en-US"),
    "Русский": ("rus", "ru-RU"),
    "Українська": ("ukr", "uk-UA"),
    "Español": ("spa", "es-ES"),
    "Français": ("fra", "fr-FR"),
    "Deutsch": ("deu", "de-DE"),
    "Italiano": ("ita", "it-IT"),
    "Polski": ("pol", "pl-PL"),
    "Türkçe": ("tur", "tr-TR"),
    "Português": ("por", "pt-PT"),
    "日本語 (Jap)": ("jpn", "ja-JP"),
    "中文 (Chi)": ("chi_sim", "zh-CN"),
    "한국어 (Kor)": ("kor", "ko-KR"),
}

# Доступные цветовые темы
THEMES = [
    {
        "name": "Мятный",
        "accent": "#00C896",
        "bg_main": "#13131A",
        "bg_header": "#0D0D12",
        "bg_input": "#1E1E28",
        "border": "#2E3244",
        "text_main": "#D4D8E8",
        "text_muted": "#72778F"
    },
    {
        "name": "Киберпанк",
        "accent": "#A855F7",
        "bg_main": "#15101A",
        "bg_header": "#0D0A12",
        "bg_input": "#221A2D",
        "border": "#3A284D",
        "text_main": "#E5D8F8",
        "text_muted": "#8A779F"
    },
    {
        "name": "Неон",
        "accent": "#F97316",
        "bg_main": "#1A1410",
        "bg_header": "#120D0A",
        "bg_input": "#2D201A",
        "border": "#4D3328",
        "text_main": "#F8E5D8",
        "text_muted": "#9F8077"
    }
]

class ToolTip:
    """Класс для создания всплывающих подсказок при наведении мыши"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip) # Задержка полсекунды перед появлением

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        if self.tipwindow:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#1E1E28", foreground="#D4D8E8",
            relief=tk.SOLID, borderwidth=1,
            font=("Segoe UI", 8)
        )
        label.pack(ipadx=4, ipady=2)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def set_dark_title_bar(window):
    """Включает нативную тёмную тему для шапки окна Windows"""
    window.update_idletasks()
    try:
        HWND = ctypes.windll.user32.GetParent(window.winfo_id())
        for attr in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                HWND, attr, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
            )
    except:
        pass

class ScreenTranslatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.is_selecting = False
        self.overlay = None
        self.popup = None
        self.src_lang_name = "Авто / Eng"
        self.dst_lang_name = "Русский"
        self.theme_index = 0
        self.is_topmost = True
        
        self.last_image = None
        self.last_coords = (100, 100)
        self.font_size = 11
        
        self.show_loading_screen()
        self.setup_dark_styles()

    def get_theme(self):
        return THEMES[self.theme_index]

    def show_loading_screen(self):
        load_win = tk.Toplevel(self.root)
        load_win.overrideredirect(True)
        load_win.attributes('-topmost', True)
        colors = self.get_theme()
        load_win.configure(bg=colors["bg_main"])
        
        w, h = 260, 70
        screen_w = load_win.winfo_screenwidth()
        screen_h = load_win.winfo_screenheight()
        x = (screen_w // 2) - (w // 2)
        y = (screen_h // 2) - (h // 2)
        load_win.geometry(f"{w}x{h}+{x}+{y}")

        frame = tk.Frame(
            load_win, bg=colors["bg_main"],
            highlightbackground=colors["border"], highlightthickness=1
        )
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame, text="⚡ Game Translator", fg=colors["accent"],
            bg=colors["bg_main"], font=('Segoe UI', 10, 'bold')
        ).pack(pady=(10, 2))

        tk.Label(
            frame, text="Запуск в фоновом режиме...", fg=colors["text_muted"],
            bg=colors["bg_main"], font=('Segoe UI', 8)
        ).pack()

        load_win.after(1200, load_win.destroy)

    def setup_dark_styles(self):
        colors = self.get_theme()
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure(
            'Dark.TCombobox',
            fieldbackground=colors["bg_input"],
            background=colors["bg_input"],
            foreground=colors["text_main"],
            arrowcolor=colors["accent"],
            bordercolor=colors["border"],
            lightcolor=colors["bg_input"],
            darkcolor=colors["bg_input"],
            padding=2
        )
        style.map(
            'Dark.TCombobox',
            fieldbackground=[('readonly', colors["bg_input"])],
            selectbackground=[('readonly', colors["bg_input"])],
            selectforeground=[('readonly', colors["text_main"])]
        )

        self.root.option_add('*TCombobox*Listbox.background', colors["bg_input"])
        self.root.option_add('*TCombobox*Listbox.foreground', colors["text_main"])
        self.root.option_add('*TCombobox*Listbox.selectBackground', colors["accent"])
        self.root.option_add('*TCombobox*Listbox.selectForeground', colors["bg_header"])

    def close_all(self, event=None):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        if self.overlay and self.overlay.winfo_exists():
            self.overlay.destroy()
        self.is_selecting = False

    def start_selection(self):
        if self.is_selecting:
            return
        self.is_selecting = True
        self.root.after(0, self.create_snipping_overlay)

    def create_snipping_overlay(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()

        self.full_screen = ImageGrab.grab()
        self.overlay = tk.Toplevel(self.root)
        colors = self.get_theme()
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)
        self.overlay.attributes('-alpha', 0.35)
        self.overlay.configure(bg=colors["bg_main"], cursor='cross')

        self.canvas = tk.Canvas(self.overlay, bg=colors["bg_main"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.overlay.bind('<Escape>', self.close_all)

    def on_press(self, event):
        colors = self.get_theme()
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline=colors["accent"], width=2
        )

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        end_x, end_y = event.x, event.y
        if self.overlay and self.overlay.winfo_exists():
            self.overlay.destroy()
        self.is_selecting = False

        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)

        if x2 - x1 < 10 or y2 - y1 < 10:
            return

        self.last_image = self.full_screen.crop((x1, y1, x2, y2))
        self.last_coords = (x1, y2)
        threading.Thread(target=self.process_image, daemon=True).start()

    def preprocess_image(self, image):
        w, h = image.size
        img = image.resize((w * 2, h * 2))
        img = ImageOps.grayscale(img)
        img = ImageEnhance.Contrast(img).enhance(1.8)
        return img

    def process_image(self):
        if self.last_image is None:
            return

        ocr_code, trans_code = LANGUAGES[self.src_lang_name]
        _, dst_trans_code = LANGUAGES[self.dst_lang_name]

        if self.src_lang_name == "Авто / Eng":
            ocr_code = "eng+rus"

        processed_img = self.preprocess_image(self.last_image)

        try:
            raw_text = pytesseract.image_to_string(processed_img, lang=ocr_code).strip()
        except Exception:
            raw_text = pytesseract.image_to_string(processed_img, lang='eng').strip()

        clean_text = ' '.join(raw_text.split())

        if not clean_text:
            translated = "Текст не найден. Выбери язык сверху"
        else:
            try:
                translated = MyMemoryTranslator(
                    source=trans_code,
                    target=dst_trans_code
                ).translate(clean_text)
            except Exception as e:
                translated = f"Ошибка перевода: {e}"

        x, y = self.last_coords
        self.root.after(0, lambda: self.show_popup(clean_text, translated, x, y))

    def show_popup(self, original, translated, x, y):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()

        colors = self.get_theme()
        self.popup = tk.Toplevel(self.root)
        self.popup.attributes('-topmost', self.is_topmost)
        self.popup.configure(bg=colors["bg_main"])
        self.popup.title("Game Translator")

        set_dark_title_bar(self.popup)
        self.popup.protocol("WM_DELETE_WINDOW", self.close_all)

        frame = tk.Frame(
            self.popup,
            bg=colors["bg_main"],
            highlightbackground=colors["border"],
            highlightthickness=1
        )
        frame.pack(fill=tk.BOTH, expand=True)

        top_bar = tk.Frame(frame, bg=colors["bg_header"], padx=6, pady=6)
        top_bar.pack(fill=tk.X)

        # Выбор языков
        lang_list = list(LANGUAGES.keys())
        src_var = tk.StringVar(value=self.src_lang_name)
        src_menu = ttk.Combobox(
            top_bar, textvariable=src_var, values=lang_list,
            width=10, font=('Segoe UI', 9), state='readonly', style='Dark.TCombobox'
        )
        src_menu.pack(side=tk.LEFT)
        ToolTip(src_menu, "Язык распознавания текста (OCR)")

        tk.Label(
            top_bar, text="→", fg=colors["accent"],
            bg=colors["bg_header"], font=('Segoe UI', 9, 'bold')
        ).pack(side=tk.LEFT, padx=2)

        dst_var = tk.StringVar(value=self.dst_lang_name)
        dst_menu = ttk.Combobox(
            top_bar, textvariable=dst_var, values=lang_list[1:],
            width=10, font=('Segoe UI', 9), state='readonly', style='Dark.TCombobox'
        )
        dst_menu.pack(side=tk.LEFT)
        ToolTip(dst_menu, "Язык, на который нужно перевести")

        def retranslate(event=None):
            self.src_lang_name = src_var.get()
            self.dst_lang_name = dst_var.get()
            threading.Thread(target=self.process_image, daemon=True).start()

        src_menu.bind('<<ComboboxSelected>>', retranslate)
        dst_menu.bind('<<ComboboxSelected>>', retranslate)

        # Кнопка смены цветовой темы (🎨)
        def cycle_theme():
            self.theme_index = (self.theme_index + 1) % len(THEMES)
            self.setup_dark_styles()
            curr_x = self.popup.winfo_x()
            curr_y = self.popup.winfo_y()
            self.show_popup(original, translated, curr_x, curr_y)

        theme_btn = tk.Button(
            top_bar, text="🎨", bg=colors["bg_header"], fg=colors["accent"],
            font=('Segoe UI', 9), relief='flat', bd=0, cursor='hand2', command=cycle_theme
        )
        theme_btn.pack(side=tk.LEFT, padx=4)
        ToolTip(theme_btn, "Сменить цветовую тему интерфейса")

        # Кнопка «Поверх всех окон» (Булавка)
        def toggle_topmost():
            self.is_topmost = not self.is_topmost
            self.popup.attributes('-topmost', self.is_topmost)
            pin_btn.config(fg=colors["accent"] if self.is_topmost else colors["text_muted"])

        pin_btn = tk.Button(
            top_bar, text="📌", bg=colors["bg_header"], fg=colors["accent"] if self.is_topmost else colors["text_muted"],
            font=('Segoe UI', 9), relief='flat', bd=0, cursor='hand2', command=toggle_topmost
        )
        pin_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(pin_btn, "Закрепить окно поверх игры или сбросить")

        # Текст перевода
        lbl_trans = tk.Label(
            frame, text=translated, fg=colors["text_main"], bg=colors["bg_main"],
            font=('Segoe UI', self.font_size, 'bold'), wraplength=450, justify='left', padx=14, pady=10
        )
        lbl_trans.pack(anchor='nw', fill=tk.BOTH, expand=True)

        if original:
            lbl_orig = tk.Label(
                frame, text=original, fg=colors["text_muted"], bg=colors["bg_main"],
                font=('Segoe UI', self.font_size - 2), wraplength=450, justify='left', padx=14, pady=(0, 6)
            )
            lbl_orig.pack(anchor='nw', fill=tk.BOTH, expand=True)

        # Ручной ввод
        input_frame = tk.Frame(frame, bg=colors["bg_header"], padx=8, pady=8)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        tk.Label(
            input_frame, text="Или введите текст вручную:", fg=colors["text_muted"],
            bg=colors["bg_header"], font=('Segoe UI', 8)
        ).pack(anchor='w', pady=(0, 2))

        row_frame = tk.Frame(input_frame, bg=colors["bg_header"])
        row_frame.pack(fill=tk.X, pady=(0, 6))

        user_input_box = tk.Entry(
            row_frame, bg=colors["bg_input"], fg=colors["text_main"],
            insertbackground=colors["accent"], relief='flat', font=('Segoe UI', 9)
        )
        user_input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3, padx=(0, 6))
        ToolTip(user_input_box, "Поле для ввода текста вручную с клавиатуры")

        manual_result_lbl = tk.Label(
            input_frame, text="", fg=colors["accent"], bg=colors["bg_header"],
            font=('Segoe UI', 9, 'bold'), wraplength=430, justify='left'
        )
        manual_result_lbl.pack(anchor='w')

        def translate_manual_text(event=None):
            text_val = user_input_box.get().strip()
            if not text_val:
                return
            _, src_code = LANGUAGES[src_var.get()]
            _, dst_code = LANGUAGES[dst_var.get()]
            if src_var.get() == "Авто / Eng":
                src_code = "en-US"
            try:
                res = MyMemoryTranslator(source=src_code, target=dst_code).translate(text_val)
                manual_result_lbl.config(text=f"➔ {res}")
            except Exception as e:
                manual_result_lbl.config(text=f"Ошибка: {e}")

        trans_btn = tk.Button(
            row_frame, text="Перевести", bg=colors["accent"], fg=colors["bg_header"],
            font=('Segoe UI', 8, 'bold'), relief='flat', padx=8, pady=2, cursor='hand2',
            command=translate_manual_text
        )
        trans_btn.pack(side=tk.RIGHT)
        ToolTip(trans_btn, "Нажмите для перевода введенного текста")

        user_input_box.bind('<Return>', translate_manual_text)

        self.popup.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = max(self.popup.winfo_width(), 480)
        win_h = max(self.popup.winfo_height(), 190)

        pos_x = min(x, screen_w - win_w - 20)
        pos_y = min(y + 8, screen_h - win_h - 40)
        self.popup.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        self.popup.bind('<Escape>', self.close_all)
        self.popup.focus_force()

    def run(self, event=None):
        print("Переводчик запущен в фоне! Нажми Alt + Q.")
        keyboard.add_hotkey('alt+q', self.start_selection)
        self.root.mainloop()

if __name__ == '__main__':
    try:
        app = ScreenTranslatorApp()
        app.run()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Критическая ошибка", f"Произошла ошибка при запуске:\n{traceback.format_exc()}")