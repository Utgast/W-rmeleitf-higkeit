"""
Wärmeleitfähigkeit Calculator - Main Application
Hauptprogramm mit GUI-Interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from material_database import MaterialDatabase
from thermal_calculator import ThermalCalculator
import json
from datetime import datetime


class ThermalCalculatorGUI:
    """Hauptfenster der Anwendung"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Wärmeleitfähigkeit Calculator - ARCADIS")
        self.root.geometry("1200x800")
        
        self.calculator = ThermalCalculator()
        self.db = MaterialDatabase()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        
        # Header
        header = tk.Frame(self.root, bg="#0066CC", height=60)
        header.pack(fill=tk.X)
        
        title_label = tk.Label(
            header,
            text="Wärmeleitfähigkeit Calculator",
            font=("Arial", 20, "bold"),
            bg="#0066CC",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # Notebook für verschiedene Berechnungen
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tabs erstellen
        self.create_heat_flow_tab()
        self.create_u_value_tab()
        self.create_temperature_dist_tab()
        self.create_material_db_tab()
    
    def create_heat_flow_tab(self):
        """Tab für Wärmestrom-Berechnung"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Wärmestrom")
        
        # Eingabebereich
        input_frame = tk.LabelFrame(tab, text="Eingabeparameter", font=("Arial", 12, "bold"))
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Material auswählen
        tk.Label(input_frame, text="Material:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.material_combo = ttk.Combobox(input_frame, values=self.db.get_all_materials(), width=30)
        self.material_combo.grid(row=0, column=1, padx=5, pady=5)
        self.material_combo.set("Beton (Normal)")
        
        # Fläche
        tk.Label(input_frame, text="Fläche (m²):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.area_entry = tk.Entry(input_frame, width=20)
        self.area_entry.grid(row=1, column=1, padx=5, pady=5)
        self.area_entry.insert(0, "10")
        
        # Dicke
        tk.Label(input_frame, text="Dicke (m):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.thickness_entry = tk.Entry(input_frame, width=20)
        self.thickness_entry.grid(row=2, column=1, padx=5, pady=5)
        self.thickness_entry.insert(0, "0.2")
        
        # Temperaturdifferenz
        tk.Label(input_frame, text="Temperaturdifferenz (K):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.temp_diff_entry = tk.Entry(input_frame, width=20)
        self.temp_diff_entry.grid(row=3, column=1, padx=5, pady=5)
        self.temp_diff_entry.insert(0, "20")
        
        # Berechnen Button
        calc_btn = tk.Button(
            input_frame,
            text="Berechnen",
            command=self.calculate_heat_flow,
            bg="#0066CC",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        )
        calc_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Ergebnis-Bereich
        result_frame = tk.LabelFrame(tab, text="Ergebnisse", font=("Arial", 12, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.heat_flow_result_text = tk.Text(result_frame, height=15, font=("Courier", 10))
        self.heat_flow_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_u_value_tab(self):
        """Tab für U-Wert-Berechnung"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="U-Wert")
        
        # Schichten-Eingabe
        input_frame = tk.LabelFrame(tab, text="Wandaufbau (Schichten)", font=("Arial", 12, "bold"))
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview für Schichten
        columns = ("Material", "Dicke (m)", "λ (W/mK)")
        self.layers_tree = ttk.Treeview(input_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.layers_tree.heading(col, text=col)
            self.layers_tree.column(col, width=200)
        
        self.layers_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons für Schichten
        btn_frame = tk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(btn_frame, text="Schicht hinzufügen", command=self.add_layer).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Schicht entfernen", command=self.remove_layer).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="U-Wert berechnen", command=self.calculate_u_value, bg="#0066CC", fg="white").pack(side=tk.LEFT, padx=2)
        
        # Ergebnis
        result_frame = tk.LabelFrame(tab, text="U-Wert Ergebnis", font=("Arial", 12, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.u_value_result_text = tk.Text(result_frame, height=10, font=("Courier", 10))
        self.u_value_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_temperature_dist_tab(self):
        """Tab für Temperaturverteilung"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Temperaturverteilung")
        
        # Eingabe
        input_frame = tk.LabelFrame(tab, text="Parameter", font=("Arial", 12, "bold"))
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(input_frame, text="Innentemperatur (°C):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.temp_inside_entry = tk.Entry(input_frame, width=15)
        self.temp_inside_entry.grid(row=0, column=1, padx=5, pady=5)
        self.temp_inside_entry.insert(0, "20")
        
        tk.Label(input_frame, text="Außentemperatur (°C):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.temp_outside_entry = tk.Entry(input_frame, width=15)
        self.temp_outside_entry.grid(row=0, column=3, padx=5, pady=5)
        self.temp_outside_entry.insert(0, "-10")
        
        tk.Button(
            input_frame,
            text="Temperaturverteilung berechnen",
            command=self.calculate_temp_distribution,
            bg="#0066CC",
            fg="white"
        ).grid(row=1, column=0, columnspan=4, pady=10)
        
        # Grafik
        self.temp_dist_canvas_frame = tk.Frame(tab)
        self.temp_dist_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_material_db_tab(self):
        """Tab für Material-Datenbank"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Material-Datenbank")
        
        # Kategorien
        categories_frame = tk.Frame(tab)
        categories_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        tk.Label(categories_frame, text="Kategorien", font=("Arial", 12, "bold")).pack()
        
        self.category_listbox = tk.Listbox(categories_frame, width=20, height=20)
        self.category_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.category_listbox.bind("<<ListboxSelect>>", self.on_category_select)
        
        # Kategorien füllen
        categories = self.db.get_categories()
        for category in categories.keys():
            self.category_listbox.insert(tk.END, category)
        
        # Materialien
        materials_frame = tk.Frame(tab)
        materials_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(materials_frame, text="Materialien", font=("Arial", 12, "bold")).pack()
        
        columns = ("Material", "λ (W/mK)", "ρ (kg/m³)", "c (J/kgK)")
        self.materials_tree = ttk.Treeview(materials_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.materials_tree.heading(col, text=col)
            self.materials_tree.column(col, width=150)
        
        self.materials_tree.pack(fill=tk.BOTH, expand=True)
        
        # Alle Materialien anzeigen
        self.show_all_materials()
    
    def calculate_heat_flow(self):
        """Berechnet Wärmestrom"""
        try:
            material = self.material_combo.get()
            area = float(self.area_entry.get())
            thickness = float(self.thickness_entry.get())
            temp_diff = float(self.temp_diff_entry.get())
            
            result = self.calculator.calculate_heat_flow(material, area, thickness, temp_diff)
            
            output = f"""
╔═══════════════════════════════════════════════════════════╗
║         WÄRMESTROM-BERECHNUNG - ERGEBNIS                  ║
╚═══════════════════════════════════════════════════════════╝

Material:                {result['material']}
Wärmeleitfähigkeit λ:    {result['lambda_W_mK']:.3f} W/(m·K)

EINGABEPARAMETER:
  Fläche A:              {area:.2f} m²
  Dicke d:               {thickness:.3f} m
  Temperaturdifferenz:   {temp_diff:.1f} K

ERGEBNISSE:
  Wärmestrom Q:          {result['heat_flow_W']:.2f} W
                         {result['heat_flow_W']/1000:.3f} kW
  
  Wärmestromdichte q:    {result['heat_flux_W_m2']:.2f} W/m²
  
  Wärmedurchlass-
  widerstand R:          {result['thermal_resistance_m2K_W']:.4f} m²·K/W

═══════════════════════════════════════════════════════════

Interpretation:
  Durch die {thickness*100:.1f} cm dicke {material}-Schicht
  fließen bei einer Temperaturdifferenz von {temp_diff:.0f} K
  insgesamt {result['heat_flow_W']:.1f} Watt Wärmeleistung.
  
  Pro Quadratmeter Fläche entspricht dies einer
  Wärmestromdichte von {result['heat_flux_W_m2']:.1f} W/m².
"""
            
            self.heat_flow_result_text.delete(1.0, tk.END)
            self.heat_flow_result_text.insert(1.0, output)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Berechnung fehlgeschlagen:\n{str(e)}")
    
    def add_layer(self):
        """Fügt neue Schicht hinzu"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Schicht hinzufügen")
        dialog.geometry("400x200")
        
        tk.Label(dialog, text="Material:").grid(row=0, column=0, padx=10, pady=10)
        material_combo = ttk.Combobox(dialog, values=self.db.get_all_materials(), width=30)
        material_combo.grid(row=0, column=1, padx=10, pady=10)
        material_combo.set("Beton (Normal)")
        
        tk.Label(dialog, text="Dicke (m):").grid(row=1, column=0, padx=10, pady=10)
        thickness_entry = tk.Entry(dialog, width=20)
        thickness_entry.grid(row=1, column=1, padx=10, pady=10)
        thickness_entry.insert(0, "0.1")
        
        def add():
            material = material_combo.get()
            thickness = thickness_entry.get()
            lambda_val = self.db.get_lambda(material)
            
            self.layers_tree.insert("", tk.END, values=(material, thickness, f"{lambda_val:.3f}"))
            dialog.destroy()
        
        tk.Button(dialog, text="Hinzufügen", command=add, bg="#0066CC", fg="white").grid(row=2, column=0, columnspan=2, pady=20)
    
    def remove_layer(self):
        """Entfernt ausgewählte Schicht"""
        selected = self.layers_tree.selection()
        if selected:
            self.layers_tree.delete(selected)
    
    def calculate_u_value(self):
        """Berechnet U-Wert"""
        try:
            layers = []
            for item in self.layers_tree.get_children():
                values = self.layers_tree.item(item)["values"]
                material = values[0]
                thickness = float(values[1])
                layers.append((material, thickness))
            
            if not layers:
                messagebox.showwarning("Warnung", "Keine Schichten definiert!")
                return
            
            result = self.calculator.calculate_u_value(layers)
            
            output = f"""
╔═══════════════════════════════════════════════════════════╗
║         U-WERT-BERECHNUNG - ERGEBNIS                      ║
╚═══════════════════════════════════════════════════════════╝

U-WERT:  {result['u_value_W_m2K']:.3f} W/(m²·K)

GESAMTWIDERSTAND:  {result['total_resistance_m2K_W']:.4f} m²·K/W

WIDERSTÄNDE:
  Innen (Rsi):         {result['R_si']:.3f} m²·K/W
  Außen (Rse):         {result['R_se']:.3f} m²·K/W

SCHICHTEN:
"""
            for i, layer in enumerate(result['layers'], 1):
                output += f"""
  {i}. {layer['material']}
     Dicke:            {layer['thickness_m']*100:.1f} cm
     λ:                {layer['lambda_W_mK']:.3f} W/(m·K)
     R:                {layer['resistance_m2K_W']:.4f} m²·K/W
"""
            
            output += f"""
═══════════════════════════════════════════════════════════

Bewertung nach EnEV:
"""
            u_val = result['u_value_W_m2K']
            if u_val <= 0.20:
                output += "  ★★★★★ Exzellent - Passivhaus-Standard"
            elif u_val <= 0.24:
                output += "  ★★★★☆ Sehr gut - KfW 55"
            elif u_val <= 0.28:
                output += "  ★★★☆☆ Gut - KfW 70"
            elif u_val <= 0.35:
                output += "  ★★☆☆☆ Befriedigend - EnEV Neubau"
            else:
                output += "  ★☆☆☆☆ Verbesserungswürdig"
            
            self.u_value_result_text.delete(1.0, tk.END)
            self.u_value_result_text.insert(1.0, output)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Berechnung fehlgeschlagen:\n{str(e)}")
    
    def calculate_temp_distribution(self):
        """Berechnet und zeigt Temperaturverteilung"""
        try:
            layers = []
            for item in self.layers_tree.get_children():
                values = self.layers_tree.item(item)["values"]
                material = values[0]
                thickness = float(values[1])
                layers.append((material, thickness, 10))  # 10 Punkte pro Schicht
            
            if not layers:
                messagebox.showwarning("Warnung", "Keine Schichten definiert!")
                return
            
            temp_inside = float(self.temp_inside_entry.get())
            temp_outside = float(self.temp_outside_entry.get())
            
            result = self.calculator.calculate_temperature_distribution(
                layers, temp_inside, temp_outside
            )
            
            # Grafik erstellen
            for widget in self.temp_dist_canvas_frame.winfo_children():
                widget.destroy()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(result['positions_m'], result['temperatures_C'], 'b-', linewidth=2)
            ax.set_xlabel('Position (m)', fontsize=12)
            ax.set_ylabel('Temperatur (°C)', fontsize=12)
            ax.set_title('Temperaturverteilung durch den Wandaufbau', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            canvas = FigureCanvasTkAgg(fig, self.temp_dist_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            messagebox.showinfo("Erfolg", f"Wärmestromdichte: {result['heat_flux_W_m2']:.2f} W/m²")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Berechnung fehlgeschlagen:\n{str(e)}")
    
    def on_category_select(self, event):
        """Zeigt Materialien der ausgewählten Kategorie"""
        selection = self.category_listbox.curselection()
        if not selection:
            return
        
        category = self.category_listbox.get(selection[0])
        categories = self.db.get_categories()
        materials = categories.get(category, [])
        
        # Treeview leeren
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)
        
        # Materialien anzeigen
        for mat_name in materials:
            mat = self.db.get_material(mat_name)
            if mat:
                self.materials_tree.insert("", tk.END, values=(
                    mat_name,
                    f"{mat['lambda']:.3f}",
                    mat['density'],
                    mat['specific_heat']
                ))
    
    def show_all_materials(self):
        """Zeigt alle Materialien"""
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)
        
        for mat_name in sorted(self.db.get_all_materials()):
            mat = self.db.get_material(mat_name)
            if mat:
                self.materials_tree.insert("", tk.END, values=(
                    mat_name,
                    f"{mat['lambda']:.3f}",
                    mat['density'],
                    mat['specific_heat']
                ))


def main():
    """Hauptprogramm"""
    root = tk.Tk()
    app = ThermalCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
