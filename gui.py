"""
CryptoGuard GUI - Interface graphique avec Tkinter
Version: 0.7.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import main as cg


class CryptoGuardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ CryptoGuard v0.7.0")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e2e")
        
        self.cryptos = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]
        self.currencies = ["usd", "eur", "tnd"]
        self.current_currency = tk.StringVar(value="usd")
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        # ═══ Header ═══
        header = tk.Frame(self.root, bg="#1e1e2e", pady=10)
        header.pack(fill="x")
        
        title = tk.Label(
            header, text="🛡️ CryptoGuard",
            font=("Arial", 20, "bold"),
            bg="#1e1e2e", fg="#89b4fa"
        )
        title.pack(side="left", padx=20)
        
        # ═══ Toolbar ═══
        toolbar = tk.Frame(self.root, bg="#313244", pady=8)
        toolbar.pack(fill="x")
        
        refresh_btn = tk.Button(
            toolbar, text="🔄 Refresh",
            command=self.refresh_data,
            bg="#a6e3a1", fg="#1e1e2e",
            font=("Arial", 10, "bold"),
            padx=15, pady=5, relief="flat"
        )
        refresh_btn.pack(side="left", padx=10)
        
        # اختيار العملة
        tk.Label(
            toolbar, text="Devise:",
            bg="#313244", fg="white",
            font=("Arial", 10)
        ).pack(side="left", padx=(20, 5))
        
        for curr in self.currencies:
            rb = tk.Radiobutton(
                toolbar, text=curr.upper(),
                variable=self.current_currency,
                value=curr,
                command=self.refresh_data,
                bg="#313244", fg="white",
                selectcolor="#89b4fa",
                activebackground="#313244",
                font=("Arial", 10)
            )
            rb.pack(side="left", padx=5)
        
        # ═══ Table ═══
        table_frame = tk.Frame(self.root, bg="#1e1e2e")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#313244",
                        foreground="white",
                        fieldbackground="#313244",
                        rowheight=30,
                        font=("Arial", 10))
        style.configure("Treeview.Heading",
                        background="#89b4fa",
                        foreground="#1e1e2e",
                        font=("Arial", 11, "bold"))
        style.map("Treeview",
                  background=[("selected", "#89b4fa")],
                  foreground=[("selected", "#1e1e2e")])
        
        columns = ("Symbole", "Nom", "Prix", "24h", "Market Cap")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ألوان للصفوف
        self.tree.tag_configure("up", foreground="#a6e3a1")    # أخضر
        self.tree.tag_configure("down", foreground="#f38ba8")  # أحمر
        
        # ═══ Status bar ═══
        self.status = tk.Label(
            self.root, text="Prêt",
            bg="#313244", fg="white",
            font=("Arial", 9), anchor="w", padx=10
        )
        self.status.pack(fill="x", side="bottom")
    
    def refresh_data(self):
        """تحديث البيانات"""
        self.status.config(text="⏳ Chargement des données...")
        self.root.update()
        
        # نحذفو القديم
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # نجيبو البيانات
        currency = self.current_currency.get()
        
        if currency == "tnd":
            data = cg.fetch_prices("usd", self.cryptos)
            taux = cg.get_exchange_rate("TND")
            if data and taux:
                for coin in data:
                    coin["current_price"] *= taux
                    coin["market_cap"] *= taux
        else:
            data = cg.fetch_prices(currency, self.cryptos)
        
        if not data:
            self.status.config(text="❌ Erreur: Impossible de récupérer les données")
            messagebox.showerror("Erreur", "Impossible de récupérer les données.\nVérifiez votre connexion.")
            return
        
        # نضيفو البيانات
        for coin in data:
            symbol = coin["symbol"].upper()
            name = coin["name"]
            price = f"{coin['current_price']:,.2f}"
            change = coin.get("price_change_percentage_24h", 0) or 0
            
            if change >= 0:
                change_str = f"▲ +{change:.2f}%"
                tag = "up"
            else:
                change_str = f"▼ {change:.2f}%"
                tag = "down"
            
            market_cap = f"{coin['market_cap']:,.0f}"
            
            self.tree.insert("", "end",
                             values=(symbol, name, price, change_str, market_cap),
                             tags=(tag,))
        
        now = datetime.now().strftime("%H:%M:%S")
        self.status.config(text=f"✅ Dernière mise à jour: {now}  |  {len(data)} cryptos  |  Devise: {currency.upper()}")


def main():
    root = tk.Tk()
    app = CryptoGuardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()