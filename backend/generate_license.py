import os
import sys
import customtkinter as ctk
from datetime import datetime, timedelta, date
import license_manager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LicenseGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Antigravity CCTV - Admin License Key Generator")
        self.geometry("600x550")
        self.resizable(False, False)
        
        lbl_title = ctk.CTkLabel(self, text="Admin License Key Generator", font=ctk.CTkFont(size=22, weight="bold"))
        lbl_title.pack(pady=(20, 5))
        
        lbl_sub = ctk.CTkLabel(self, text="Generate subscription keys for clients based on Machine HWID.", text_color="gray")
        lbl_sub.pack(pady=(0, 15))
        
        frame = ctk.CTkFrame(self)
        frame.pack(padx=30, pady=10, fill="both", expand=True)
        
        # Client Name
        ctk.CTkLabel(frame, text="Client Name / Company:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 2))
        self.entry_client = ctk.CTkEntry(frame, placeholder_text="e.g. John Doe / ABC Security")
        self.entry_client.pack(fill="x", padx=20, pady=(0, 10))
        
        # Machine HWID
        ctk.CTkLabel(frame, text="Target Machine HWID (or 'UNIVERSAL'):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_hwid = ctk.CTkEntry(frame, placeholder_text="e.g. A1B2-C3D4-E5F6-7890 or UNIVERSAL")
        self.entry_hwid.pack(fill="x", padx=20, pady=(0, 10))
        
        # Subscription Duration
        ctk.CTkLabel(frame, text="Subscription Plan Duration:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(5, 2))
        self.option_duration = ctk.CTkOptionMenu(
            frame,
            values=["30 Days (1 Month Trial)", "90 Days (Quarterly)", "365 Days (1 Year Annual)", "LIFETIME (Permanent)"]
        )
        self.option_duration.set("365 Days (1 Year Annual)")
        self.option_duration.pack(fill="x", padx=20, pady=(0, 15))
        
        # Generate Button
        btn_gen = ctk.CTkButton(frame, text="Generate & Copy License Key", command=self.generate_key, height=40, font=ctk.CTkFont(size=14, weight="bold"))
        btn_gen.pack(fill="x", padx=20, pady=10)
        
        # Output Text Box
        self.text_output = ctk.CTkTextbox(frame, height=100)
        self.text_output.pack(fill="x", padx=20, pady=10)
        
    def generate_key(self):
        client = self.entry_client.get().strip() or "Valued Client"
        hwid = self.entry_hwid.get().strip().upper() or "UNIVERSAL"
        duration_choice = self.option_duration.get()
        
        if "30 Days" in duration_choice:
            exp_date = str(date.today() + timedelta(days=30))
        elif "90 Days" in duration_choice:
            exp_date = str(date.today() + timedelta(days=90))
        elif "365 Days" in duration_choice:
            exp_date = str(date.today() + timedelta(days=365))
        else:
            exp_date = "LIFETIME"
            
        lic_key = license_manager.generate_license_key(client, hwid, exp_date, plan_name="PRO")
        
        self.text_output.delete("1.0", "end")
        self.text_output.insert("1.0", f"=== LICENSE KEY FOR {client.upper()} ===\n")
        self.text_output.insert("end", f"HWID: {hwid}\n")
        self.text_output.insert("end", f"EXPIRY: {exp_date}\n\n")
        self.text_output.insert("end", lic_key)
        
        # Copy to clipboard
        self.clipboard_clear()
        self.clipboard_append(lic_key)
        
        # Also write license.lic file locally for quick testing
        license_manager.save_license(lic_key)

if __name__ == "__main__":
    app = LicenseGeneratorApp()
    app.mainloop()
