
import os
import json
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from crypto_handler import (
    derive_keys, encrypt_message, decrypt_message,
    generate_hmac, verify_hmac
)
from image_handler import (
    embed_payload, extract_payload, image_quality_metrics
)


APP_DIR = Path(__file__).resolve().parent
IMAGE_DIR = APP_DIR / "image"
OUTPUT_DIR = IMAGE_DIR / "output"
DEFAULT_COVER = IMAGE_DIR / "cover_image.png"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#0B1020"
PANEL = "#121C31"
BORDER = "#263550"
ACCENT = "#0EA5E9"
TEXT = "#F1F5F9"
MUTED = "#9AA8C2"


class StegoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AEGIS | Image Steganography & Cryptography")
        self.geometry("1000x680")
        self.minsize(850, 600)
        self.configure(fg_color=BG)

        self.cover_path = (
            str(DEFAULT_COVER) if DEFAULT_COVER.is_file() else ""
        )
        self.stego_path = ""
        self.preview_ref = None

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=28, pady=24)

        self.show_home()

    def clear_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.preview_ref = None

    def header(self, title, back=True):
        top = ctk.CTkFrame(self.container, fg_color="transparent")
        top.pack(fill="x", pady=(0, 24))

        if back:
            ctk.CTkButton(
                top, text="← Back", width=85,
                fg_color=PANEL, hover_color=BORDER,
                command=self.show_home
            ).pack(side="left", padx=(0, 14))

        ctk.CTkLabel(
            top, text=title,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=TEXT
        ).pack(side="left", anchor="center")

    def make_panel(self, parent):
        return ctk.CTkFrame(
            parent, fg_color=PANEL,
            corner_radius=16, border_width=1,
            border_color=BORDER
        )

    def field_label(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", pady=(14, 7))

    def password_field(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")

        entry = ctk.CTkEntry(
            row, height=40, show="*",
            placeholder_text="Enter password",
            fg_color=BG, border_color=BORDER
        )
        entry.pack(side="left", fill="x", expand=True)

        visible = tk.BooleanVar(value=False)

        def toggle_password():
            entry.configure(show="" if visible.get() else "*")

        ctk.CTkCheckBox(
            row, text="Show", variable=visible,
            command=toggle_password, width=65
        ).pack(side="right", padx=(10, 0))

        return entry

    def primary_button(self, parent, text, command):
        ctk.CTkButton(
            parent, text=text, height=44,
            corner_radius=10, fg_color=ACCENT,
            hover_color="#0284C7",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=command
        ).pack(fill="x", pady=(20, 0))

    def show_home(self):
        self.clear_screen()

        ctk.CTkLabel(
            self.container, text="◈  AEGIS",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color="#7DD3FC"
        ).pack(pady=(55, 5))

        ctk.CTkLabel(
            self.container,
            text="IMAGE STEGANOGRAPHY & CRYPTOGRAPHY",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=MUTED
        ).pack(pady=(0, 40))

        cards = ctk.CTkFrame(self.container, fg_color="transparent")
        cards.pack(fill="x", padx=35)
        cards.grid_columnconfigure((0, 1), weight=1, uniform="card")

        embed = self.make_panel(cards)
        embed.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        ctk.CTkLabel(
            embed, text="↗",
            font=ctk.CTkFont(size=38),
            text_color="#7DD3FC"
        ).pack(pady=(30, 8))

        ctk.CTkLabel(
            embed, text="Embed Secret",
            font=ctk.CTkFont(size=21, weight="bold"),
            text_color=TEXT
        ).pack(pady=(0, 18))

        ctk.CTkButton(
            embed, text="Get Started  →", height=42,
            fg_color=ACCENT, hover_color="#0284C7",
            command=self.show_embed
        ).pack(fill="x", padx=24, pady=(0, 28))

        extract = self.make_panel(cards)
        extract.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        ctk.CTkLabel(
            extract, text="↙",
            font=ctk.CTkFont(size=38),
            text_color="#7DD3FC"
        ).pack(pady=(30, 8))

        ctk.CTkLabel(
            extract, text="Decrypt Secret",
            font=ctk.CTkFont(size=21, weight="bold"),
            text_color=TEXT
        ).pack(pady=(0, 18))

        ctk.CTkButton(
            extract, text="Get Started  →", height=42,
            fg_color=ACCENT, hover_color="#0284C7",
            command=self.show_extract
        ).pack(fill="x", padx=24, pady=(0, 28))

    def show_embed(self):
        self.clear_screen()
        self.header("Embed Secret")

        body = ctk.CTkFrame(self.container, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        form = self.make_panel(body)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        form.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(form, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=12)

        self.field_label(content, "Cover Image")

        image_row = ctk.CTkFrame(content, fg_color="transparent")
        image_row.pack(fill="x")

        self.cover_label = ctk.CTkLabel(
            image_row, text=self.short_path(self.cover_path),
            text_color=MUTED, anchor="w"
        )
        self.cover_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            image_row, text="Browse", width=85,
            command=self.choose_cover
        ).pack(side="right", padx=(8, 0))

        self.field_label(content, "Password")
        self.embed_password = self.password_field(content)

        self.field_label(content, "Secret Message")
        self.embed_message = ctk.CTkTextbox(
            content, height=150, wrap="word",
            fg_color=BG, border_color=BORDER,
            border_width=1, corner_radius=10
        )
        self.embed_message.pack(fill="both", expand=True)

        self.primary_button(
            content, "ENCRYPT & GENERATE IMAGE",
            self.run_embedding
        )

        preview = self.make_panel(body)
        preview.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        ctk.CTkLabel(
            preview, text="IMAGE PREVIEW",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=16, pady=(18, 8))

        self.preview_label = ctk.CTkLabel(
            preview, text="Select an image",
            text_color=MUTED
        )
        self.preview_label.pack(fill="both", expand=True, padx=12, pady=12)

        self.update_preview(self.cover_path)

    def show_extract(self):
        self.clear_screen()
        self.header("Decrypt Secret")

        panel = self.make_panel(self.container)
        panel.pack(fill="both", expand=True)

        content = ctk.CTkFrame(panel, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=18)

        self.field_label(content, "Stego Image")

        image_row = ctk.CTkFrame(content, fg_color="transparent")
        image_row.pack(fill="x")

        self.stego_label = ctk.CTkLabel(
            image_row, text=self.short_path(self.stego_path),
            text_color=MUTED, anchor="w"
        )
        self.stego_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            image_row, text="Browse", width=90,
            command=self.choose_stego
        ).pack(side="right", padx=(8, 0))

        self.field_label(content, "Password")
        self.extract_password = self.password_field(content)

        self.primary_button(
            content, "VERIFY & DECRYPT",
            self.run_extraction
        )

        self.field_label(content, "Recovered Message")

        self.recovered_text = ctk.CTkTextbox(
            content, height=160, wrap="word",
            fg_color=BG, border_color=BORDER,
            border_width=1, corner_radius=10
        )
        self.recovered_text.pack(fill="both", expand=True)
        self.recovered_text.configure(state="disabled")

    @staticmethod
    def short_path(path):
        return Path(path).name if path else "No image selected"

    def update_preview(self, path):
        if not path or not os.path.isfile(path):
            self.preview_label.configure(image=None, text="Select an image")
            return

        try:
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((320, 400))
                photo = ImageTk.PhotoImage(image)

            self.preview_ref = photo
            self.preview_label.configure(image=photo, text="")
        except Exception:
            self.preview_label.configure(
                image=None, text="Preview unavailable"
            )

    def choose_cover(self):
        path = filedialog.askopenfilename(
            title="Select Cover Image",
            initialdir=str(IMAGE_DIR),
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")
            ]
        )

        if path:
            self.cover_path = path
            self.cover_label.configure(text=self.short_path(path))
            self.update_preview(path)

    def choose_stego(self):
        path = filedialog.askopenfilename(
            title="Select Stego Image",
            initialdir=str(OUTPUT_DIR),
            filetypes=[
                ("PNG images", "*.png"),
                ("Image files", "*.png *.jpg *.jpeg")
            ]
        )

        if path:
            self.stego_path = path
            self.stego_label.configure(text=self.short_path(path))

    def run_embedding(self):
        password = self.embed_password.get()
        message = self.embed_message.get("1.0", "end-1c").strip()

        if not self.cover_path or not os.path.isfile(self.cover_path):
            messagebox.showwarning("Image Required", "Select a cover image.")
            return

        if not password:
            messagebox.showwarning("Password Required", "Enter a password.")
            return

        if not message:
            messagebox.showwarning("Message Required", "Enter a message.")
            return

        try:
            salt = os.urandom(16)
            aes_key, hmac_key, embedding_key = derive_keys(password, salt)

            iv, ciphertext = encrypt_message(message, aes_key)
            mac = generate_hmac(iv + ciphertext, hmac_key)

            payload = b"AEG1" + salt + iv + mac + ciphertext

            stamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = OUTPUT_DIR / f"stego_{stamp}.png"

            details = embed_payload(
                self.cover_path, payload,
                embedding_key, str(output_path)
            )

            metrics = image_quality_metrics(
                self.cover_path, str(output_path)
            )

            report = {
                "method": "Texture-ranked blue-channel LSB",
                "payload_bytes": details["payload_bytes"],
                "capacity_bytes": details["capacity_bytes"],
                "width": details["width"],
                "height": details["height"],
                "mse": metrics["mse"],
                "psnr_db": metrics["psnr_db"],
                "output_file": str(output_path)
            }

            output_path.with_suffix(".json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )

            messagebox.showinfo(
                "Success",
                f"Stego image saved successfully:\n{output_path}"
            )

        except Exception as exc:
            messagebox.showerror("Embedding Failed", str(exc))

    def run_extraction(self):
        password = self.extract_password.get()

        if not self.stego_path or not os.path.isfile(self.stego_path):
            messagebox.showwarning("Image Required", "Select a stego image.")
            return

        if not password:
            messagebox.showwarning("Password Required", "Enter a password.")
            return

        try:
            _, _, embedding_key = derive_keys(password, b"\x00" * 16)
            payload, _ = extract_payload(
                self.stego_path, embedding_key
            )

            if len(payload) < 68 or payload[:4] != b"AEG1":
                raise ValueError("No valid AEGIS payload found.")

            salt = payload[4:20]
            iv = payload[20:36]
            mac = payload[36:68]
            ciphertext = payload[68:]

            aes_key, hmac_key, _ = derive_keys(password, salt)

            if not verify_hmac(iv + ciphertext, mac, hmac_key):
                raise ValueError(
                    "Authentication failed. Check the password or image."
                )

            message = decrypt_message(iv, ciphertext, aes_key)

            self.recovered_text.configure(state="normal")
            self.recovered_text.delete("1.0", "end")
            self.recovered_text.insert("1.0", message)
            self.recovered_text.configure(state="disabled")

        except Exception as exc:
            messagebox.showerror("Decryption Failed", str(exc))


if __name__ == "__main__":
    app = StegoApp()
    app.mainloop()