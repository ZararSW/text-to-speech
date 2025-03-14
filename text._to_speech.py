import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import tempfile
import threading
import time
import sys

class TextToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EchoLingual - Multi-Language Text to Speech")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # Set theme
        self.set_theme()
        
        # Check for dependencies before proceeding
        if not self.check_dependencies():
            return
            
        # Initialize pygame mixer
        import pygame
        pygame.mixer.init()
        
        # Temp file for audio
        self.audio_file = os.path.join(tempfile.gettempdir(), "speech.mp3")
        
        # Available languages (common ones)
        self.languages = {
            "English": "en",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Portuguese": "pt",
            "Russian": "ru",
            "Japanese": "ja",
            "Korean": "ko",
            "Chinese": "zh-CN",
            "Arabic": "ar",
            "Hindi": "hi"
        }
        
        # History of spoken texts
        self.history = []
        self.max_history = 10
        
        # Create variables for additional features
        self.volume = 0.8  # Default volume
        self.is_playing = False
        self.pause_event = threading.Event()
        
        self.create_widgets()
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        missing_deps = []
        
        try:
            import pygame
        except ImportError:
            missing_deps.append("pygame")
            
        try:
            from gtts import gTTS
        except ImportError:
            missing_deps.append("gtts")
            
        try:
            from PIL import Image
        except ImportError:
            missing_deps.append("pillow")
            
        if missing_deps:
            error_msg = "Missing required libraries:\n"
            for dep in missing_deps:
                error_msg += f"  - {dep}\n"
            error_msg += "\nPlease install them using:\n"
            error_msg += "pip install -r requirements.txt"
            
            messagebox.showerror("Missing Dependencies", error_msg)
            
            # Create a requirements file for the user
            with open("requirements.txt", "w") as f:
                f.write("gtts>=2.2.0\n")
                f.write("pygame>=2.0.0\n")
                f.write("pillow>=8.0.0\n")
            
            self.root.after(500, self.root.destroy)
            return False
        
        return True
        
    def set_theme(self):
        # Try to use a modern theme if available
        try:
            style = ttk.Style()
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
            elif 'alt' in available_themes:
                style.theme_use('alt')
                
            # Define colors
            self.bg_color = "#f5f5f5"
            self.accent_color = "#3498db"
            self.text_bg = "#ffffff"
            self.button_bg = "#2980b9"
            
            style.configure("TFrame", background=self.bg_color)
            style.configure("TLabelframe", background=self.bg_color)
            style.configure("TLabelframe.Label", background=self.bg_color, foreground="#333333", font=("Arial", 10, "bold"))
            style.configure("TButton", background=self.button_bg, foreground="white", font=("Arial", 10, "bold"))
            style.map("TButton", background=[("active", "#3498db")])
            
            self.root.configure(bg=self.bg_color)
        except Exception:
            # Fallback if theme settings fail
            pass
        
    def create_widgets(self):
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)  # Header
        self.root.rowconfigure(1, weight=1)  # Content
        self.root.rowconfigure(2, weight=0)  # Status bar
        
        # Create header frame
        header_frame = ttk.Frame(self.root)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header_frame.columnconfigure(0, weight=1)
        
        # App title
        title_label = ttk.Label(header_frame, text="EchoLingual", 
                               font=("Arial", 18, "bold"), foreground="#2c3e50")
        title_label.grid(row=0, column=0, sticky="w")
        
        # Main content frame
        content_frame = ttk.Frame(self.root)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.columnconfigure(0, weight=3)  # Text input area
        content_frame.columnconfigure(1, weight=1)  # Controls
        content_frame.rowconfigure(0, weight=1)
        
        # Left side - Text input
        left_frame = ttk.LabelFrame(content_frame, text="Enter Text")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=0)
        
        # Text input with scrollbar
        self.text_input = tk.Text(left_frame, wrap=tk.WORD, font=("Arial", 12), 
                                background=self.text_bg, borderwidth=1, relief="solid")
        self.text_input.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add scrollbar to text input
        text_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.text_input.yview)
        text_scroll.grid(row=0, column=1, sticky="ns", pady=5)
        self.text_input.configure(yscrollcommand=text_scroll.set)
        
        # Character count
        self.char_count_var = tk.StringVar()
        self.char_count_var.set("Characters: 0  Words: 0")
        char_count_label = ttk.Label(left_frame, textvariable=self.char_count_var, anchor="e")
        char_count_label.grid(row=1, column=0, columnspan=2, sticky="e", padx=5, pady=(0, 5))
        
        # Bind text changes to update count
        self.text_input.bind("<KeyRelease>", self.update_text_count)
        
        # Right side - Controls
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        for i in range(8):  # Adjust based on number of control sections
            right_frame.rowconfigure(i, weight=0)
        right_frame.rowconfigure(8, weight=1)  # History will expand
        
        # Language selection
        lang_frame = ttk.LabelFrame(right_frame, text="Language")
        lang_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        lang_frame.columnconfigure(0, weight=1)
        
        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, 
                                         values=list(self.languages.keys()), state="readonly")
        self.language_combo.current(0)  # Default to English
        self.language_combo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Voice options
        voice_frame = ttk.LabelFrame(right_frame, text="Voice Options")
        voice_frame.grid(row=1, column=0, sticky="ew", pady=5)
        voice_frame.columnconfigure(0, weight=1)
        voice_frame.columnconfigure(1, weight=1)
        
        # Speed control
        ttk.Label(voice_frame, text="Speed:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.speed_var = tk.BooleanVar()
        self.speed_check = ttk.Checkbutton(voice_frame, text="Slow", variable=self.speed_var)
        self.speed_check.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Volume control
        ttk.Label(voice_frame, text="Volume:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.volume_scale = ttk.Scale(voice_frame, from_=0, to=1, orient="horizontal", 
                                    value=self.volume, command=self.set_volume)
        self.volume_scale.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Playback controls
        playback_frame = ttk.LabelFrame(right_frame, text="Playback")
        playback_frame.grid(row=2, column=0, sticky="ew", pady=5)
        playback_frame.columnconfigure(0, weight=1)
        playback_frame.columnconfigure(1, weight=1)
        playback_frame.columnconfigure(2, weight=1)
        
        # Play button
        self.play_button = ttk.Button(playback_frame, text="Speak", command=self.speak_text)
        self.play_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Pause/Resume button
        self.pause_button = ttk.Button(playback_frame, text="Pause", command=self.pause_resume_speech, state="disabled")
        self.pause_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Stop button
        self.stop_button = ttk.Button(playback_frame, text="Stop", command=self.stop_speech)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # File operations
        file_frame = ttk.LabelFrame(right_frame, text="File Operations")
        file_frame.grid(row=3, column=0, sticky="ew", pady=5)
        file_frame.columnconfigure(0, weight=1)
        file_frame.columnconfigure(1, weight=1)
        
        # Save to file button
        self.save_button = ttk.Button(file_frame, text="Save to MP3", command=self.save_to_file)
        self.save_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Clear button
        self.clear_button = ttk.Button(file_frame, text="Clear Text", command=self.clear_text)
        self.clear_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Progress bar for speech
        progress_frame = ttk.Frame(right_frame)
        progress_frame.grid(row=4, column=0, sticky="ew", pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", 
                                          variable=self.progress_var, mode="determinate")
        self.progress_bar.grid(row=0, column=0, padx=5, sticky="ew")
        
        # History section
        history_frame = ttk.LabelFrame(right_frame, text="History")
        history_frame.grid(row=5, column=0, sticky="nsew", pady=5)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Listbox for history with scrollbar
        self.history_listbox = tk.Listbox(history_frame, height=6, font=("Arial", 10))
        self.history_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        history_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_listbox.yview)
        history_scroll.grid(row=0, column=1, sticky="ns", pady=5)
        self.history_listbox.configure(yscrollcommand=history_scroll.set)
        
        # Double click to load history item
        self.history_listbox.bind("<Double-1>", self.load_history_item)
        
        # Status bar at the bottom
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=2, column=0, sticky="ew")
    
    def update_text_count(self, event=None):
        text = self.text_input.get("1.0", tk.END).strip()
        char_count = len(text)
        word_count = len(text.split()) if text else 0
        self.char_count_var.set(f"Characters: {char_count}  Words: {word_count}")
    
    def set_volume(self, volume):
        import pygame
        self.volume = float(volume)
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(self.volume)
    
    def speak_text(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text to speak")
            return
        
        try:
            import pygame
            from gtts import gTTS
            
            self.status_var.set("Converting text to speech...")
            self.root.update()
            
            # Get language code
            lang_name = self.language_var.get()
            lang_code = self.languages[lang_name]
            
            # Create speech
            tts = gTTS(text=text, lang=lang_code, slow=self.speed_var.get())
            
            # Save to temp file
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)
            tts.save(self.audio_file)
            
            # Add to history if not already there
            if text not in self.history:
                # Truncate if too long
                short_text = (text[:40] + '...') if len(text) > 40 else text
                self.history.insert(0, short_text)
                self.history = self.history[:self.max_history]  # Keep only the most recent items
                self.update_history_display()
            
            # Play the audio with threading to allow pause/resume
            self.is_playing = True
            self.pause_event.set()  # Ensure not paused
            self.play_thread = threading.Thread(target=self.play_audio_with_progress)
            self.play_thread.daemon = True
            self.play_thread.start()
            
            # Update button states
            self.pause_button.configure(text="Pause", state="normal")
            
        except Exception as e:
            self.status_var.set("Error: " + str(e))
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def play_audio_with_progress(self):
        try:
            import pygame
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            
            # Get audio length
            audio_length = pygame.mixer.Sound(self.audio_file).get_length()
            
            # Update status
            lang_name = self.language_var.get()
            self.status_var.set(f"Speaking in {lang_name}...")
            
            # Reset progress bar
            self.progress_var.set(0)
            start_time = time.time()
            
            # Update progress while playing
            while pygame.mixer.music.get_busy() and self.is_playing:
                if not self.pause_event.is_set():
                    # Paused, wait for resume
                    time.sleep(0.1)
                    continue
                
                elapsed = time.time() - start_time
                progress = min(100, (elapsed / audio_length) * 100)
                self.progress_var.set(progress)
                time.sleep(0.1)
            
            # Reset progress when done
            self.progress_var.set(0)
            self.pause_button.configure(state="disabled")
            self.status_var.set("Ready")
            
        except Exception as e:
            self.status_var.set(f"Playback error: {str(e)}")
    
    def pause_resume_speech(self):
        import pygame
        if not pygame.mixer.music.get_busy() and not self.is_playing:
            return
        
        if self.pause_event.is_set():  # Currently playing, pause it
            pygame.mixer.music.pause()
            self.pause_event.clear()
            self.pause_button.configure(text="Resume")
            self.status_var.set("Paused")
        else:  # Currently paused, resume it
            pygame.mixer.music.unpause()
            self.pause_event.set()
            self.pause_button.configure(text="Pause")
            self.status_var.set(f"Speaking in {self.language_var.get()}...")
    
    def stop_speech(self):
        import pygame
        if pygame.mixer.music.get_busy() or self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.pause_event.set()  # Reset pause state
            self.pause_button.configure(state="disabled")
            self.progress_var.set(0)
            self.status_var.set("Speech stopped")
    
    def save_to_file(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text to save")
            return
            
        try:
            from gtts import gTTS
            
            # Get save path from user
            save_path = filedialog.asksaveasfilename(
                defaultextension=".mp3",
                filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
                title="Save Speech As"
            )
            
            if not save_path:  # User cancelled
                return
                
            self.status_var.set("Creating audio file...")
            self.root.update()
            
            # Get language code
            lang_name = self.language_var.get()
            lang_code = self.languages[lang_name]
            
            # Create and save speech
            tts = gTTS(text=text, lang=lang_code, slow=self.speed_var.get())
            tts.save(save_path)
            
            self.status_var.set(f"File saved to: {save_path}")
            
        except Exception as e:
            self.status_var.set("Error: " + str(e))
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def clear_text(self):
        self.text_input.delete("1.0", tk.END)
        self.status_var.set("Text cleared")
        self.update_text_count()
    
    def update_history_display(self):
        self.history_listbox.delete(0, tk.END)
        for item in self.history:
            self.history_listbox.insert(tk.END, item)
    
    def load_history_item(self, event):
        try:
            index = self.history_listbox.curselection()[0]
            selected_text = self.history[index]
            
            # Confirm if the current text should be replaced
            current_text = self.text_input.get("1.0", tk.END).strip()
            if current_text and current_text != selected_text:
                if not messagebox.askyesno("Replace Text", "Replace current text with history item?"):
                    return
            
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", selected_text)
            self.update_text_count()
            
        except (IndexError, Exception):
            pass

def main():
    root = tk.Tk()
    app = TextToSpeechApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 