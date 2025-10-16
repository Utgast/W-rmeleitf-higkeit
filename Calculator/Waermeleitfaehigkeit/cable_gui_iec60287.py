"""
IEC 60287 Kabel-Thermische Analyse GUI
Benutzeroberfläche für wissenschaftlich korrekte Kabelberechnungen
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from cable_model_iec60287 import (
    CableConfiguration, CableLayer, CableMaterialLibrary
)
from material_database import MaterialDatabase


class CableAnalysisGUI:
    """GUI für IEC 60287 konforme Kabelanalyse"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("IEC 60287 Kabel-Thermische Analyse")
        self.root.geometry("1400x900")
        
        self.material_db = MaterialDatabase()
        self.cable = None
        
        self.create_widgets()
        self.load_predefined_cable()
    
    def create_widgets(self):
        """Erstellt alle GUI-Elemente"""
        
        # Haupt-Container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Linke Seite: Eingaben
        input_frame = ttk.LabelFrame(main_frame, text="Kabelkonfiguration", padding="10")
        input_frame.grid(row=0, column=0, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Vordefinierte Kabel
        ttk.Label(input_frame, text="Vordefiniertes Kabel:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.cable_type = tk.StringVar(value="MV 240mm²")
        cable_combo = ttk.Combobox(input_frame, textvariable=self.cable_type, width=30)
        cable_combo['values'] = ["MV 240mm² Cu/XLPE 20kV", "HV 630mm² Cu/XLPE 110kV"]
        cable_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        cable_combo.bind('<<ComboboxSelected>>', lambda e: self.load_predefined_cable())
        
        ttk.Separator(input_frame, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Betriebsparameter
        ttk.Label(input_frame, text="Betriebsparameter", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(input_frame, text="Strom [A]:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.current_var = tk.StringVar(value="400")
        ttk.Entry(input_frame, textvariable=self.current_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(input_frame, text="Umgebungstemperatur [°C]:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.ambient_temp_var = tk.StringVar(value="20")
        ttk.Entry(input_frame, textvariable=self.ambient_temp_var, width=15).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(input_frame, text="Max. Leitertemperatur [°C]:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.max_temp_var = tk.StringVar(value="90")
        ttk.Entry(input_frame, textvariable=self.max_temp_var, width=15).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Separator(input_frame, orient='horizontal').grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Externe Umgebung
        ttk.Label(input_frame, text="Externe Umgebung", font=('Arial', 10, 'bold')).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(input_frame, text="Erdreich-Wärmeleitfähigkeit [W/mK]:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.soil_lambda_var = tk.StringVar(value="1.0")
        ttk.Entry(input_frame, textvariable=self.soil_lambda_var, width=15).grid(row=8, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(input_frame, text="Verlegetiefe (äquiv. Radius) [m]:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.burial_depth_var = tk.StringVar(value="1.0")
        ttk.Entry(input_frame, textvariable=self.burial_depth_var, width=15).grid(row=9, column=1, sticky=tk.W, pady=5)
        
        ttk.Separator(input_frame, orient='horizontal').grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Berechnen", command=self.calculate).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Ampacity berechnen", command=self.calculate_ampacity).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Zurücksetzen", command=self.reset).grid(row=0, column=2, padx=5)
        
        # Kabelschichten anzeigen
        ttk.Label(input_frame, text="Kabelschichten:", font=('Arial', 10, 'bold')).grid(row=12, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        layers_frame = ttk.Frame(input_frame)
        layers_frame.grid(row=13, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.layers_text = tk.Text(layers_frame, height=10, width=40, wrap=tk.WORD)
        self.layers_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        layers_scroll = ttk.Scrollbar(layers_frame, orient=tk.VERTICAL, command=self.layers_text.yview)
        layers_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.layers_text['yscrollcommand'] = layers_scroll.set
        
        # Rechte Seite: Ergebnisse und Grafiken
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Ergebnisse
        results_frame = ttk.LabelFrame(right_frame, text="Berechnungsergebnisse", padding="10")
        results_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        
        self.results_text = tk.Text(results_frame, height=8, width=80, wrap=tk.WORD)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Grafik
        graph_frame = ttk.LabelFrame(right_frame, text="Temperaturprofil", padding="10")
        graph_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)
        
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def load_predefined_cable(self):
        """Lädt vordefiniertes Kabel"""
        cable_name = self.cable_type.get()
        
        if "240mm²" in cable_name:
            self.cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
        elif "630mm²" in cable_name:
            self.cable = CableMaterialLibrary.create_hv_cable_630mm2_xlpe()
        else:
            self.cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
        
        self.display_cable_layers()
    
    def display_cable_layers(self):
        """Zeigt Kabelschichten an"""
        if not self.cable:
            return
        
        self.layers_text.delete(1.0, tk.END)
        
        self.layers_text.insert(tk.END, f"Kabel: {self.cable.name}\n\n")
        self.layers_text.insert(tk.END, "Interne Schichten:\n")
        self.layers_text.insert(tk.END, "-" * 40 + "\n")
        
        for i, layer in enumerate(self.cable.layers, 1):
            self.layers_text.insert(tk.END, f"{i}. {layer.name}\n")
            self.layers_text.insert(tk.END, f"   Radien: {layer.inner_radius:.1f} - {layer.outer_radius:.1f} mm\n")
            self.layers_text.insert(tk.END, f"   Lambda: {layer.thermal_conductivity:.3f} W/(m·K)\n\n")
        
        if self.cable.external_layers:
            self.layers_text.insert(tk.END, "\nExterne Schichten:\n")
            self.layers_text.insert(tk.END, "-" * 40 + "\n")
            
            for i, layer in enumerate(self.cable.external_layers, 1):
                self.layers_text.insert(tk.END, f"{i}. {layer.name}\n")
                self.layers_text.insert(tk.END, f"   Lambda: {layer.thermal_conductivity:.3f} W/(m·K)\n\n")
    
    def calculate(self):
        """Führt thermische Berechnung durch"""
        try:
            # Parameter einlesen
            current = float(self.current_var.get())
            ambient_temp = float(self.ambient_temp_var.get())
            max_temp = float(self.max_temp_var.get())
            soil_lambda = float(self.soil_lambda_var.get())
            burial_depth = float(self.burial_depth_var.get())
            
            # Kabel aktualisieren
            self.cable.current = current
            self.cable.ambient_temp = ambient_temp
            self.cable.max_conductor_temp = max_temp
            
            # Externe Umgebung aktualisieren
            if self.cable.external_layers:
                cable_outer_radius = self.cable.layers[-1].outer_radius
                self.cable.external_layers[0].thermal_conductivity = soil_lambda
                self.cable.external_layers[0].inner_radius = cable_outer_radius
                self.cable.external_layers[0].outer_radius = burial_depth * 1000  # m to mm
            
            # Berechnung
            t_conductor, details = self.cable.calculate_conductor_temperature()
            
            # Ergebnisse anzeigen
            self.results_text.delete(1.0, tk.END)
            
            self.results_text.insert(tk.END, f"BERECHNUNGSERGEBNISSE (IEC 60287)\n")
            self.results_text.insert(tk.END, "=" * 80 + "\n\n")
            
            self.results_text.insert(tk.END, f"Betriebsstrom: {current:.1f} A\n")
            self.results_text.insert(tk.END, f"Umgebungstemperatur: {ambient_temp:.1f} °C\n")
            self.results_text.insert(tk.END, f"Leitertemperatur: {t_conductor:.2f} °C\n")
            self.results_text.insert(tk.END, f"Max. erlaubte Temperatur: {max_temp:.1f} °C\n\n")
            
            self.results_text.insert(tk.END, f"Verlustleistung: {details['losses_W_per_m']:.2f} W/m\n")
            self.results_text.insert(tk.END, f"Thermischer Widerstand (gesamt): {details['thermal_resistance_K_m_W']:.4f} K·m/W\n")
            self.results_text.insert(tk.END, f"Temperaturanstieg: {t_conductor - ambient_temp:.2f} K\n")
            self.results_text.insert(tk.END, f"Konvergenz: {details['iterations']} Iterationen\n\n")
            
            # Status
            if t_conductor > max_temp:
                self.results_text.insert(tk.END, "STATUS: WARNUNG - Leitertemperatur überschreitet Maximum!\n")
            else:
                margin = max_temp - t_conductor
                self.results_text.insert(tk.END, f"STATUS: OK - Sicherheitsreserve: {margin:.1f} K\n")
            
            # Temperaturprofil plotten
            self.plot_temperature_profile()
            
        except ValueError as e:
            messagebox.showerror("Eingabefehler", f"Ungültige Eingabe: {e}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Berechnungsfehler: {e}")
    
    def calculate_ampacity(self):
        """Berechnet maximal zulässigen Strom"""
        try:
            # Parameter einlesen
            ambient_temp = float(self.ambient_temp_var.get())
            max_temp = float(self.max_temp_var.get())
            soil_lambda = float(self.soil_lambda_var.get())
            burial_depth = float(self.burial_depth_var.get())
            
            # Kabel aktualisieren
            self.cable.ambient_temp = ambient_temp
            self.cable.max_conductor_temp = max_temp
            
            # Externe Umgebung aktualisieren
            if self.cable.external_layers:
                cable_outer_radius = self.cable.layers[-1].outer_radius
                self.cable.external_layers[0].thermal_conductivity = soil_lambda
                self.cable.external_layers[0].inner_radius = cable_outer_radius
                self.cable.external_layers[0].outer_radius = burial_depth * 1000
            
            # Ampacity berechnen
            i_max, details = self.cable.calculate_max_current()
            
            # Ergebnisse anzeigen
            self.results_text.delete(1.0, tk.END)
            
            self.results_text.insert(tk.END, f"AMPACITY BERECHNUNG (IEC 60287)\n")
            self.results_text.insert(tk.END, "=" * 80 + "\n\n")
            
            self.results_text.insert(tk.END, f"Max. zulässiger Strom: {i_max:.1f} A\n\n")
            
            self.results_text.insert(tk.END, f"Umgebungstemperatur: {ambient_temp:.1f} °C\n")
            self.results_text.insert(tk.END, f"Max. Leitertemperatur: {max_temp:.1f} °C\n")
            self.results_text.insert(tk.END, f"Erreichte Leitertemperatur: {details['conductor_temp_C']:.2f} °C\n\n")
            
            self.results_text.insert(tk.END, f"Verlustleistung bei I_max: {details['losses_W_per_m']:.2f} W/m\n")
            self.results_text.insert(tk.END, f"Thermischer Widerstand: {details['thermal_resistance_K_m_W']:.4f} K·m/W\n\n")
            
            self.results_text.insert(tk.END, "Hinweis: Strom automatisch in Eingabefeld übernommen.\n")
            
            # Strom in Eingabefeld übernehmen
            self.current_var.set(f"{i_max:.1f}")
            
            # Temperaturprofil plotten
            self.plot_temperature_profile()
            
        except ValueError as e:
            messagebox.showerror("Eingabefehler", f"Ungültige Eingabe: {e}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Berechnungsfehler: {e}")
    
    def plot_temperature_profile(self):
        """Plottet Temperaturprofil"""
        try:
            profile = self.cable.calculate_temperature_profile()
            
            if not profile:
                return
            
            # Daten extrahieren
            radii = [r for r, t, l in profile]
            temps = [t for r, t, l in profile]
            
            # Plot erstellen
            self.ax.clear()
            
            self.ax.plot(radii, temps, 'b-', linewidth=2, label='Temperaturverlauf')
            self.ax.scatter(radii, temps, color='red', s=30, zorder=5)
            
            # Schichtgrenzen markieren
            for layer in self.cable.layers:
                self.ax.axvline(x=layer.outer_radius, color='gray', linestyle='--', alpha=0.5)
                
                # Label
                mid_radius = (layer.inner_radius + layer.outer_radius) / 2
                y_pos = self.ax.get_ylim()[1] * 0.95
                self.ax.text(mid_radius, y_pos, layer.name, 
                           rotation=90, fontsize=7, ha='center', va='top')
            
            # Grenztemperatur
            self.ax.axhline(y=self.cable.max_conductor_temp, color='red', 
                          linestyle='--', label=f'Max. Temp: {self.cable.max_conductor_temp}°C')
            
            self.ax.axhline(y=self.cable.ambient_temp, color='blue', 
                          linestyle='--', label=f'Umgebung: {self.cable.ambient_temp}°C')
            
            self.ax.set_xlabel('Radius [mm]', fontsize=10)
            self.ax.set_ylabel('Temperatur [°C]', fontsize=10)
            self.ax.set_title('Temperaturprofil im Kabel (IEC 60287)', fontsize=12, fontweight='bold')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='best')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Plot-Fehler: {e}")
    
    def reset(self):
        """Setzt alle Eingaben zurück"""
        self.current_var.set("400")
        self.ambient_temp_var.set("20")
        self.max_temp_var.set("90")
        self.soil_lambda_var.set("1.0")
        self.burial_depth_var.set("1.0")
        
        self.results_text.delete(1.0, tk.END)
        self.ax.clear()
        self.canvas.draw()
        
        self.load_predefined_cable()


def main():
    """Hauptfunktion"""
    root = tk.Tk()
    app = CableAnalysisGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
