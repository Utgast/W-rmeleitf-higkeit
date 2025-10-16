"""
Kabel Wärmeleitfähigkeit Calculator
Speziell für HGÜ-Kabel mit Schichtaufbau und Wärmeausbreitung
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from material_database import MaterialDatabase
from thermal_calculator import ThermalCalculator
from datetime import datetime


class CableHeatCalculator:
    """Wärmeberechnung für Kabel mit Umgebungsschichten"""
    
    def __init__(self):
        self.db = MaterialDatabase()
        self.calc = ThermalCalculator()
    
    def calculate_cable_heat_dissipation(self, cable_power, cable_diameter, 
                                        layers_config, ambient_temp):
        """
        Berechnet Wärmeausbreitung vom Kabel durch verschiedene Schichten
        
        Args:
            cable_power: Verlustleistung des Kabels in W/m
            cable_diameter: Kabeldurchmesser in m
            layers_config: Liste von (material, thickness) für jede Schicht
            ambient_temp: Umgebungstemperatur in °C
            
        Returns:
            dict mit Temperaturen, Wärmefluss, etc.
        """
        # Kabelradius
        r_cable = cable_diameter / 2
        
        # Radien der Schichten berechnen
        radii = [r_cable]
        current_radius = r_cable
        
        for material, thickness in layers_config:
            current_radius += thickness
            radii.append(current_radius)
        
        # Thermische Widerstände berechnen (zylindrisch)
        thermal_resistances = []
        layer_details = []
        
        for i, (material, thickness) in enumerate(layers_config):
            lambda_val = self.db.get_lambda(material)
            if lambda_val is None:
                raise ValueError(f"Material '{material}' nicht gefunden")
            
            r_inner = radii[i]
            r_outer = radii[i + 1]
            
            # Thermischer Widerstand für Zylinder: R = ln(r_outer/r_inner) / (2π * λ * L)
            # Pro Meter Länge (L=1m)
            R_thermal = np.log(r_outer / r_inner) / (2 * np.pi * lambda_val)
            
            thermal_resistances.append(R_thermal)
            layer_details.append({
                'material': material,
                'thickness_m': thickness,
                'r_inner_m': r_inner,
                'r_outer_m': r_outer,
                'lambda_W_mK': lambda_val,
                'R_thermal_mK_W': R_thermal
            })
        
        # Gesamter thermischer Widerstand
        R_total = sum(thermal_resistances)
        
        # Temperatur an der Kabeloberfläche
        temp_cable_surface = ambient_temp + (cable_power * R_total)
        
        # Temperaturen an jeder Schichtgrenze berechnen
        temperatures = [temp_cable_surface]
        current_temp = temp_cable_surface
        
        for R in thermal_resistances:
            current_temp = current_temp - (cable_power * R)
            temperatures.append(current_temp)
        
        # Temperaturverteilung innerhalb der Schichten (hochauflösend)
        detailed_positions = []
        detailed_temps = []
        
        for i, (material, thickness) in enumerate(layers_config):
            r_inner = radii[i]
            r_outer = radii[i + 1]
            lambda_val = layer_details[i]['lambda_W_mK']
            temp_inner = temperatures[i]
            temp_outer = temperatures[i + 1]
            
            # 50 Punkte pro Schicht
            n_points = 50
            for j in range(n_points + 1):
                ratio = j / n_points
                r = r_inner + ratio * thickness
                
                # Logarithmische Temperaturverteilung in Zylinder
                if r_outer > r_inner:
                    ln_ratio = np.log(r / r_inner) / np.log(r_outer / r_inner)
                    temp = temp_inner - (temp_inner - temp_outer) * ln_ratio
                else:
                    temp = temp_inner
                
                detailed_positions.append(r)
                detailed_temps.append(temp)
        
        return {
            'cable_surface_temp_C': temp_cable_surface,
            'ambient_temp_C': ambient_temp,
            'temp_difference_K': temp_cable_surface - ambient_temp,
            'total_thermal_resistance_mK_W': R_total,
            'cable_power_W_m': cable_power,
            'layer_temperatures_C': temperatures,
            'layer_radii_m': radii,
            'layer_details': layer_details,
            'detailed_positions_m': detailed_positions,
            'detailed_temps_C': detailed_temps
        }
    
    def calculate_cable_ampacity(self, max_conductor_temp, cable_diameter,
                                 conductor_resistance, layers_config, ambient_temp):
        """
        Berechnet maximalen Strom basierend auf Temperaturgrenze
        
        Args:
            max_conductor_temp: Maximale Leitertemperatur in °C
            cable_diameter: Kabeldurchmesser in m
            conductor_resistance: Leiterwiderstand in Ohm/m
            layers_config: Schichtaufbau
            ambient_temp: Umgebungstemperatur in °C
            
        Returns:
            dict mit maximalem Strom und Details
        """
        # Binäre Suche für maximalen Strom
        I_min = 0
        I_max = 10000  # Start mit 10 kA
        tolerance = 0.1
        
        while I_max - I_min > tolerance:
            I_test = (I_min + I_max) / 2
            
            # Verlustleistung: P = I² * R
            power = I_test ** 2 * conductor_resistance
            
            result = self.calculate_cable_heat_dissipation(
                power, cable_diameter, layers_config, ambient_temp
            )
            
            temp_conductor = result['cable_surface_temp_C']
            
            if temp_conductor < max_conductor_temp:
                I_min = I_test
            else:
                I_max = I_test
        
        optimal_current = I_min
        optimal_power = optimal_current ** 2 * conductor_resistance
        
        final_result = self.calculate_cable_heat_dissipation(
            optimal_power, cable_diameter, layers_config, ambient_temp
        )
        
        return {
            'max_current_A': optimal_current,
            'power_loss_W_m': optimal_power,
            'conductor_temp_C': final_result['cable_surface_temp_C'],
            'thermal_result': final_result
        }


class CableHeatGUI:
    """GUI für Kabel-Wärmeberechnung"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Kabel Wärmeleitfähigkeit Calculator - ARCADIS HGÜ")
        self.root.geometry("1400x900")
        
        self.calculator = CableHeatCalculator()
        self.db = MaterialDatabase()
        self.layers = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        
        # Header
        header = tk.Frame(self.root, bg="#CC0000", height=70)
        header.pack(fill=tk.X)
        
        title_label = tk.Label(
            header,
            text="🔥 HGÜ-Kabel Wärmeleitfähigkeit & Temperaturausbreitung",
            font=("Arial", 18, "bold"),
            bg="#CC0000",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # Hauptbereich
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linke Seite - Eingaben
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_cable_params(left_frame)
        self.create_layers_section(left_frame)
        
        # Rechte Seite - Visualisierung
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_visualization_section(right_frame)
        self.create_results_section(right_frame)
    
    def create_cable_params(self, parent):
        """Kabelparameter-Eingabe"""
        frame = tk.LabelFrame(parent, text="⚡ Kabelparameter", 
                             font=("Arial", 12, "bold"), fg="#CC0000")
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid-Layout
        row = 0
        
        # Kabeldurchmesser
        tk.Label(frame, text="Kabeldurchmesser (mm):", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.cable_diameter_entry = tk.Entry(frame, width=15)
        self.cable_diameter_entry.grid(row=row, column=1, padx=10, pady=5)
        self.cable_diameter_entry.insert(0, "150")
        tk.Label(frame, text="(typisch: 100-200mm)", font=("Arial", 8), fg="gray").grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1
        
        # Verlustleistung
        tk.Label(frame, text="Verlustleistung (W/m):", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.power_loss_entry = tk.Entry(frame, width=15)
        self.power_loss_entry.grid(row=row, column=1, padx=10, pady=5)
        self.power_loss_entry.insert(0, "50")
        tk.Label(frame, text="(Wärmeverlust pro Meter)", font=("Arial", 8), fg="gray").grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1
        
        # Umgebungstemperatur
        tk.Label(frame, text="Umgebungstemperatur (°C):", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.ambient_temp_entry = tk.Entry(frame, width=15)
        self.ambient_temp_entry.grid(row=row, column=1, padx=10, pady=5)
        self.ambient_temp_entry.insert(0, "15")
        tk.Label(frame, text="(Erdreich-Temperatur)", font=("Arial", 8), fg="gray").grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1
        
        # Max. Leitertemperatur
        tk.Label(frame, text="Max. Leitertemperatur (°C):", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.max_temp_entry = tk.Entry(frame, width=15)
        self.max_temp_entry.grid(row=row, column=1, padx=10, pady=5)
        self.max_temp_entry.insert(0, "90")
        tk.Label(frame, text="(typisch: 70-90°C)", font=("Arial", 8), fg="gray").grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
    
    def create_layers_section(self, parent):
        """Schichten-Editor"""
        frame = tk.LabelFrame(parent, text="📦 Schichtaufbau (von Kabel nach außen)", 
                             font=("Arial", 12, "bold"), fg="#CC0000")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Schnellauswahl
        quick_frame = tk.Frame(frame)
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(quick_frame, text="Schnellauswahl:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(quick_frame, text="Schutzrohr + Erdreich", 
                 command=self.add_protection_pipe_earth,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
        
        tk.Button(quick_frame, text="Direkterdverlegung", 
                 command=self.add_direct_earth,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)
        
        tk.Button(quick_frame, text="Rohr + Beton + Erdreich", 
                 command=self.add_pipe_concrete_earth,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        
        # Treeview für Schichten
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("Nr", "Material", "Dicke (mm)", "λ (W/mK)")
        self.layers_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.layers_tree.heading(col, text=col)
        
        self.layers_tree.column("Nr", width=40)
        self.layers_tree.column("Material", width=200)
        self.layers_tree.column("Dicke (mm)", width=100)
        self.layers_tree.column("λ (W/mK)", width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.layers_tree.yview)
        self.layers_tree.configure(yscroll=scrollbar.set)
        
        self.layers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(btn_frame, text="➕ Schicht hinzufügen", 
                 command=self.add_custom_layer,
                 bg="#4CAF50", fg="white", width=18).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="🗑️ Schicht entfernen", 
                 command=self.remove_layer,
                 bg="#f44336", fg="white", width=18).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="🧹 Alle löschen", 
                 command=self.clear_layers,
                 bg="#9E9E9E", fg="white", width=15).pack(side=tk.LEFT, padx=2)
        
        # Berechnen Button
        calc_frame = tk.Frame(frame)
        calc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(calc_frame, text="🔥 WÄRMEAUSBREITUNG BERECHNEN", 
                 command=self.calculate_heat_dissipation,
                 bg="#CC0000", fg="white", font=("Arial", 12, "bold"),
                 height=2).pack(fill=tk.X)
    
    def create_visualization_section(self, parent):
        """Visualisierungsbereich"""
        frame = tk.LabelFrame(parent, text="📊 Temperaturverteilung", 
                             font=("Arial", 12, "bold"), fg="#CC0000")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.canvas_frame = tk.Frame(frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_results_section(self, parent):
        """Ergebnisbereich"""
        frame = tk.LabelFrame(parent, text="📋 Berechnungsergebnisse", 
                             font=("Arial", 12, "bold"), fg="#CC0000")
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = tk.Text(frame, height=12, font=("Courier", 9), 
                                    bg="#f5f5f5", wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def add_protection_pipe_earth(self):
        """Schutzrohr + Erdreich"""
        self.clear_layers()
        self.layers = [
            ("Kunststoff (PE)", 0.010),  # 10mm Schutzrohr
            ("Luftschicht (ruhend)", 0.020),  # 20mm Luftspalt
            ("Erdreich (feucht)", 0.500)  # 500mm Erdreich
        ]
        self.update_layers_display()
    
    def add_direct_earth(self):
        """Direkterdverlegung"""
        self.clear_layers()
        self.layers = [
            ("Sand (trocken)", 0.050),  # 50mm Sandbettung
            ("Erdreich (feucht)", 0.500)  # 500mm Erdreich
        ]
        self.update_layers_display()
    
    def add_pipe_concrete_earth(self):
        """Rohr + Beton + Erdreich"""
        self.clear_layers()
        self.layers = [
            ("Kunststoff (PE)", 0.010),  # 10mm Schutzrohr
            ("Luftschicht (ruhend)", 0.020),  # 20mm Luft
            ("Beton (Normal)", 0.100),  # 100mm Beton
            ("Erdreich (feucht)", 0.400)  # 400mm Erdreich
        ]
        self.update_layers_display()
    
    def add_custom_layer(self):
        """Benutzerdefinierte Schicht hinzufügen"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Schicht hinzufügen")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Material wählen:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )
        
        # Material Dropdown nach Kategorie
        materials_by_category = {
            "Schutzrohre": ["Kunststoff (PE)", "Stahl"],
            "Bettung": ["Sand (trocken)", "Sand (feucht)", "Beton (Normal)", "Mörtel"],
            "Erdreich": ["Erdreich (trocken)", "Erdreich (feucht)", "Lehm"],
            "Luft/Isolierung": ["Luftschicht (ruhend)", "Mineralwolle", "Polystyrol (EPS)"],
            "Alle Materialien": sorted(self.db.get_all_materials())
        }
        
        tk.Label(dialog, text="Kategorie:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        category_combo = ttk.Combobox(dialog, values=list(materials_by_category.keys()), 
                                     width=30, state="readonly")
        category_combo.grid(row=1, column=1, padx=10, pady=5)
        category_combo.set("Schutzrohre")
        
        tk.Label(dialog, text="Material:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        material_combo = ttk.Combobox(dialog, values=materials_by_category["Schutzrohre"], 
                                     width=30)
        material_combo.grid(row=2, column=1, padx=10, pady=5)
        material_combo.set("Kunststoff (PE)")
        
        def on_category_change(event):
            category = category_combo.get()
            material_combo['values'] = materials_by_category[category]
            if materials_by_category[category]:
                material_combo.set(materials_by_category[category][0])
        
        category_combo.bind("<<ComboboxSelected>>", on_category_change)
        
        tk.Label(dialog, text="Dicke (mm):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        thickness_entry = tk.Entry(dialog, width=15)
        thickness_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        thickness_entry.insert(0, "10")
        
        # Lambda-Wert anzeigen
        lambda_label = tk.Label(dialog, text="", font=("Arial", 9), fg="blue")
        lambda_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        
        def update_lambda(*args):
            material = material_combo.get()
            lambda_val = self.db.get_lambda(material)
            if lambda_val:
                lambda_label.config(text=f"λ = {lambda_val:.3f} W/(m·K)")
        
        material_combo.bind("<<ComboboxSelected>>", update_lambda)
        update_lambda()
        
        def add():
            material = material_combo.get()
            try:
                thickness = float(thickness_entry.get()) / 1000  # mm -> m
                if thickness <= 0:
                    messagebox.showerror("Fehler", "Dicke muss größer als 0 sein!")
                    return
                
                self.layers.append((material, thickness))
                self.update_layers_display()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Fehler", "Ungültige Dicke!")
        
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="Hinzufügen", command=add, 
                 bg="#4CAF50", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Abbrechen", command=dialog.destroy, 
                 width=12).pack(side=tk.LEFT, padx=5)
    
    def remove_layer(self):
        """Ausgewählte Schicht entfernen"""
        selected = self.layers_tree.selection()
        if selected:
            item = self.layers_tree.item(selected[0])
            index = int(item['values'][0]) - 1
            if 0 <= index < len(self.layers):
                self.layers.pop(index)
                self.update_layers_display()
    
    def clear_layers(self):
        """Alle Schichten löschen"""
        self.layers = []
        self.update_layers_display()
    
    def update_layers_display(self):
        """Aktualisiert die Schichten-Anzeige"""
        for item in self.layers_tree.get_children():
            self.layers_tree.delete(item)
        
        for i, (material, thickness) in enumerate(self.layers, 1):
            lambda_val = self.db.get_lambda(material)
            self.layers_tree.insert("", tk.END, values=(
                i,
                material,
                f"{thickness*1000:.1f}",
                f"{lambda_val:.3f}" if lambda_val else "N/A"
            ))
    
    def calculate_heat_dissipation(self):
        """Führt Wärmeausbreitungsberechnung durch"""
        try:
            if not self.layers:
                messagebox.showwarning("Warnung", "Bitte mindestens eine Schicht hinzufügen!")
                return
            
            # Parameter einlesen
            cable_diameter = float(self.cable_diameter_entry.get()) / 1000  # mm -> m
            power_loss = float(self.power_loss_entry.get())
            ambient_temp = float(self.ambient_temp_entry.get())
            
            # Berechnung durchführen
            result = self.calculator.calculate_cable_heat_dissipation(
                power_loss, cable_diameter, self.layers, ambient_temp
            )
            
            # Ergebnisse anzeigen
            self.display_results(result)
            
            # Visualisierung erstellen
            self.create_temperature_plot(result)
            
        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Berechnung fehlgeschlagen:\n{str(e)}")
    
    def display_results(self, result):
        """Zeigt Berechnungsergebnisse an"""
        output = f"""
╔══════════════════════════════════════════════════════════════╗
║  KABEL-WÄRMEAUSBREITUNG - ERGEBNIS                           ║
╚══════════════════════════════════════════════════════════════╝

TEMPERATUREN:
  Kabeloberfläche:       {result['cable_surface_temp_C']:.2f} °C
  Umgebung:              {result['ambient_temp_C']:.2f} °C
  Temperaturdifferenz:   {result['temp_difference_K']:.2f} K

THERMISCHE EIGENSCHAFTEN:
  Gesamtwiderstand:      {result['total_thermal_resistance_mK_W']:.4f} m·K/W
  Verlustleistung:       {result['cable_power_W_m']:.2f} W/m

SCHICHTTEMPERATUREN:
"""
        
        for i, layer in enumerate(result['layer_details']):
            temp = result['layer_temperatures_C'][i]
            output += f"""
  Schicht {i+1}: {layer['material']}
    Radius innen:        {layer['r_inner_m']*1000:.1f} mm
    Radius außen:        {layer['r_outer_m']*1000:.1f} mm
    Dicke:               {layer['thickness_m']*1000:.1f} mm
    λ:                   {layer['lambda_W_mK']:.3f} W/(m·K)
    Temperatur (innen):  {temp:.2f} °C
    R (thermisch):       {layer['R_thermal_mK_W']:.4f} m·K/W
"""
        
        output += f"\n  Außentemperatur:     {result['layer_temperatures_C'][-1]:.2f} °C\n"
        
        output += """
══════════════════════════════════════════════════════════════

BEURTEILUNG:
"""
        temp_diff = result['temp_difference_K']
        if temp_diff < 20:
            output += "  ✓ Sehr gut - Geringe Erwärmung"
        elif temp_diff < 40:
            output += "  ⚠ Akzeptabel - Moderate Erwärmung"
        elif temp_diff < 60:
            output += "  ⚠⚠ Grenzwertig - Hohe Erwärmung"
        else:
            output += "  ✗ Kritisch - Sehr hohe Erwärmung!"
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, output)
    
    def create_temperature_plot(self, result):
        """Erstellt Temperatur-Visualisierung"""
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot 1: Temperatur vs. Radius
        positions = np.array(result['detailed_positions_m']) * 1000  # m -> mm
        temps = result['detailed_temps_C']
        
        ax1.plot(positions, temps, 'r-', linewidth=2, label='Temperaturverlauf')
        ax1.axhline(y=result['ambient_temp_C'], color='b', linestyle='--', 
                   label=f'Umgebungstemperatur ({result["ambient_temp_C"]:.1f}°C)')
        ax1.axhline(y=result['cable_surface_temp_C'], color='orange', linestyle='--', 
                   label=f'Kabeltemperatur ({result["cable_surface_temp_C"]:.1f}°C)')
        
        # Schichtgrenzen markieren
        for i, radius in enumerate(result['layer_radii_m']):
            ax1.axvline(x=radius*1000, color='gray', linestyle=':', alpha=0.5)
            if i < len(result['layer_details']):
                layer = result['layer_details'][i]
                mid_radius = (layer['r_inner_m'] + layer['r_outer_m']) / 2 * 1000
                ax1.text(mid_radius, ax1.get_ylim()[1]*0.95, 
                        layer['material'].split('(')[0].strip(),
                        ha='center', fontsize=8, rotation=0)
        
        ax1.set_xlabel('Radius vom Kabelmittelpunkt (mm)', fontsize=11)
        ax1.set_ylabel('Temperatur (°C)', fontsize=11)
        ax1.set_title('Radiale Temperaturverteilung', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best', fontsize=9)
        
        # Plot 2: Schichtaufbau
        layer_names = [layer['material'] for layer in result['layer_details']]
        layer_temps = result['layer_temperatures_C'][:-1]  # Ohne letzte (Umgebung)
        layer_widths = [layer['thickness_m']*1000 for layer in result['layer_details']]
        
        colors = plt.cm.RdYlBu_r(np.linspace(0.2, 0.8, len(layer_names)))
        
        ax2.barh(range(len(layer_names)), layer_widths, color=colors)
        ax2.set_yticks(range(len(layer_names)))
        ax2.set_yticklabels([f"{name}\n{temp:.1f}°C" 
                             for name, temp in zip(layer_names, layer_temps)],
                           fontsize=9)
        ax2.set_xlabel('Dicke (mm)', fontsize=11)
        ax2.set_title('Schichtaufbau mit Temperaturen', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def main():
    """Hauptprogramm"""
    root = tk.Tk()
    app = CableHeatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
