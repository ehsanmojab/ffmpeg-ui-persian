import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import shlex
import json
import os
import threading

# --- تنظیمات ظاهری ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class FFmpegGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("رابط کاربری FFmpeg")
        self.geometry("850x800")

        self.ffmpeg_path = "ffmpeg"
        self.ffprobe_path = "ffprobe"
        self.check_ffmpeg_ffprobe()

        self.input_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()
        self.operation_var = tk.StringVar(value="تبدیل فرمت")

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(input_frame, text="فایل ورودی:").pack(side="left", padx=5)
        self.input_entry = ctk.CTkEntry(input_frame, textvariable=self.input_file_path, width=350)
        self.input_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.select_input_button = ctk.CTkButton(input_frame, text="انتخاب فایل", command=self.select_input_file)
        self.select_input_button.pack(side="left", padx=5)

        self.operation_frame = ctk.CTkFrame(main_frame) # Defined here
        self.operation_frame.pack(pady=10, padx=10, fill="x") # Packed here
        ctk.CTkLabel(self.operation_frame, text="عملیات مورد نظر:").pack(side="left", padx=5)
        operations = ["تبدیل فرمت", "فشرده سازی ویدیو", "استخراج اطلاعات", "برش ویدیو"]
        self.operation_menu = ctk.CTkOptionMenu(self.operation_frame, variable=self.operation_var, values=operations, command=self.update_options_ui)
        self.operation_menu.pack(side="left", padx=5)

        # This frame's visibility will be toggled, but it's packed in a stable position
        self.output_widgets_frame = ctk.CTkFrame(main_frame)
        self.output_widgets_frame.pack(pady=10, padx=10, fill="x") # Packed after operation_frame
        ctk.CTkLabel(self.output_widgets_frame, text="فایل خروجی:").pack(side="left", padx=5)
        self.output_entry = ctk.CTkEntry(self.output_widgets_frame, textvariable=self.output_file_path, width=350)
        self.output_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.select_output_button = ctk.CTkButton(self.output_widgets_frame, text="انتخاب مسیر", command=self.select_output_file)
        self.select_output_button.pack(side="left", padx=5)

        self.options_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent", height=350)
        # self.options_frame is packed in update_options_ui relative to main_frame children

        self.info_textbox_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.info_textbox = ctk.CTkTextbox(self.info_textbox_frame, height=350, wrap="word")
        self.info_textbox.pack(fill="both", expand=True)
        # self.info_textbox_frame is packed in update_options_ui relative to main_frame children

        action_frame = ctk.CTkFrame(main_frame)
        action_frame.pack(pady=10, padx=10, fill="x", side="bottom") # Pack action_frame at the bottom
        self.execute_button = ctk.CTkButton(action_frame, text="اجرای عملیات", command=self.execute_ffmpeg_threaded)
        self.execute_button.pack(pady=10)
        self.status_label = ctk.CTkLabel(action_frame, text="وضعیت: آماده", wraplength=750)
        self.status_label.pack(pady=5)
        self.progress_bar = ctk.CTkProgressBar(action_frame, orientation="horizontal", mode="indeterminate")

        self.update_options_ui(self.operation_var.get())

    def check_ffmpeg_ffprobe(self):
        try:
            subprocess.run([self.ffmpeg_path, "-version"], capture_output=True, check=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run([self.ffprobe_path, "-version"], capture_output=True, check=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showinfo("اطلاعات FFmpeg", "FFmpeg/FFprobe در PATH سیستم یافت نشد یا قابل اجرا نیست. لطفاً مسیر آنها را مشخص کنید.")
            new_ffmpeg_path = filedialog.askopenfilename(title="FFmpeg.exe را انتخاب کنید", filetypes=[("Executable", "*.exe")])
            if new_ffmpeg_path:
                self.ffmpeg_path = new_ffmpeg_path
                ffmpeg_dir = os.path.dirname(new_ffmpeg_path)
                ffprobe_candidate = os.path.join(ffmpeg_dir, "ffprobe.exe")
                if os.path.exists(ffprobe_candidate):
                    self.ffprobe_path = ffprobe_candidate
                else:
                    new_ffprobe_path = filedialog.askopenfilename(title="ffprobe.exe را انتخاب کنید", filetypes=[("Executable", "*.exe")])
                    if new_ffprobe_path:
                        self.ffprobe_path = new_ffprobe_path
                    else:
                        messagebox.showerror("خطا", "ffprobe.exe انتخاب نشد. عملکرد برنامه ناقص خواهد بود.")
                        self.quit()
            else:
                messagebox.showerror("خطا", "FFmpeg انتخاب نشد. لطفاً FFmpeg را نصب کرده و در PATH قرار دهید یا مسیر آن را به برنامه بدهید."[...])
                self.quit()

    def select_input_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.input_file_path.set(path)
            base, ext = os.path.splitext(path)
            op = self.operation_var.get()
            suffix_map = {
                "تبدیل فرمت": "_converted",
                "فشرده سازی ویدیو": "_compressed",
                "برش ویدیو": "_trimmed"
            }
            suggested_name = f"{base}{suffix_map.get(op, '_processed')}{ext}"
            self.output_file_path.set(suggested_name)

    def select_output_file(self):
        op = self.operation_var.get()
        default_name = self.output_file_path.get() or "output_file"
        file_types = [("All files", "*.*")]
        current_ext = os.path.splitext(default_name)[1]

        if op == "تبدیل فرمت" and hasattr(self, 'convert_format_var'):
            fmt = self.convert_format_var.get().lower()
            current_ext = f".{fmt}"
            format_map = {
                "mp3": [("MP3 audio", "*.mp3")], "wav": [("WAV audio", "*.wav")],
                "mp4": [("MP4 video", "*.mp4")], "mkv": [("MKV video", "*.mkv")],
                "avi": [("AVI video", "*.avi")], "webm": [("WebM video", "*.webm")],
                "ogg": [("OGG audio", "*.ogg")], "flac": [("FLAC audio", "*.flac")],
                "opus": [("Opus audio", "*.opus")]
            }
            file_types = format_map.get(fmt, []) + [("All files", "*.*")]
        elif op == "فشرده سازی ویدیو":
            codec_name = self.compress_codec_var.get() if hasattr(self, 'compress_codec_var') else ""
            if "libx265" in codec_name: current_ext = ".mkv"
            elif "libx264" in codec_name: current_ext = ".mp4"
            else: current_ext = os.path.splitext(self.input_file_path.get() or ".mp4")[1]
            file_types = [("Video files", f"*{current_ext}"), ("All files", "*.*")]

        base_name, _ = os.path.splitext(default_name)
        initial_file_with_ext = f"{base_name}{current_ext}"

        path = filedialog.asksaveasfilename(defaultextension=current_ext,
                                               initialfile=initial_file_with_ext,
                                               filetypes=file_types)
        if path:
            self.output_file_path.set(path)

    def update_options_ui(self, selected_operation):
        self.options_frame.pack_forget()
        self.info_textbox_frame.pack_forget()

        for widget in self.options_frame.winfo_children():
            widget.destroy()

        if selected_operation == "استخراج اطلاعات":
            self.output_entry.configure(state="disabled")
            if self.output_widgets_frame.winfo_ismapped():
                self.output_widgets_frame.pack_forget()
            # Pack info_textbox_frame before action_frame
            self.info_textbox_frame.pack(pady=10, padx=10, fill="both", expand=True, before=self.output_widgets_frame.master.winfo_children()[-1]) # Try to pack before action_frame
            self.info_textbox.delete("1.0", tk.END)
            self.info_textbox.insert(tk.END, "پس از انتخاب فایل و اجرای عملیات، اطلاعات فایل اینجا نمایش داده خواهد شد.\n")
        else:
            self.output_entry.configure(state="normal")
            if not self.output_widgets_frame.winfo_ismapped():
                self.output_widgets_frame.pack(pady=10, padx=10, fill="x") # Re-pack if hidden
            # Pack options_frame before action_frame
            self.options_frame.pack(pady=10, padx=10, fill="both", expand=True, before=self.output_widgets_frame.master.winfo_children()[-1])


        if selected_operation == "تبدیل فرمت":
            ctk.CTkLabel(self.options_frame, text="فرمت مقصد:").pack(pady=(10,0), padx=10, anchor="w")
            self.convert_format_var = tk.StringVar(value="mp4")
            formats = ["mp4", "mkv", "avi", "mov", "webm", "mp3", "wav", "ogg", "flac", "opus"]
            ctk.CTkOptionMenu(self.options_frame, variable=self.convert_format_var, values=formats).pack(pady=5, padx=10, fill="x")

        elif selected_operation == "فشرده سازی ویدیو":
            ctk.CTkLabel(self.options_frame, text="کدک ویدیو:").pack(pady=(10,0), padx=10, anchor="w")
            self.compress_codec_var = tk.StringVar(value="libx264 (H.264)")
            codecs = ["libx264 (H.264)", "libx265 (H.265/HEVC)"]
            ctk.CTkOptionMenu(self.options_frame, variable=self.compress_codec_var, values=codecs, command=self._update_crf_label).pack(pady=5, padx=10, fill="x")

            self.crf_label_text = tk.StringVar(value="میزان فشرده سازی (CRF برای libx264، کمتر=بهتر، 18-28 معمول):")
            ctk.CTkLabel(self.options_frame, textvariable=self.crf_label_text).pack(pady=(10,0), padx=10, anchor="w")
            self.crf_var = tk.StringVar(value="23")
            ctk.CTkEntry(self.options_frame, textvariable=self.crf_var).pack(pady=5, padx=10, fill="x")
            self._update_crf_label(self.compress_codec_var.get())

            ctk.CTkLabel(self.options_frame, text="پیش تنظیم سرعت (Preset):").pack(pady=(10,0), padx=10, anchor="w")
            self.preset_var = tk.StringVar(value="medium")
            presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
            ctk.CTkOptionMenu(self.options_frame, variable=self.preset_var, values=presets).pack(pady=5, padx=10, fill="x")

            ctk.CTkLabel(self.options_frame, text="بهینه سازی برای (Tune):").pack(pady=(10,0), padx=10, anchor="w")
            self.tune_var = tk.StringVar(value="None")
            tunes = ["None", "film", "animation", "grain", "stillimage", "fastdecode", "zerolatency"]
            ctk.CTkOptionMenu(self.options_frame, variable=self.tune_var, values=tunes).pack(pady=5, padx=10, fill="x")

            ctk.CTkLabel(self.options_frame, text="تغییر اندازه (عرض x ارتفاع - خالی یا -1 برای حفظ نسبت):").pack(pady=(10,0), padx=10, anchor="w")
            res_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
            res_frame.pack(pady=5, padx=10, fill="x")
            self.scale_width_var = tk.StringVar()
            ctk.CTkEntry(res_frame, textvariable=self.scale_width_var, placeholder_text="عرض").pack(side="left", padx=(0,5), expand=True, fill="x")
            ctk.CTkLabel(res_frame, text="x").pack(side="left", padx=5)
            self.scale_height_var = tk.StringVar()
            ctk.CTkEntry(res_frame, textvariable=self.scale_height_var, placeholder_text="ارتفاع").pack(side="left", padx=(5,0), expand=True, fill="x")

            ctk.CTkLabel(self.options_frame, text="تنظیمات صدا:").pack(pady=(10,0), padx=10, anchor="w")
            self.audio_action_var = tk.StringVar(value="Copy Audio")
            audio_options = ["Copy Audio", "Convert Audio (AAC)"]
            ctk.CTkOptionMenu(self.options_frame, variable=self.audio_action_var, values=audio_options, command=self._update_audio_bitrate_visibility).pack(pady=5, padx=10, fill="x")

            self.audio_bitrate_label = ctk.CTkLabel(self.options_frame, text="بیت ریت صدا (مثال: 128k, 192k):")
            self.audio_bitrate_var = tk.StringVar(value="128k")
            self.audio_bitrate_entry = ctk.CTkEntry(self.options_frame, textvariable=self.audio_bitrate_var)
            self._update_audio_bitrate_visibility(self.audio_action_var.get())

        elif selected_operation == "برش ویدیو":
            # This check ensures options_frame is visible before packing into it.
            if not self.options_frame.winfo_ismapped():
                 self.options_frame.pack(pady=10, padx=10, fill="both", expand=True, before=self.output_widgets_frame.master.winfo_children()[-1])

            ctk.CTkLabel(self.options_frame, text="زمان شروع (فرمت HH:MM:SS یا ثانیه):").pack(pady=(10,0), padx=10, anchor="w")
            self.trim_start_var = tk.StringVar(value="00:00:00")
            ctk.CTkEntry(self.options_frame, textvariable=self.trim_start_var).pack(pady=5, padx=10, fill="x")

            ctk.CTkLabel(self.options_frame, text="زمان پایان یا مدت زمان (فرمت HH:MM:SS یا ثانیه):").pack(pady=(10,0), padx=10, anchor="w")
            self.trim_end_var = tk.StringVar(value="00:00:10")
            ctk.CTkEntry(self.options_frame, textvariable=self.trim_end_var).pack(pady=5, padx=10, fill="x")


    def _update_crf_label(self, selected_codec_with_format):
        selected_codec = selected_codec_with_format.split(" ")[0]
        if selected_codec == "libx265":
            self.crf_label_text.set("میزان فشرده سازی (CRF برای libx265، کمتر=بهتر، 20-30 معمول):")
            if self.crf_var.get() == "23": self.crf_var.set("28")
        else:
            self.crf_label_text.set("میزان فشرده سازی (CRF برای libx264، کمتر=بهتر، 18-28 معمول):")
            if self.crf_var.get() == "28": self.crf_var.set("23")

    def _update_audio_bitrate_visibility(self, audio_action):
        if audio_action == "Convert Audio (AAC)":
            self.audio_bitrate_label.pack(in_=self.options_frame, pady=(10,0), padx=10, anchor="w")
            self.audio_bitrate_entry.pack(in_=self.options_frame, pady=5, padx=10, fill="x")
        else:
            self.audio_bitrate_label.pack_forget()
            self.audio_bitrate_entry.pack_forget()

    def _toggle_ui(self, enabled: bool, exclude: list = None):
        """
        Recursively enable/disable interactive widgets.
        exclude: list of widget instances to skip (they will not be changed).
        """
        if exclude is None:
            exclude = []
        state = "normal" if enabled else "disabled"

        def recurse(widget):
            for child in widget.winfo_children():
                if child in exclude:
                    # skip excluded widgets
                    recurse(child)
                    continue
                try:
                    # Try to set state for widgets that support it; ignore exceptions
                    child.configure(state=state)
                except Exception:
                    # widget might not support 'state' (e.g., Frames, Labels) — ignore
                    pass
                recurse(child)

        recurse(self)

    def build_ffmpeg_command(self):
        input_f = self.input_file_path.get()
        output_f = self.output_file_path.get()
        operation = self.operation_var.get()

        if not input_f:
            messagebox.showerror("خطا", "لطفا یک فایل ورودی انتخاب کنید.")
            return None
        if not os.path.exists(input_f):
            messagebox.showerror("خطا", f"فایل ورودی یافت نشد: {input_f}")
            return None

        if operation != "استخراج اطلاعات" and not output_f:
            messagebox.showerror("خطا", "لطفا مسیر فایل خروجی را مشخص کنید.")
            return None

        base_cmd = [self.ffmpeg_path, "-y", "-i", input_f]

        if operation == "تبدیل فرمت":
            target_format = self.convert_format_var.get()
            cmd = base_cmd.copy()
            if target_format in ["mp4", "mkv", "avi", "mov", "webm"]:
                cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"])
                cmd.extend(["-c:a", "aac", "-b:a", "128k"])
            elif target_format in ["mp3", "wav", "ogg", "flac", "opus"]:
                audio_codecs = {"mp3": "libmp3lame", "wav": "pcm_s16le", "ogg": "libvorbis", "flac": "flac", "opus": "libopus"}
                cmd.extend(["-vn", "-c:a", audio_codecs.get(target_format, "aac")])
                if target_format == "mp3": cmd.extend(["-q:a", "2"])
                elif target_format == "opus": cmd.extend(["-b:a", "96k"])
            cmd.append(output_f)
            return cmd

        elif operation == "فشرده سازی ویدیو":
            cmd = base_cmd.copy()
            codec_choice = self.compress_codec_var.get().split(" ")[0]
            cmd.extend(["-c:v", codec_choice])
            cmd.extend(["-preset", self.preset_var.get()])
            cmd.extend(["-crf", self.crf_var.get()])
            if self.tune_var.get() != "None": cmd.extend(["-tune", self.tune_var.get()])
            cmd.extend(["-pix_fmt", "yuv420p"])

            width = self.scale_width_var.get().strip()
            height = self.scale_height_var.get().strip()
            scale_filter_parts = []
            if width or height:
                w_val = width if width else "-1"
                h_val = height if height else "-1"
                is_w_valid = w_val == "-1" or (w_val.isdigit() and int(w_val) > 0)
                is_h_valid = h_val == "-1" or (h_val.isdigit() and int(h_val) > 0)
                if is_w_valid and is_h_valid :
                     scale_filter_parts.append(f"scale={w_val}:{h_val}")
                else:
                    if not (not width and not height):
                        messagebox.showwarning("هشدار مقیاس", "مقادیر عرض/ارتفاع نامعتبر هستند. تغییر اندازه اعمال نخواهد شد.")
            if scale_filter_parts:
                cmd.extend(["-vf", ",".join(scale_filter_parts)])

            audio_action = self.audio_action_var.get()
            if audio_action == "Copy Audio":
                cmd.extend(["-c:a", "copy"])
            elif audio_action == "Convert Audio (AAC)":
                audio_br = self.audio_bitrate_var.get().strip() or "128k"
                cmd.extend(["-c:a", "aac", "-b:a", audio_br])
            cmd.append(output_f)
            return cmd

        elif operation == "استخراج اطلاعات":
            return [self.ffprobe_path, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", input_f]

        elif operation == "برش ویدیو":
            cmd = base_cmd.copy()
            cmd.extend(["-ss", self.trim_start_var.get()])
            end_val = self.trim_end_var.get()
            if ':' in end_val or any(c.isalpha() for c in end_val if c not in '0123456789:.'):
                cmd.extend(["-to", end_val])
            else:
                cmd.extend(["-t", end_val])
            cmd.extend(["-c", "copy"])
            cmd.append(output_f)
            return cmd
        return None

    def execute_ffmpeg_threaded(self):
        cmd_list = self.build_ffmpeg_command()
        if not cmd_list:
            return

        self.status_label.configure(text="وضعیت: در حال پردازش...")
        # ensure execute button is disabled and then disable other interactive widgets
        self.execute_button.configure(state="disabled")
        # exclude widgets that should remain enabled/visible (progress/status)
        self._toggle_ui(False, exclude=[self.execute_button, self.progress_bar, self.status_label])

        self.progress_bar.pack(pady=10, padx=10, fill="x", in_=self.status_label.master)
        self.progress_bar.start()

        thread = threading.Thread(target=self.run_command_in_thread, args=(cmd_list, self.operation_var.get()))
        thread.daemon = True
        thread.start()

    def run_command_in_thread(self, cmd_list, operation):
        try:
            print(f"Executing command: {' '.join(shlex.quote(str(c)) for c in cmd_list)}")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8')
            stdout, stderr = process.communicate()
            self.after(0, self._handle_process_completion, process.returncode, stdout, stderr, operation)
        except FileNotFoundError:
            self.after(0, lambda: self.status_label.configure(text="وضعیت: خطا! FFmpeg یا FFprobe یافت نشد."))
            self.after(0, lambda: messagebox.showerror("خطا", "FFmpeg یا FFprobe در مسیر مشخص شده یا PATH سیستم یافت نشد."))
            self.after(0, self._finalize_ui_after_process)
        except Exception as e:
            error_str = str(e)
            self.after(0, lambda: self.status_label.configure(text=f"وضعیت: خطای ناشناخته در اجرا: {error_str[:100]}"))
            self.after(0, lambda: messagebox.showerror("خطای ناشناخته", error_str))
            self.after(0, self._finalize_ui_after_process)

    def _handle_process_completion(self, returncode, stdout, stderr, operation):
        if returncode == 0:
            if operation == "استخراج اطلاعات":
                if not stdout or not stdout.strip():
                    self.info_textbox.delete("1.0", tk.END)
                    self.info_textbox.insert(tk.END, f"ffprobe خروجی تولید نکرد.\nStderr:\n{stderr}")
                    self.status_label.configure(text="وضعیت: ffprobe خروجی نداشت یا خروجی خالی بود.")
                else:
                    try:
                        data = json.loads(stdout)
                        pretty_data = json.dumps(data, indent=4, ensure_ascii=False)
                        self.info_textbox.delete("1.0", tk.END)
                        self.info_textbox.insert(tk.END, pretty_data)
                        self.status_label.configure(text="وضعیت: اطلاعات با موفقیت استخراج شد.")
                    except json.JSONDecodeError:
                        self.info_textbox.delete("1.0", tk.END)
                        self.info_textbox.insert(tk.END, f"خطا در تجزیه خروجی JSON از ffprobe.\nRaw Output:\n{stdout}\nStderr:\n{stderr}")
                        self.status_label.configure(text="وضعیت: خطا در تجزیه خروجی JSON.")
            else:
                self.status_label.configure(text=f"وضعیت: عملیات '{operation}' با موفقیت انجام شد.")
        else:
            error_message = f"خطا در اجرای دستور '{operation}':\nReturn Code: {returncode}\nStderr:\n{stderr}\nStdout:\n{stdout}"
            self.status_label.configure(text=f"وضعیت: خطا در عملیات '{operation}'.")
            if operation == "استخراج اطلاعات":
                self.info_textbox.delete("1.0", tk.END)
                self.info_textbox.insert(tk.END, error_message)
            else:
                 messagebox.showerror(f"خطای {operation}", f"Return Code: {returncode}\nStderr:\n{stderr[:1000]}...\n\nStdout:\n{stdout[:500]}...")
        self._finalize_ui_after_process()

    def _finalize_ui_after_process(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        # Re-enable previously disabled widgets. keep progress/status as they are.
        self._toggle_ui(True, exclude=[self.progress_bar, self.status_label])
        # Ensure execute button is enabled again
        try:
            self.execute_button.configure(state="normal")
        except Exception:
            pass

if __name__ == "__main__":
    app = FFmpegGUI()
    app.mainloop()
