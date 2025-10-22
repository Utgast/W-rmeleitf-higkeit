"""
ARCADIS PROFESSIONAL HGÜ THERMAL CALCULATOR
Vereinfachte, aber professionelle Version mit AC/DC Differenzierung
und vollständiger Nachvollziehbarkeit des Berechnungsweges.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
import numpy as np
import math
from datetime import datetime
from collections import defaultdict

# MCP-Validierung
from mcp_calculation_validator import MCPCalculationValidator
from calculation_report_generator_mcp import generate_complete_calculation_report_with_mcp

# ARCADIS Corporate Colors
ARCADIS_ORANGE = '#FF6A00'
ARCADIS_BLUE = '#003A70'
ARCADIS_LIGHT_BLUE = '#0066CC'
ARCADIS_GREY = '#7A7A7A'
ARCADIS_LIGHT_GREY = '#F5F5F5'
ARCADIS_WHITE = '#FFFFFF'


class MaterialDatabase:
    """Professionelle Materialdatenbank für Kabelberechnungen"""

    def __init__(self):
        self.materials = {
            # Leiter
            'Kupfer (Cu)': {
                'lambda': 400,
                'density': 8960,
                'cp': 385,
                'type': 'conductor',
                'color': '#CD7F32'
            },
            'Aluminium (Al)': {
                'lambda': 235,
                'density': 2700,
                'cp': 900,
                'type': 'conductor',
                'color': '#C0C0C0'
            },

            # Isolation
            'XLPE': {
                'lambda': 0.4,
                'density': 920,
                'cp': 2200,
                'type': 'insulation',
                'color': '#8B4513'
            },
            'EPR': {
                'lambda': 0.35,
                'density': 950,
                'cp': 2100,
                'type': 'insulation',
                'color': '#A0522D'
            },
            'PVC': {
                'lambda': 0.2,
                'density': 1400,
                'cp': 1200,
                'type': 'insulation',
                'color': '#696969'
            },
            'PE': {
                'lambda': 0.4,
                'density': 920,
                'cp': 2200,
                'type': 'insulation',
                'color': '#2F4F4F'
            },

            # Mantel und Schutz
            'PE-Mantel': {
                'lambda': 0.4,
                'density': 920,
                'cp': 2200,
                'type': 'sheath',
                'color': '#2F4F4F'
            },
            'PVC-Mantel': {
                'lambda': 0.2,
                'density': 1400,
                'cp': 1200,
                'type': 'sheath',
                'color': '#708090'
            },
            'Bleimantel': {
                'lambda': 35,
                'density': 11340,
                'cp': 129,
                'type': 'sheath',
                'color': '#778899'
            },
            'PE-Rohr': {
                'lambda': 0.4,
                'density': 920,
                'cp': 2200,
                'type': 'protection',
                'color': '#4169E1'
            },
            'PVC-Rohr': {
                'lambda': 0.2,
                'density': 1400,
                'cp': 1200,
                'type': 'protection',
                'color': '#191970'
            },
            'Stahlrohr': {
                'lambda': 50,
                'density': 7850,
                'cp': 490,
                'type': 'protection',
                'color': '#2F4F4F'
            },

            # Bettung und Verlegung
            'Sand trocken': {
                'lambda': 0.35,
                'density': 1600,
                'cp': 800,
                'type': 'bedding',
                'color': '#F4A460'
            },
            'Sand feucht': {
                'lambda': 2.0,
                'density': 1800,
                'cp': 1200,
                'type': 'bedding',
                'color': '#DAA520'
            },
            'Kies': {
                'lambda': 0.5,
                'density': 1800,
                'cp': 850,
                'type': 'bedding',
                'color': '#B8860B'
            },
            'Beton normal': {
                'lambda': 1.4,
                'density': 2400,
                'cp': 880,
                'type': 'bedding',
                'color': '#696969'
            },
            'Magerbeton': {
                'lambda': 1.2,
                'density': 2200,
                'cp': 880,
                'type': 'bedding',
                'color': '#808080'
            },

            # Erdreich
            'Erdreich trocken': {
                'lambda': 0.5,
                'density': 1600,
                'cp': 800,
                'type': 'soil',
                'color': '#8B4513'
            },
            'Erdreich normal': {
                'lambda': 1.2,
                'density': 1800,
                'cp': 1000,
                'type': 'soil',
                'color': '#A0522D'
            },
            'Erdreich feucht': {
                'lambda': 2.0,
                'density': 2000,
                'cp': 1200,
                'type': 'soil',
                'color': '#D2691E'
            },
            'Lehm': {
                'lambda': 1.5,
                'density': 2000,
                'cp': 1000,
                'type': 'soil',
                'color': '#CD853F'
            },
            'Ton': {
                'lambda': 1.3,
                'density': 1900,
                'cp': 950,
                'type': 'soil',
                'color': '#DEB887'
            },

            # Spezial
            'Luft': {
                'lambda': 0.026,
                'density': 1.2,
                'cp': 1005,
                'type': 'air',
                'color': '#E6E6FA'
            },
            'Wasser': {
                'lambda': 0.6,
                'density': 1000,
                'cp': 4180,
                'type': 'water',
                'color': '#4682B4'
            },
        }

    def get_materials_by_type(self, material_type):
        return [name for name, props in self.materials.items() if props['type'] == material_type]

    def get_material_properties(self, material_name):
        return self.materials.get(material_name, {})


class CableLayer:
    """Kabelschicht mit vollständigen Eigenschaften"""

    def __init__(self, name, material, inner_radius_mm, thickness_mm):
        self.name = name
        self.material = material
        self.inner_radius_mm = inner_radius_mm
        self.thickness_mm = thickness_mm
        self.outer_radius_mm = inner_radius_mm + thickness_mm

        db = MaterialDatabase()
        props = db.get_material_properties(material)
        self.thermal_conductivity = props.get('lambda', 1.0)
        self.density = props.get('density', 1000)
        self.specific_heat = props.get('cp', 1000)
        self.material_type = props.get('type', 'unknown')
        self.color = props.get('color', '#CCCCCC')


class ARCADISSimpleThermalGUI:
    """ARCADIS Professional Thermal Calculator - Vereinfachte, professionelle Version"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("ARCADIS Professional HGÜ Thermal Calculator v2.2")
        self.window.geometry("1600x980")
        self.window.configure(bg=ARCADIS_WHITE)

        self.cable_layers = []
        self.calculation_results = None
        self.material_db = MaterialDatabase()
        self.trace_log = []

        self.create_interface()
        self.load_demo_configuration()
        print("ARCADIS Professional HGÜ Thermal Calculator gestartet")

    # ------------------------------------------------------------------
    # Oberflächenaufbau
    # ------------------------------------------------------------------
    def create_interface(self):
        self.create_header()
        self.create_main_area()
        self.create_statusbar()

    def create_header(self):
        header = tk.Frame(self.window, bg=ARCADIS_BLUE, height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg=ARCADIS_BLUE)
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)

        tk.Label(
            title_frame,
            text="ARCADIS",
            font=('Arial', 18, 'bold'),
            fg=ARCADIS_ORANGE,
            bg=ARCADIS_BLUE
        ).pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text=" | Professional HGÜ Thermal Calculator",
            font=('Arial', 14),
            fg='white',
            bg=ARCADIS_BLUE
        ).pack(side=tk.LEFT)

        info_frame = tk.Frame(header, bg=ARCADIS_BLUE)
        info_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        tk.Label(
            info_frame,
            text="Version 2.2 Professional",
            font=('Arial', 10),
            fg='white',
            bg=ARCADIS_BLUE
        ).pack(anchor=tk.E)

        tk.Label(
            info_frame,
            text="IEC 60287-1-1 & IEC 60287-2-1",
            font=('Arial', 9),
            fg=ARCADIS_ORANGE,
            bg=ARCADIS_BLUE
        ).pack(anchor=tk.E)

        tk.Label(
            info_frame,
            text=datetime.now().strftime('%d.%m.%Y %H:%M'),
            font=('Arial', 8),
            fg='white',
            bg=ARCADIS_BLUE
        ).pack(anchor=tk.E)

    def create_main_area(self):
        main_frame = tk.Frame(self.window, bg=ARCADIS_WHITE)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        paned = tk.PanedWindow(
            main_frame,
            orient=tk.HORIZONTAL,
            bg=ARCADIS_WHITE,
            sashwidth=6,
            sashrelief=tk.RAISED
        )
        paned.pack(fill=tk.BOTH, expand=True)

        config_panel = self.create_config_panel(paned)
        paned.add(config_panel, width=620)

        viz_panel = self.create_visualization_panel(paned)
        paned.add(viz_panel, width=960)

    def create_config_panel(self, parent):
        frame = tk.Frame(parent, bg=ARCADIS_WHITE, relief=tk.RIDGE, bd=1)

        header = tk.Frame(frame, bg=ARCADIS_LIGHT_BLUE, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="⚙ KABELKONFIGURATION",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg=ARCADIS_LIGHT_BLUE
        ).pack(pady=10)

        canvas = tk.Canvas(frame, bg=ARCADIS_WHITE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=ARCADIS_WHITE)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.create_basic_parameters(scrollable)
        self.create_layer_management(scrollable)
        self.create_calculation_controls(scrollable)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return frame

    def create_basic_parameters(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Kabelparameter",
            font=('Arial', 11, 'bold'),
            fg=ARCADIS_BLUE,
            bg=ARCADIS_WHITE,
            relief=tk.GROOVE,
            bd=2
        )
        frame.pack(fill=tk.X, padx=10, pady=10)

        params = [
            ("Nennspannung [kV]:", "voltage", "20.0"),
            ("Betriebsstrom [A]:", "current", "300.0"),
            ("Leiterdurchmesser [mm]:", "conductor_diameter", "16.0"),
            ("Max. Leitertemperatur [°C]:", "max_temp", "90.0"),
            ("Umgebungstemperatur [°C]:", "ambient_temp", "15.0"),
            ("Verlegetiefe [m]:", "burial_depth", "1.2"),
        ]

        self.param_vars = {}

        for row, (label, key, default) in enumerate(params):
            tk.Label(
                frame,
                text=label,
                font=('Arial', 9),
                fg=ARCADIS_BLUE,
                bg=ARCADIS_WHITE
            ).grid(row=row, column=0, sticky=tk.W, pady=5, padx=10)

            var = tk.StringVar(value=default)
            entry = tk.Entry(
                frame,
                textvariable=var,
                width=18,
                font=('Arial', 9),
                relief=tk.SUNKEN,
                bd=1
            )
            entry.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
            self.param_vars[key] = var

        tk.Label(
            frame,
            text="Leitermaterial:",
            font=('Arial', 9),
            fg=ARCADIS_BLUE,
            bg=ARCADIS_WHITE
        ).grid(row=len(params), column=0, sticky=tk.W, pady=5, padx=10)

        self.conductor_var = tk.StringVar(value="Kupfer (Cu)")
        conductor_combo = ttk.Combobox(
            frame,
            textvariable=self.conductor_var,
            values=self.material_db.get_materials_by_type('conductor'),
            width=15,
            font=('Arial', 9)
        )
        conductor_combo.configure(state='readonly')
        conductor_combo.grid(row=len(params), column=1, sticky=tk.W, padx=10, pady=5)
        self.param_vars['conductor_type'] = self.conductor_var

        tk.Label(
            frame,
            text="Systemtyp:",
            font=('Arial', 9),
            fg=ARCADIS_BLUE,
            bg=ARCADIS_WHITE
        ).grid(row=len(params)+1, column=0, sticky=tk.W, pady=5, padx=10)

        system_frame = tk.Frame(frame, bg=ARCADIS_WHITE)
        system_frame.grid(row=len(params)+1, column=1, sticky=tk.W, padx=10, pady=5)

        self.system_type = tk.StringVar(value="AC")
        tk.Radiobutton(
            system_frame,
            text="AC",
            variable=self.system_type,
            value="AC",
            font=('Arial', 9),
            fg=ARCADIS_BLUE,
            bg=ARCADIS_WHITE
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            system_frame,
            text="DC",
            variable=self.system_type,
            value="DC",
            font=('Arial', 9),
            fg=ARCADIS_BLUE,
            bg=ARCADIS_WHITE
        ).pack(side=tk.LEFT, padx=10)

        self.param_vars['system_type'] = self.system_type

    def create_layer_management(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Schichtaufbau",
            font=('Arial', 11, 'bold'),
            fg=ARCADIS_BLUE,
            bg=ARCADIS_WHITE,
            relief=tk.GROOVE,
            bd=2
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar = tk.Frame(frame, bg=ARCADIS_WHITE)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        button_specs = [
            ("+ Isolation", 'insulation'),
            ("+ Mantel", 'sheath'),
            ("+ Schutz", 'protection'),
            ("+ Bettung", 'bedding'),
            ("+ Erdreich", 'soil'),
        ]

        for idx, (title, layer_type) in enumerate(button_specs):
            tk.Button(
                toolbar,
                text=title,
                command=lambda lt=layer_type: self.add_layer_simple(lt),
                bg=ARCADIS_ORANGE,
                fg='white',
                font=('Arial', 8, 'bold'),
                relief=tk.RAISED,
                bd=1,
                padx=6,
                pady=2
            ).grid(row=0, column=idx, padx=2, pady=2, sticky=tk.W)

        mgmt_frame = tk.Frame(toolbar, bg=ARCADIS_WHITE)
        mgmt_frame.grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=5)

        tk.Button(
            mgmt_frame,
            text="Letzte entfernen",
            command=self.remove_last_layer,
            bg=ARCADIS_BLUE,
            fg='white',
            font=('Arial', 8),
            relief=tk.RAISED,
            bd=1,
            padx=6,
            pady=2
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            mgmt_frame,
            text="Alle löschen",
            command=self.clear_layers,
            bg=ARCADIS_GREY,
            fg='white',
            font=('Arial', 8),
            relief=tk.RAISED,
            bd=1,
            padx=6,
            pady=2
        ).pack(side=tk.LEFT, padx=2)

        list_frame = tk.Frame(frame, bg=ARCADIS_WHITE)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.layer_listbox = tk.Listbox(
            list_frame,
            font=('Consolas', 9),
            height=12,
            bg='white',
            fg=ARCADIS_BLUE,
            selectbackground=ARCADIS_LIGHT_BLUE
        )
        self.layer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.layer_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.layer_listbox.configure(yscrollcommand=scrollbar.set)

    def create_calculation_controls(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Berechnung",
            font=('Arial', 11, 'bold'),
            fg=ARCADIS_BLUE,
            bg=ARCADIS_WHITE,
            relief=tk.GROOVE,
            bd=2
        )
        frame.pack(fill=tk.X, padx=10, pady=10)

        self.calc_options = {}
        options = [
            ("AC-Verluste berücksichtigen", "ac_losses", True),
            ("Dielektrische Verluste", "dielectric_losses", True),
            ("Mantelverluste", "sheath_losses", True),
        ]

        for idx, (label, key, default) in enumerate(options):
            var = tk.BooleanVar(value=default)
            tk.Checkbutton(
                frame,
                text=label,
                variable=var,
                font=('Arial', 9),
                fg=ARCADIS_BLUE,
                bg=ARCADIS_WHITE
            ).grid(row=idx // 2, column=idx % 2, sticky=tk.W, padx=10, pady=3)
            self.calc_options[key] = var

        calc_button = tk.Button(
            frame,
            text="THERMISCHE ANALYSE STARTEN",
            command=self.perform_calculation,
            bg=ARCADIS_ORANGE,
            fg='white',
            font=('Arial', 11, 'bold'),
            relief=tk.RAISED,
            bd=3,
            pady=8
        )
        calc_button.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=15)

        # NEUER BUTTON: Vollständiger Rechenweg
        rechenweg_button = tk.Button(
            frame,
            text="VOLLSTAENDIGER RECHENWEG MIT FORMELN",
            command=self.show_complete_calculation_path,
            bg=ARCADIS_BLUE,
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            bd=2,
            pady=6
        )
        rechenweg_button.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=(0, 15))

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def create_visualization_panel(self, parent):
        frame = tk.Frame(parent, bg=ARCADIS_WHITE, relief=tk.RIDGE, bd=1)

        header = tk.Frame(frame, bg=ARCADIS_LIGHT_BLUE, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="VISUALISIERUNG & ERGEBNISSE",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg=ARCADIS_LIGHT_BLUE
        ).pack(pady=10)

        self.notebook = ttk.Notebook(frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_schematic_tab()
        self.create_temperature_tab()
        self.create_results_tab()

        return frame

    def create_schematic_tab(self):
        tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab, text='Kabelschema')

        self.schema_fig, self.schema_ax = plt.subplots(figsize=(8, 6))
        self.schema_fig.patch.set_facecolor('white')
        self.schema_canvas = FigureCanvasTkAgg(self.schema_fig, tab)
        self.schema_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Button(
            tab,
            text="Schema aktualisieren",
            command=self.update_schematic,
            bg=ARCADIS_ORANGE,
            fg='white',
            font=('Arial', 9, 'bold')
        ).pack(pady=5)

    def create_temperature_tab(self):
        tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab, text='Temperaturprofil')

        self.temp_fig, self.temp_ax = plt.subplots(figsize=(8, 6))
        self.temp_fig.patch.set_facecolor('white')
        self.temp_canvas = FigureCanvasTkAgg(self.temp_fig, tab)
        self.temp_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_results_tab(self):
        tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab, text='Ergebnisse')

        text_frame = tk.Frame(tab, bg='white')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.results_text = tk.Text(
            text_frame,
            font=('Consolas', 9),
            wrap=tk.WORD,
            bg='white',
            fg=ARCADIS_BLUE
        )
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)

    def create_statusbar(self):
        bar = tk.Frame(self.window, bg=ARCADIS_BLUE, height=26)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self.status_label = tk.Label(
            bar,
            text="ARCADIS Professional - Bereit",
            bg=ARCADIS_BLUE,
            fg='white',
            font=('Arial', 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)

        tk.Label(
            bar,
            text="© ARCADIS 2025",
            bg=ARCADIS_BLUE,
            fg=ARCADIS_ORANGE,
            font=('Arial', 9)
        ).pack(side=tk.RIGHT, padx=10, pady=2)

    # ------------------------------------------------------------------
    # Schichtverwaltung
    # ------------------------------------------------------------------
    def add_layer_simple(self, layer_type):
        defaults = {
            'insulation': ('XLPE', 8.0),
            'sheath': ('PE-Mantel', 2.5),
            'protection': ('PE-Rohr', 3.0),
            'bedding': ('Sand feucht', 100.0),
            'soil': ('Erdreich normal', 500.0)
        }

        if layer_type not in defaults:
            return

        material, thickness = defaults[layer_type]
        name = f"{layer_type.title()}-Schicht"

        inner_radius = self.cable_layers[-1].outer_radius_mm if self.cable_layers else float(self.param_vars['conductor_diameter'].get()) / 2

        layer = CableLayer(name, material, inner_radius, thickness)
        self.cable_layers.append(layer)

        self.update_layer_display()
        self.update_schematic()
        self.update_status(f"Schicht '{name}' hinzugefügt")

    def remove_last_layer(self):
        if self.cable_layers:
            removed = self.cable_layers.pop()
            self.recalculate_radii()
            self.update_layer_display()
            self.update_schematic()
            self.update_status(f"Schicht '{removed.name}' entfernt")

    def clear_layers(self):
        if self.cable_layers and messagebox.askyesno("ARCADIS", "Alle Schichten entfernen?"):
            self.cable_layers.clear()
            self.update_layer_display()
            self.update_schematic()
            self.update_status("Alle Schichten entfernt")

    def recalculate_radii(self):
        if not self.cable_layers:
            return

        current_radius = float(self.param_vars['conductor_diameter'].get()) / 2
        for layer in self.cable_layers:
            layer.inner_radius_mm = current_radius
            layer.outer_radius_mm = current_radius + layer.thickness_mm
            current_radius = layer.outer_radius_mm

    def update_layer_display(self):
        self.layer_listbox.delete(0, tk.END)
        for idx, layer in enumerate(self.cable_layers, 1):
            entry = (
                f"{idx:2d}: {layer.name:<18} | {layer.material:<16} | "
                f"{layer.thickness_mm:6.1f} mm | λ={layer.thermal_conductivity:6.3f}"
            )
            self.layer_listbox.insert(tk.END, entry)

    # ------------------------------------------------------------------
    # Visualisierung
    # ------------------------------------------------------------------
    def update_schematic(self):
        self.schema_ax.clear()

        if not self.cable_layers:
            self.schema_ax.text(
                0.5,
                0.5,
                'Keine Schichten konfiguriert\nBitte Schichten hinzufügen',
                ha='center',
                va='center',
                transform=self.schema_ax.transAxes,
                fontsize=12,
                color=ARCADIS_GREY
            )
            self.schema_canvas.draw()
            return

        conductor_radius = float(self.param_vars['conductor_diameter'].get()) / 2
        self.schema_ax.add_patch(
            Circle((0, 0), conductor_radius, color='#CD7F32', alpha=0.9, label='Leiter')
        )

        for layer in self.cable_layers:
            self.schema_ax.add_patch(
                Circle(
                    (0, 0),
                    layer.outer_radius_mm,
                    color=layer.color,
                    alpha=0.6,
                    fill=False,
                    linewidth=max(layer.thickness_mm / 2, 1),
                    label=layer.name
                )
            )

        max_radius = self.cable_layers[-1].outer_radius_mm
        margin = max_radius * 0.2
        self.schema_ax.set_xlim(-max_radius - margin, max_radius + margin)
        self.schema_ax.set_ylim(-max_radius - margin, max_radius + margin)
        self.schema_ax.set_aspect('equal')
        self.schema_ax.set_title(
            'ARCADIS Kabelquerschnitt',
            fontweight='bold',
            fontsize=12,
            color=ARCADIS_BLUE
        )
        self.schema_ax.grid(True, alpha=0.3)

        if len(self.cable_layers) <= 6:
            self.schema_ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1))

        self.schema_canvas.draw()

    # ------------------------------------------------------------------
    # Berechnung
    # ------------------------------------------------------------------
    def perform_calculation(self):
        try:
            if not self.cable_layers:
                messagebox.showwarning("ARCADIS", "Bitte mindestens eine Schicht konfigurieren!")
                return

            self.update_status("Berechnung läuft...")
            results = self.calculate_thermal()
            self.display_results(results)
            self.plot_temperature_profile(results)
            self.update_status("Berechnung erfolgreich abgeschlossen")
        except Exception as exc:
            self.update_status("Berechnungsfehler")
            messagebox.showerror("ARCADIS - Fehler", f"Berechnungsfehler:\n{exc}")

    def show_complete_calculation_path(self):
        """
        Zeigt vollständigen Rechenweg mit Formeln, Gegeben-Werten und Annahmen
        in einem separaten Fenster
        """
        if not self.calculation_results:
            messagebox.showinfo(
                "ARCADIS",
                "Bitte zuerst eine Berechnung durchfuehren!\n\n"
                "Klicken Sie auf 'THERMISCHE ANALYSE' um die Berechnung zu starten."
            )
            return

        # Neues Fenster erstellen
        calc_window = tk.Toplevel(self.window)
        calc_window.title("ARCADIS - Vollständiger Rechenweg mit Formeln")
        calc_window.geometry("1200x900")
        calc_window.configure(bg=ARCADIS_WHITE)

        # Header
        header = tk.Frame(calc_window, bg=ARCADIS_BLUE, height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="VOLLSTAENDIGER RECHENWEG",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg=ARCADIS_BLUE
        ).pack(side=tk.LEFT, padx=20, pady=15)

        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        tk.Label(
            header,
            text=f"Erstellt: {timestamp}",
            font=('Arial', 9),
            fg='white',
            bg=ARCADIS_BLUE
        ).pack(side=tk.RIGHT, padx=20, pady=15)

        # Scrollbarer Hauptbereich
        main_frame = tk.Frame(calc_window, bg=ARCADIS_WHITE)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(main_frame, bg=ARCADIS_WHITE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=ARCADIS_WHITE)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Inhalt generieren
        self._generate_calculation_report(scrollable_frame)

        # Footer mit Buttons
        footer = tk.Frame(calc_window, bg=ARCADIS_LIGHT_GREY, height=50)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Button(
            footer,
            text="Speichern als TXT",
            command=lambda: self._save_calculation_report_txt(),
            bg=ARCADIS_BLUE,
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=10, pady=10)

        tk.Button(
            footer,
            text="Als PDF exportieren",
            command=lambda: self._export_calculation_to_pdf(),
            bg=ARCADIS_ORANGE,
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5, pady=10)

        tk.Button(
            footer,
            text="Schliessen",
            command=calc_window.destroy,
            bg=ARCADIS_GREY,
            fg='white',
            font=('Arial', 10),
            padx=20,
            pady=5
        ).pack(side=tk.RIGHT, padx=10, pady=10)

    def _generate_calculation_report(self, parent):
        """Generiert den vollständigen MCP-validierten Berechnungsbericht"""
        results = self.calculation_results
        
        # DEBUG: Prüfe welche Daten verfügbar sind
        print("\n=== DEBUG: calculation_results keys ===")
        if results:
            print(f"Keys: {results.keys()}")
            if 'conductor_details' in results:
                print(f"conductor_details keys: {results['conductor_details'].keys()}")
        else:
            print("ERROR: results ist None!")
        
        # MCP-VALIDIERUNG: Nur wenn alle Daten vorhanden
        mcp_report = None
        if results and 'conductor_details' in results:
            # Prüfe ob alle notwendigen Schlüssel vorhanden sind
            required_keys = ['rho20', 'alpha', 'area', 'rho_temp', 'r_dc', 'resistance']
            conductor_details = results['conductor_details']
            missing_keys = [k for k in required_keys if k not in conductor_details]
            
            if missing_keys:
                print(f"WARNING: Fehlende conductor_details: {missing_keys}")
                # Ergänze fehlende Werte
                if 'rho20' not in conductor_details:
                    # Bestimme aus Leitertyp
                    if 'Cu' in self.conductor_var.get():
                        conductor_details['rho20'] = 1.72e-8
                        conductor_details['alpha'] = 0.00393
                    else:  # Aluminium
                        conductor_details['rho20'] = 2.65e-8
                        conductor_details['alpha'] = 0.00403
                
                if 'area' not in conductor_details:
                    diameter_mm = float(self.param_vars['conductor_diameter'].get())
                    conductor_details['area'] = 3.14159 * (diameter_mm / 2000.0) ** 2
                
                if 'rho_temp' not in conductor_details:
                    conductor_details['rho_temp'] = conductor_details['rho20'] * \
                        (1 + conductor_details['alpha'] * (results['max_temp'] - 20))
                
                if 'r_dc' not in conductor_details:
                    conductor_details['r_dc'] = conductor_details['rho_temp'] / conductor_details['area']
                
                if 'resistance' not in conductor_details:
                    conductor_details['resistance'] = conductor_details['r_dc']
            
            try:
                mcp_report = generate_complete_calculation_report_with_mcp(
                    calculation_results=results,
                    cable_layers=self.cable_layers,
                    param_vars=self.param_vars,
                    calc_options=self.calc_options,
                    conductor_type=self.conductor_var.get()
                )
                print("✓ MCP-Report erfolgreich generiert")
            except Exception as e:
                print(f"✗ MCP-Fehler: {str(e)}")
                import traceback
                traceback.print_exc()
                mcp_report = None

        # GEGEBEN: Eingabeparameter
        self._add_section_header(parent, "1. GEGEBEN: Eingabeparameter")
        
        gegeben_data = [
            ("Systemtyp", results['system_type'], ""),
            ("Nennspannung", f"{results['voltage']:.0f}", "kV"),
            ("Betriebsstrom", f"{results['current']:.2f}", "A"),
            ("Leiterdurchmesser", f"{float(self.param_vars['conductor_diameter'].get()):.2f}", "mm"),
            ("Max. zulässige Leitertemperatur", f"{results['max_temp']:.1f}", "°C"),
            ("Umgebungstemperatur", f"{results['ambient_temp']:.1f}", "°C"),
            ("Verlegetiefe", f"{results['burial_depth']:.2f}", "m"),
            ("Leitertyp", self.conductor_var.get(), ""),
            ("Anzahl Kabelschichten", str(len(self.cable_layers)), "")
        ]

        self._add_data_table(parent, gegeben_data)

        # ANNAHMEN
        self._add_section_header(parent, "2. ANNAHMEN")
        
        # Erdreich-Wärmeleitfähigkeit aus letzter Schicht extrahieren
        soil_lambda = 1.0  # Standardwert
        if self.cable_layers:
            # Letzte Schicht ist meist Erdreich
            last_layer = self.cable_layers[-1]
            if 'Erdreich' in last_layer.name or 'Soil' in last_layer.name or 'Boden' in last_layer.name:
                soil_lambda = last_layer.thermal_conductivity
        
        annahmen_text = f"""
NORMATIVE GRUNDLAGEN:
• Berechnung nach IEC 60287-1-1:2023 (Elektrische Kabel - Belastbarkeit)
• Thermische Widerstände nach IEC 60287-2-1:2023
• Materialeigenschaften nach DIN EN 12524:2000-07 und VDI-Wärmeatlas
• Erdreichparameter nach VDI 4640 Blatt 1

BETRIEBSBEDINGUNGEN:
• Stationärer Betriebszustand (keine transienten Effekte berücksichtigt)
• Konstante Umgebungstemperatur θ_a = {results['ambient_temp']:.1f} °C
• Verlegetiefe {results['burial_depth']:.2f} m unter Geländeoberkante
• {'Drehstrom (AC, 50 Hz)' if results['system_type'] == 'AC' else 'Gleichstrom (DC)'}

MATERIALEIGENSCHAFTEN:
• Leiter: {self.conductor_var.get()}
  - Spezifischer Widerstand ρ₂₀ = {results['conductor_details']['rho20']:.3e} Ω·m bei 20°C
  - Temperaturkoeffizient α = {results['conductor_details']['alpha']:.5f} /K
  - Wärmeleitfähigkeit λ_leiter = {self.cable_layers[0].thermal_conductivity if self.cable_layers else 'N/A'} W/(m·K)
  
• Isolation: {self.cable_layers[1].material if len(self.cable_layers) > 1 else 'N/A'}
  - Wärmeleitfähigkeit λ_iso = {self.cable_layers[1].thermal_conductivity if len(self.cable_layers) > 1 else 'N/A'} W/(m·K)
  - Max. zulässige Temperatur: {results['max_temp']:.1f} °C
  
• Erdreich:
  - Wärmeleitfähigkeit λ_soil = {soil_lambda:.2f} W/(m·K)
  - Homogen angenommen (keine Schichtung)

VERLUSTMECHANISMEN:
• Leiterverluste: {'AC-Verluste mit Skin-/Proximity-Effekt (k_skin=1.08, k_prox=1.05)' if results['system_type'] == 'AC' and self.calc_options.get('ac_losses', tk.BooleanVar(value=False)).get() else 'Gleichstromverluste (R_DC)'}
• Dielektrische Verluste: {'Berücksichtigt (vereinfachtes Modell)' if self.calc_options.get('dielectric_losses', tk.BooleanVar(value=False)).get() else 'Vernachlässigt'}
• Mantelverluste: {'Berücksichtigt (Wirbelströme, vereinfachtes Modell)' if self.calc_options.get('sheath_losses', tk.BooleanVar(value=False)).get() else 'Vernachlässigt'}

GEOMETRIE:
• Leiterdurchmesser: {float(self.param_vars['conductor_diameter'].get()):.2f} mm
• Anzahl Kabelschichten: {len(self.cable_layers)}
• Gesamtaußendurchmesser: {self.cable_layers[-1].outer_radius_mm * 2:.2f} mm ({self.cable_layers[-1].outer_radius_mm * 2 / 1000:.3f} m)

VEREINFACHUNGEN:
• Keine gegenseitige Erwärmung benachbarter Kabel
• Keine solaren/atmosphärischen Einflüsse
• Keine Bodentrocknungs-Effekte (λ_soil = konstant)
• Keine Alterungseffekte der Isolation
"""
        self._add_text_box(parent, annahmen_text)

        # RECHENWEG: Elektrische Verluste
        self._add_section_header(parent, "3. RECHENWEG: Elektrische Verluste")
        
        # 3.1 Leiterverluste
        self._add_subsection_header(parent, "3.1 Leiterverluste")
        self._add_formula_block(parent,
            title="Leiterquerschnitt",
            formula="A = π · (d/2)²",
            variables=[
                ("d", f"{float(self.param_vars['conductor_diameter'].get()):.2f} mm", "Leiterdurchmesser")
            ],
            calculation=f"A = π · ({float(self.param_vars['conductor_diameter'].get()):.2f}/2)² = {results['conductor_details']['area']:.6e} m²",
            result=f"A = {results['conductor_details']['area']:.6e} m²"
        )

        self._add_formula_block(parent,
            title="Temperaturabhängiger Widerstand",
            formula="ρ(θ) = ρ₂₀ · [1 + α · (θ - 20°C)]",
            variables=[
                ("ρ₂₀", f"{results['conductor_details']['rho20']:.3e} Ω·m", "Spez. Widerstand bei 20°C"),
                ("α", f"{results['conductor_details']['alpha']:.5f} /K", "Temperaturkoeffizient"),
                ("θ", f"{results['max_temp']:.1f} °C", "Leitertemperatur")
            ],
            calculation=f"ρ({results['max_temp']:.1f}°C) = {results['conductor_details']['rho20']:.3e} · [1 + {results['conductor_details']['alpha']:.5f} · ({results['max_temp']:.1f} - 20)]",
            result=f"ρ(θ) = {results['conductor_details']['rho_temp']:.3e} Ω·m"
        )

        self._add_formula_block(parent,
            title="Leiterwiderstand (DC)",
            formula="R_DC = ρ(θ) / A",
            variables=[
                ("ρ(θ)", f"{results['conductor_details']['rho_temp']:.3e} Ω·m", "Spez. Widerstand"),
                ("A", f"{results['conductor_details']['area']:.6e} m²", "Querschnittsfläche")
            ],
            calculation=f"R_DC = {results['conductor_details']['rho_temp']:.3e} / {results['conductor_details']['area']:.6e}",
            result=f"R_DC = {results['conductor_details']['r_dc']:.6f} Ω/m"
        )

        if results['system_type'] == 'AC' and self.calc_options['ac_losses'].get():
            self._add_formula_block(parent,
                title="AC-Korrektur (Skin-/Proximity-Effekt)",
                formula="R_AC = R_DC · k_skin · k_prox",
                variables=[
                    ("k_skin", "1.08", "Skin-Effekt-Faktor"),
                    ("k_prox", "1.05", "Proximity-Effekt-Faktor")
                ],
                calculation=f"R_AC = {results['conductor_details']['r_dc']:.6f} · 1.08 · 1.05",
                result=f"R_AC = {results['conductor_details']['resistance']:.6f} Ω/m"
            )

        self._add_formula_block(parent,
            title="Leiterverluste",
            formula="P_Leiter = I² · R",
            variables=[
                ("I", f"{results['current']:.2f} A", "Betriebsstrom"),
                ("R", f"{results['conductor_details']['resistance']:.6f} Ω/m", "Leiterwiderstand")
            ],
            calculation=f"P_Leiter = {results['current']:.2f}² · {results['conductor_details']['resistance']:.6f}",
            result=f"P_Leiter = {results['conductor_losses']:.4f} W/m"
        )

        # 3.2 Dielektrische Verluste
        if self.calc_options['dielectric_losses'].get() and results['system_type'] == 'AC':
            self._add_subsection_header(parent, "3.2 Dielektrische Verluste")
            self._add_formula_block(parent,
                title="Dielektrische Verluste (vereinfacht)",
                formula="P_diel ≈ k · U²",
                variables=[
                    ("k", "1.0e-7", "Vereinfachter Faktor"),
                    ("U", f"{results['voltage']:.0f} kV", "Spannung")
                ],
                calculation=f"P_diel = 1.0e-7 · {results['voltage']:.0f}²",
                result=f"P_diel = {results['dielectric_losses']:.4f} W/m"
            )

        # 3.3 Mantelverluste
        if self.calc_options['sheath_losses'].get():
            self._add_subsection_header(parent, "3.3 Mantelverluste (Wirbelströme)")
            self._add_formula_block(parent,
                title="Mantelverluste (vereinfacht)",
                formula="P_Mantel ≈ k · I²",
                variables=[
                    ("k", "0.0001", "Vereinfachter Faktor"),
                    ("I", f"{results['current']:.2f} A", "Betriebsstrom")
                ],
                calculation=f"P_Mantel = 0.0001 · {results['current']:.2f}²",
                result=f"P_Mantel = {results['sheath_losses']:.4f} W/m"
            )

        # 3.4 Gesamtverluste
        self._add_subsection_header(parent, "3.4 Gesamtverluste")
        self._add_formula_block(parent,
            title="Summe aller Verluste",
            formula="P_total = P_Leiter + P_diel + P_Mantel",
            variables=[
                ("P_Leiter", f"{results['conductor_losses']:.4f} W/m", "Leiterverluste"),
                ("P_diel", f"{results['dielectric_losses']:.4f} W/m", "Dielektr. Verluste"),
                ("P_Mantel", f"{results['sheath_losses']:.4f} W/m", "Mantelverluste")
            ],
            calculation=f"P_total = {results['conductor_losses']:.4f} + {results['dielectric_losses']:.4f} + {results['sheath_losses']:.4f}",
            result=f"P_total = {results['total_losses']:.4f} W/m"
        )

        # RECHENWEG: Thermische Widerstände
        self._add_section_header(parent, "4. RECHENWEG: Thermische Widerstände")

        self._add_text_box(parent, """
Für zylindrische Geometrie (Kabel) gilt die IEC 60287-1-1 Formel:

    R_th = ln(r_o/r_i) / (2π · λ)  [K·m/W]

wobei:
• r_o = Außenradius [m]
• r_i = Innenradius [m]
• λ = Wärmeleitfähigkeit [W/(m·K)]

WICHTIG: ln(r_o/r_i) ergibt sich aus der Integration über 1/r (zylindrische Geometrie)!
         Dies ist NICHT dasselbe wie die planare Formel R = d/(λ·A)!
""")

        for i, layer in enumerate(self.cable_layers):
            details = results['thermal_resistance_details'][i]
            self._add_formula_block(parent,
                title=f"Schicht {i+1}: {layer.name} ({layer.material})",
                formula="R_th = ln(r_o/r_i) / (2π · λ)",
                variables=[
                    ("r_i", f"{layer.inner_radius_mm:.2f} mm", "Innenradius"),
                    ("r_o", f"{layer.outer_radius_mm:.2f} mm", "Außenradius"),
                    ("λ", f"{layer.thermal_conductivity:.3f} W/(m·K)", "Wärmeleitfähigkeit")
                ],
                calculation=f"R_th = ln({layer.outer_radius_mm:.2f}/{layer.inner_radius_mm:.2f}) / (2π · {layer.thermal_conductivity:.3f})",
                result=f"R_th = {details.get('R_th', details.get('rth', 0)):.6f} K·m/W"
            )

        self._add_formula_block(parent,
            title="Gesamter thermischer Widerstand",
            formula="ΣR_th = Σ R_th,i",
            variables=[
                (f"R_th,{i+1}", f"{r:.6f} K·m/W", f"{self.cable_layers[i].name}")
                for i, r in enumerate(results['thermal_resistances'])
            ],
            calculation=" + ".join([f"{r:.6f}" for r in results['thermal_resistances']]),
            result=f"ΣR_th = {results['total_thermal_resistance']:.6f} K·m/W"
        )

        # ERGEBNIS: Leitertemperatur
        self._add_section_header(parent, "5. ERGEBNIS: Leitertemperatur")

        self._add_formula_block(parent,
            title="Temperaturerhöhung",
            formula="Δθ = P_total · ΣR_th",
            variables=[
                ("P_total", f"{results['total_losses']:.4f} W/m", "Gesamtverluste"),
                ("ΣR_th", f"{results['total_thermal_resistance']:.6f} K·m/W", "Therm. Widerstand")
            ],
            calculation=f"Δθ = {results['total_losses']:.4f} · {results['total_thermal_resistance']:.6f}",
            result=f"Δθ = {results['temperature_rise']:.2f} K"
        )

        self._add_formula_block(parent,
            title="Leitertemperatur",
            formula="θ_Leiter = θ_Umgebung + Δθ",
            variables=[
                ("θ_Umgebung", f"{results['ambient_temp']:.1f} °C", "Umgebungstemperatur"),
                ("Δθ", f"{results['temperature_rise']:.2f} K", "Temperaturerhöhung")
            ],
            calculation=f"θ_Leiter = {results['ambient_temp']:.1f} + {results['temperature_rise']:.2f}",
            result=f"θ_Leiter = {results['conductor_temp']:.2f} °C"
        )

        # BEWERTUNG
        self._add_section_header(parent, "6. BEWERTUNG")

        margin = results['safety_margin']
        margin_percent = (margin / results['max_temp']) * 100

        bewertung_text = f"""
✓ Berechnete Leitertemperatur: {results['conductor_temp']:.2f} °C
✓ Maximal zulässige Temperatur: {results['max_temp']:.1f} °C
✓ Sicherheitsmarge: {margin:.2f} K ({margin_percent:.1f}%)

"""
        if margin > 10:
            bewertung_text += "SEHR GUT: Große Sicherheitsmarge vorhanden!"
        elif margin > 5:
            bewertung_text += "GUT: Ausreichende Sicherheitsmarge vorhanden."
        elif margin > 0:
            bewertung_text += "GRENZWERTIG: Geringe Sicherheitsmarge!"
        else:
            bewertung_text += "KRITISCH: Leitertemperatur überschreitet zulässige Grenze!"

        self._add_text_box(parent, bewertung_text, bg=ARCADIS_LIGHT_GREY if margin > 5 else '#FFE6E6')

        # MCP-VALIDIERUNG
        if mcp_report:
            self._add_section_header(parent, "MCP-VALIDIERUNG")
            
            summary = mcp_report['mcp_summary']
            validation_text = f"""
╔══════════════════════════════════════════════════════════════╗
║           MCP CALCULATION VALIDATION SUMMARY                ║
╠══════════════════════════════════════════════════════════════╣
║  Validierte Schritte: {summary['passed_steps']}/{summary['total_steps']}                                   ║
║  Erfolgsrate: {summary['success_rate']:.1f}%                                        ║
║  Status: {'ALLE TESTS BESTANDEN' if summary['all_valid'] else 'EINIGE TESTS FEHLGESCHLAGEN'}                       ║
╚══════════════════════════════════════════════════════════════╝

"""
            for val in summary['validation_log']:
                status_icon = "[OK]" if val.is_valid else "[FEHLER]"
                validation_text += f"\n{status_icon} {val.step_name}\n"
                validation_text += f"   Formel: {val.formula}\n"
                validation_text += f"   Ergebnis: {val.calculated_value:.6e}\n"
                validation_text += f"   {val.validation_message}\n"
            
            self._add_text_box(parent, validation_text, font=('Courier', 9), 
                             bg='#E8F5E9' if summary['all_valid'] else '#FFF3E0')

        # REFERENZEN
        self._add_section_header(parent, "7. REFERENZEN & NORMEN")
        ref_text = """
• IEC 60287-1-1:2023 - Electric cables - Calculation of the current rating - Part 1-1: Current rating equations
• IEC 60287-2-1:2023 - Part 2-1: Thermal resistance - Calculation of thermal resistance
• DIN EN 12524:2000-07 - Baustoffe und -produkte - Wärme- und feuchteschutztechnische Eigenschaften
• VDI-Wärmeatlas 11. Auflage - Wärmeleitfähigkeit von Metallen und Isolierstoffen
• VDI 4640 Blatt 1 - Thermische Nutzung des Untergrunds - Erdwärmequellen
"""
        self._add_text_box(parent, ref_text, font=('Courier', 9))

    def _add_section_header(self, parent, text):
        """Fügt eine Abschnittsüberschrift hinzu"""
        frame = tk.Frame(parent, bg=ARCADIS_BLUE, height=40)
        frame.pack(fill=tk.X, pady=(20, 10), padx=5)
        frame.pack_propagate(False)
        
        tk.Label(
            frame,
            text=text,
            font=('Arial', 12, 'bold'),
            fg='white',
            bg=ARCADIS_BLUE,
            anchor='w'
        ).pack(side=tk.LEFT, padx=15, pady=10)

    def _add_subsection_header(self, parent, text):
        """Fügt eine Unterabschnittsüberschrift hinzu"""
        tk.Label(
            parent,
            text=text,
            font=('Arial', 11, 'bold'),
            fg=ARCADIS_ORANGE,
            bg=ARCADIS_WHITE,
            anchor='w'
        ).pack(fill=tk.X, pady=(15, 5), padx=20)

    def _add_data_table(self, parent, data):
        """Fügt eine Datentabelle hinzu"""
        frame = tk.Frame(parent, bg=ARCADIS_WHITE, relief=tk.RIDGE, bd=1)
        frame.pack(fill=tk.X, pady=5, padx=20)

        for i, (label, value, unit) in enumerate(data):
            row_frame = tk.Frame(frame, bg=ARCADIS_LIGHT_GREY if i % 2 == 0 else ARCADIS_WHITE)
            row_frame.pack(fill=tk.X)

            tk.Label(
                row_frame,
                text=label,
                font=('Arial', 10),
                fg=ARCADIS_BLUE,
                bg=row_frame['bg'],
                anchor='w',
                width=35
            ).pack(side=tk.LEFT, padx=10, pady=5)

            tk.Label(
                row_frame,
                text=f"{value} {unit}",
                font=('Arial', 10, 'bold'),
                fg='black',
                bg=row_frame['bg'],
                anchor='e',
                width=20
            ).pack(side=tk.RIGHT, padx=10, pady=5)

    def _add_formula_block(self, parent, title, formula, variables, calculation, result):
        """Fügt einen Formelblock hinzu"""
        frame = tk.Frame(parent, bg='#F0F8FF', relief=tk.GROOVE, bd=2)
        frame.pack(fill=tk.X, pady=10, padx=20)

        # Titel
        tk.Label(
            frame,
            text=title,
            font=('Arial', 10, 'bold'),
            fg=ARCADIS_BLUE,
            bg='#F0F8FF',
            anchor='w'
        ).pack(fill=tk.X, padx=10, pady=(10, 5))

        # Formel
        tk.Label(
            frame,
            text=f"Formel:  {formula}",
            font=('Courier', 11, 'bold'),
            fg='black',
            bg='#F0F8FF',
            anchor='w'
        ).pack(fill=tk.X, padx=20, pady=5)

        # Variablen
        var_frame = tk.Frame(frame, bg='#F0F8FF')
        var_frame.pack(fill=tk.X, padx=20, pady=5)

        for var_name, var_value, var_desc in variables:
            var_line = tk.Frame(var_frame, bg='#F0F8FF')
            var_line.pack(fill=tk.X, pady=2)

            tk.Label(
                var_line,
                text=f"  {var_name} = {var_value}",
                font=('Courier', 10),
                fg='black',
                bg='#F0F8FF',
                anchor='w',
                width=40
            ).pack(side=tk.LEFT)

            if var_desc:
                tk.Label(
                    var_line,
                    text=f"  # {var_desc}",
                    font=('Courier', 9, 'italic'),
                    fg=ARCADIS_GREY,
                    bg='#F0F8FF',
                    anchor='w'
                ).pack(side=tk.LEFT)

        # Berechnung
        tk.Label(
            frame,
            text=f"Einsetzen:  {calculation}",
            font=('Courier', 10),
            fg='#006400',
            bg='#F0F8FF',
            anchor='w'
        ).pack(fill=tk.X, padx=20, pady=5)

        # Ergebnis
        result_frame = tk.Frame(frame, bg='#FFE6CC', relief=tk.RAISED, bd=1)
        result_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            result_frame,
            text=f"➤  {result}",
            font=('Courier', 12, 'bold'),
            fg=ARCADIS_ORANGE,
            bg='#FFE6CC',
            anchor='w'
        ).pack(padx=10, pady=8)

    def _add_text_box(self, parent, text, bg=ARCADIS_LIGHT_GREY, font=('Arial', 10)):
        """Fügt eine Textbox hinzu"""
        frame = tk.Frame(parent, bg=bg, relief=tk.RIDGE, bd=1)
        frame.pack(fill=tk.X, pady=5, padx=20)

        tk.Label(
            frame,
            text=text,
            font=font,
            fg='black',
            bg=bg,
            anchor='w',
            justify=tk.LEFT
        ).pack(padx=15, pady=10)

    def _save_calculation_report_txt(self):
        """Speichert den vollständigen Rechenweg als TXT-Datei"""
        if not self.calculation_results:
            messagebox.showwarning("ARCADIS", "Keine Berechnungsergebnisse vorhanden!")
            return
        
        try:
            from tkinter import filedialog
            from datetime import datetime
            
            # Dateinamen vorschlagen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"ARCADIS_Rechenweg_{timestamp}.txt"
            
            # Speicherdialog öffnen
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text-Dateien", "*.txt"), ("Alle Dateien", "*.*")],
                initialfile=default_filename,
                title="Rechenweg speichern"
            )
            
            if not filename:
                return  # User cancelled
            
            results = self.calculation_results
            
            # Text-Bericht generieren
            report_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ARCADIS THERMAL CALCULATION REPORT                       ║
║                  Vollständiger Rechenweg mit Formeln                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Norm: IEC 60287-1-1:2023 / IEC 60287-2-1:2023

════════════════════════════════════════════════════════════════════════════════
1. GEGEBEN: EINGABEPARAMETER
════════════════════════════════════════════════════════════════════════════════

Systemtyp:                       {results['system_type']}
Nennspannung:                    {results['voltage']:.0f} kV
Betriebsstrom:                   {results['current']:.2f} A
Leiterdurchmesser:               {float(self.param_vars['conductor_diameter'].get()):.2f} mm
Max. zulässige Leitertemperatur: {results['max_temp']:.1f} °C
Umgebungstemperatur:             {results['ambient_temp']:.1f} °C
Verlegetiefe:                    {results['burial_depth']:.2f} m
Leitertyp:                       {self.conductor_var.get()}
Anzahl Kabelschichten:           {len(self.cable_layers)}

════════════════════════════════════════════════════════════════════════════════
2. ANNAHMEN & RANDBEDINGUNGEN
════════════════════════════════════════════════════════════════════════════════

NORMATIVE GRUNDLAGEN:
✓ IEC 60287-1-1:2023 - Elektrische Kabel - Belastbarkeit
✓ IEC 60287-2-1:2023 - Thermische Widerstände
✓ DIN EN 12524:2000-07 - Materialeigenschaften
✓ VDI-Wärmeatlas - Wärmeübertragung
✓ VDI 4640 Blatt 1 - Erdreichparameter

BETRIEBSBEDINGUNGEN:
• Stationärer Betriebszustand (keine transienten Effekte)
• Konstante Umgebungstemperatur: θ_a = {results['ambient_temp']:.1f} °C
• Verlegetiefe: {results['burial_depth']:.2f} m unter Geländeoberkante
• Systemtyp: {'Drehstrom (AC, 50 Hz)' if results['system_type'] == 'AC' else 'Gleichstrom (DC)'}

MATERIALEIGENSCHAFTEN:
• Leiter: {self.conductor_var.get()}
  - Spez. Widerstand: ρ₂₀ = {results['conductor_details'].get('rho20', 1.72e-8):.3e} Ω·m
  - Temperaturkoeffizient: α = {results['conductor_details'].get('alpha', 0.00393):.5f} /K
  
• Kabelschichten: {len(self.cable_layers)} Schichten
"""
            
            # Schichten hinzufügen
            for i, layer in enumerate(self.cable_layers, 1):
                report_text += f"  {i}. {layer.name} ({layer.material})\n"
                report_text += f"     λ = {layer.thermal_conductivity:.3f} W/(m·K)\n"
                report_text += f"     r_i = {layer.inner_radius_mm:.2f} mm, r_o = {layer.outer_radius_mm:.2f} mm\n"
            
            report_text += f"""
════════════════════════════════════════════════════════════════════════════════
3. RECHENWEG: ELEKTRISCHE VERLUSTE
════════════════════════════════════════════════════════════════════════════════

3.1 LEITERQUERSCHNITT
─────────────────────
Formel: A = π · (d/2)²

Gegeben:
  d = {float(self.param_vars['conductor_diameter'].get()):.2f} mm = {float(self.param_vars['conductor_diameter'].get())/1000:.5f} m

Berechnung:
  A = π · ({float(self.param_vars['conductor_diameter'].get())/1000:.5f} / 2)²
  A = π · ({float(self.param_vars['conductor_diameter'].get())/2000:.5f})²
  A = {results['conductor_details']['area']:.6e} m²

► ERGEBNIS: A = {results['conductor_details']['area']:.6e} m²


3.2 TEMPERATURABHÄNGIGER SPEZIFISCHER WIDERSTAND
──────────────────────────────────────────────────
Formel: ρ(θ) = ρ₂₀ · [1 + α · (θ - 20°C)]

Gegeben:
  ρ₂₀ = {results['conductor_details'].get('rho20', 1.72e-8):.3e} Ω·m
  α = {results['conductor_details'].get('alpha', 0.00393):.5f} /K
  θ = {results['max_temp']:.1f} °C

Berechnung:
  ρ({results['max_temp']:.1f}°C) = {results['conductor_details'].get('rho20', 1.72e-8):.3e} · [1 + {results['conductor_details'].get('alpha', 0.00393):.5f} · ({results['max_temp']:.1f} - 20)]
  ρ(θ) = {results['conductor_details']['rho_temp']:.3e} Ω·m

► ERGEBNIS: ρ(θ) = {results['conductor_details']['rho_temp']:.3e} Ω·m


3.3 GLEICHSTROMWIDERSTAND
──────────────────────────
Formel: R_DC = ρ(θ) / A

Gegeben:
  ρ(θ) = {results['conductor_details']['rho_temp']:.3e} Ω·m
  A = {results['conductor_details']['area']:.6e} m²

Berechnung:
  R_DC = {results['conductor_details']['rho_temp']:.3e} / {results['conductor_details']['area']:.6e}
  R_DC = {results['conductor_details']['r_dc']:.6f} Ω/m

► ERGEBNIS: R_DC = {results['conductor_details']['r_dc']:.6f} Ω/m


3.4 LEITERVERLUSTE
───────────────────
Formel: P = I² · R

Gegeben:
  I = {results['current']:.2f} A
  R = {results['conductor_details'].get('resistance', results['conductor_details']['r_dc']):.6f} Ω/m

Berechnung:
  P = ({results['current']:.2f})² · {results['conductor_details'].get('resistance', results['conductor_details']['r_dc']):.6f}
  P = {results['current']**2:.2f} · {results['conductor_details'].get('resistance', results['conductor_details']['r_dc']):.6f}
  P = {results['conductor_losses']:.4f} W/m

► ERGEBNIS: P_Leiter = {results['conductor_losses']:.4f} W/m


════════════════════════════════════════════════════════════════════════════════
4. RECHENWEG: THERMISCHE WIDERSTÄNDE
════════════════════════════════════════════════════════════════════════════════

Formel: R_th = ln(r_o/r_i) / (2π · λ)

"""
            
            # Thermische Widerstände
            for i, layer in enumerate(self.cable_layers):
                if i < len(results['thermal_resistances']):
                    r_th = results['thermal_resistances'][i]
                    report_text += f"""
4.{i+1} {layer.name.upper()}
{'─' * 60}
Gegeben:
  r_i = {layer.inner_radius_mm:.2f} mm = {layer.inner_radius_mm/1000:.5f} m
  r_o = {layer.outer_radius_mm:.2f} mm = {layer.outer_radius_mm/1000:.5f} m
  λ = {layer.thermal_conductivity:.3f} W/(m·K)

Berechnung:
  R_th = ln({layer.outer_radius_mm:.2f}/{layer.inner_radius_mm:.2f}) / (2π · {layer.thermal_conductivity:.3f})
  R_th = {r_th:.6f} K·m/W

► ERGEBNIS: R_th,{i+1} = {r_th:.6f} K·m/W

"""
            
            report_text += f"""
GESAMTER THERMISCHER WIDERSTAND:
  ΣR_th = {' + '.join([f'{r:.6f}' for r in results['thermal_resistances']])}
  ΣR_th = {results['total_thermal_resistance']:.6f} K·m/W


════════════════════════════════════════════════════════════════════════════════
5. ERGEBNISSE
════════════════════════════════════════════════════════════════════════════════

5.1 TEMPERATURANSTIEG
──────────────────────
Formel: Δθ = P_total · R_th,total

Gegeben:
  P_total = {results['total_losses']:.4f} W/m
  R_th,total = {results['total_thermal_resistance']:.4f} K·m/W

Berechnung:
  Δθ = {results['total_losses']:.4f} · {results['total_thermal_resistance']:.4f}
  Δθ = {results['temperature_rise']:.2f} K

► ERGEBNIS: Δθ = {results['temperature_rise']:.2f} K


5.2 LEITERTEMPERATUR
─────────────────────
Formel: θ_Leiter = θ_a + Δθ

Gegeben:
  θ_a = {results['ambient_temp']:.1f} °C
  Δθ = {results['temperature_rise']:.2f} K

Berechnung:
  θ_Leiter = {results['ambient_temp']:.1f} + {results['temperature_rise']:.2f}
  θ_Leiter = {results['conductor_temp']:.2f} °C

► ERGEBNIS: θ_Leiter = {results['conductor_temp']:.2f} °C


════════════════════════════════════════════════════════════════════════════════
6. BEWERTUNG
════════════════════════════════════════════════════════════════════════════════

Berechnete Leitertemperatur:  {results['conductor_temp']:.2f} °C
Maximal zulässige Temperatur: {results['max_temp']:.1f} °C
Sicherheitsmarge:             {results['safety_margin']:.2f} K ({(results['safety_margin']/results['max_temp']*100):.1f}%)

"""
            margin = results['safety_margin']
            if margin > 10:
                report_text += "SEHR GUT: Große Sicherheitsmarge vorhanden!\n"
            elif margin > 5:
                report_text += "GUT: Ausreichende Sicherheitsmarge vorhanden.\n"
            elif margin > 0:
                report_text += "GRENZWERTIG: Geringe Sicherheitsmarge!\n"
            else:
                report_text += "KRITISCH: Leitertemperatur überschreitet zulässige Grenze!\n"
            
            report_text += f"""

════════════════════════════════════════════════════════════════════════════════
7. REFERENZEN & NORMEN
════════════════════════════════════════════════════════════════════════════════

• IEC 60287-1-1:2023 - Electric cables - Calculation of the current rating
  Part 1-1: Current rating equations (100 % load factor)

• IEC 60287-2-1:2023 - Electric cables - Calculation of the current rating
  Part 2-1: Thermal resistance - Calculation of thermal resistance

• DIN EN 12524:2000-07 - Baustoffe und -produkte
  Wärme- und feuchteschutztechnische Eigenschaften

• VDI-Wärmeatlas 11. Auflage
  Wärmeleitfähigkeit von Metallen und Isolierstoffen

• VDI 4640 Blatt 1 - Thermische Nutzung des Untergrunds
  Erdwärmequellen


════════════════════════════════════════════════════════════════════════════════
                              ENDE DES BERICHTS
════════════════════════════════════════════════════════════════════════════════

Erstellt mit: ARCADIS Professional HGÜ Thermal Calculator
Software-Version: 1.0
Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Dieser Bericht wurde automatisch generiert und enthält den vollständigen
mathematischen Rechenweg aller thermischen Berechnungen nach IEC 60287.
"""
            
            # In Datei schreiben
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            messagebox.showinfo(
                "ARCADIS - Gespeichert",
                f"Rechenweg erfolgreich gespeichert!\n\n{filename}\n\n"
                f"Dateigröße: {len(report_text)} Zeichen"
            )
            
        except Exception as e:
            messagebox.showerror(
                "ARCADIS - Speicherfehler",
                f"Fehler beim Speichern:\n{str(e)}"
            )

    def _export_calculation_to_pdf(self):
        """Exportiert Berechnung als PDF mit matplotlib"""
        if not self.calculation_results:
            messagebox.showwarning("ARCADIS", "Keine Berechnungsergebnisse vorhanden!")
            return
        
        try:
            from tkinter import filedialog
            from datetime import datetime
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages
            
            # Dateinamen vorschlagen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"ARCADIS_Thermal_Report_{timestamp}.pdf"
            
            # Speicherdialog öffnen
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")],
                initialfile=default_filename,
                title="PDF-Report speichern"
            )
            
            if not filename:
                return  # User cancelled
            
            results = self.calculation_results
            
            # PDF erstellen
            with PdfPages(filename) as pdf:
                # Seite 1: Deckblatt
                fig = plt.figure(figsize=(8.27, 11.69))  # A4
                fig.patch.set_facecolor('white')
                ax = fig.add_subplot(111)
                ax.axis('off')
                
                # ARCADIS Header
                ax.text(0.5, 0.95, 'ARCADIS', 
                       ha='center', va='top', fontsize=32, fontweight='bold',
                       color=ARCADIS_BLUE)
                ax.text(0.5, 0.90, 'Thermal Calculation Report', 
                       ha='center', va='top', fontsize=20,
                       color=ARCADIS_ORANGE)
                ax.text(0.5, 0.85, 'HGÜ Cable Thermal Analysis', 
                       ha='center', va='top', fontsize=14,
                       color=ARCADIS_GREY)
                
                # Trennlinie
                ax.plot([0.1, 0.9], [0.82, 0.82], 'k-', linewidth=2)
                
                # Projekttitel
                ax.text(0.5, 0.75, 'CALCULATION SUMMARY', 
                       ha='center', va='top', fontsize=16, fontweight='bold')
                
                # Eingabedaten
                y_pos = 0.65
                line_height = 0.04
                
                info_text = [
                    f"System Type: {results['system_type']}",
                    f"Voltage: {results['voltage']:.0f} kV",
                    f"Current: {results['current']:.2f} A",
                    f"Conductor Diameter: {float(self.param_vars['conductor_diameter'].get()):.2f} mm",
                    f"Max Temperature: {results['max_temp']:.1f} °C",
                    f"Ambient Temperature: {results['ambient_temp']:.1f} °C",
                    f"Burial Depth: {results['burial_depth']:.2f} m",
                    "",
                    "RESULTS:",
                    f"Conductor Losses: {results['conductor_losses']:.2f} W/m",
                    f"Total Thermal Resistance: {results['total_thermal_resistance']:.4f} K·m/W",
                    f"Temperature Rise: {results['temperature_rise']:.2f} K",
                    f"Conductor Temperature: {results['conductor_temp']:.2f} °C",
                    f"Safety Margin: {results['safety_margin']:.2f} K",
                ]
                
                for line in info_text:
                    if line == "RESULTS:":
                        ax.text(0.15, y_pos, line, ha='left', va='top', 
                               fontsize=12, fontweight='bold')
                    else:
                        ax.text(0.15, y_pos, line, ha='left', va='top', fontsize=11)
                    y_pos -= line_height
                
                # Footer
                ax.text(0.5, 0.05, f'Generated: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}', 
                       ha='center', va='bottom', fontsize=8, color='gray')
                ax.text(0.5, 0.02, 'Standard: IEC 60287-1-1:2023 / IEC 60287-2-1:2023', 
                       ha='center', va='bottom', fontsize=8, color='gray')
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
                
                # Seite 2: Temperaturprofil (wenn cable_layers vorhanden)
                if hasattr(self, 'cable_layers') and self.cable_layers:
                    fig, ax = plt.subplots(figsize=(8.27, 11.69))
                    
                    # Titel
                    ax.text(0.5, 0.98, 'Radial Temperature Distribution', 
                           ha='center', va='top', fontsize=16, fontweight='bold',
                           transform=ax.transAxes)
                    
                    # Temperaturen berechnen (vereinfacht)
                    radii = []
                    temps = []
                    current_temp = results['conductor_temp']
                    
                    for i, layer in enumerate(self.cable_layers):
                        radii.append(layer.inner_radius_mm)
                        temps.append(current_temp)
                        
                        if i < len(results['thermal_resistances']):
                            r_th = results['thermal_resistances'][i]
                            temp_drop = results['conductor_losses'] * r_th
                            current_temp -= temp_drop
                        
                        radii.append(layer.outer_radius_mm)
                        temps.append(current_temp)
                    
                    # Plot
                    ax2 = plt.subplot(2, 1, 1)
                    ax2.plot(radii, temps, 'o-', linewidth=2, markersize=6, color=ARCADIS_ORANGE)
                    ax2.axhline(y=results['max_temp'], color='r', linestyle='--', 
                               label=f'Max. Temperature: {results["max_temp"]:.1f}°C')
                    ax2.axhline(y=results['ambient_temp'], color='b', linestyle='--', 
                               label=f'Ambient: {results["ambient_temp"]:.1f}°C')
                    ax2.set_xlabel('Radius [mm]', fontsize=12)
                    ax2.set_ylabel('Temperature [°C]', fontsize=12)
                    ax2.set_title('Temperature vs. Radius', fontsize=14, fontweight='bold')
                    ax2.grid(True, alpha=0.3)
                    ax2.legend()
                    
                    # Kabelschichten-Tabelle
                    ax3 = plt.subplot(2, 1, 2)
                    ax3.axis('off')
                    
                    table_data = [['Layer', 'Material', 'λ [W/(m·K)]', 'R_th [K·m/W]']]
                    for i, layer in enumerate(self.cable_layers):
                        if i < len(results['thermal_resistances']):
                            r_th = results['thermal_resistances'][i]
                            table_data.append([
                                layer.name,
                                layer.material,
                                f"{layer.thermal_conductivity:.3f}",
                                f"{r_th:.6f}"
                            ])
                    
                    table = ax3.table(cellText=table_data, cellLoc='left',
                                     loc='center', colWidths=[0.25, 0.25, 0.25, 0.25])
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1, 2)
                    
                    # Header-Zeile hervorheben
                    for i in range(4):
                        table[(0, i)].set_facecolor(ARCADIS_LIGHT_GREY)
                        table[(0, i)].set_text_props(weight='bold')
                    
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close()
            
            messagebox.showinfo(
                "ARCADIS - PDF erstellt",
                f"PDF-Report erfolgreich erstellt!\n\n{filename}"
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror(
                "ARCADIS - PDF-Export-Fehler",
                f"Fehler beim PDF-Export:\n{str(e)}\n\nDetails:\n{error_details[:500]}"
            )

    def calculate_thermal(self):
        system_type = self.system_type.get()
        self.init_trace_log(system_type)

        voltage = float(self.param_vars['voltage'].get())
        current = float(self.param_vars['current'].get())
        conductor_diameter = float(self.param_vars['conductor_diameter'].get())
        max_temp = float(self.param_vars['max_temp'].get())
        ambient_temp = float(self.param_vars['ambient_temp'].get())
        burial_depth = float(self.param_vars['burial_depth'].get())

        conductor_losses, conductor_details = self.calc_conductor_losses(
            system_type,
            current,
            conductor_diameter,
            max_temp
        )
        dielectric_losses, dielectric_details = self.calc_dielectric_losses(system_type, voltage)
        sheath_losses, sheath_details = self.calc_sheath_losses(system_type, current, voltage)

        total_losses = conductor_losses + dielectric_losses + sheath_losses
        self.add_trace_entry(
            category="Elektrische Verluste",
            title="Gesamtverlustleistung",
            formula="P_total = P_leiter + P_diel + P_mantel",
            variables={
                "P_leiter": f"{conductor_losses:.4f} W/m",
                "P_diel": f"{dielectric_losses:.4f} W/m",
                "P_mantel": f"{sheath_losses:.4f} W/m"
            },
            result=total_losses,
            unit="W/m"
        )

        thermal_resistances, thermal_details = self.calc_thermal_resistances()
        total_thermal_resistance = sum(thermal_resistances)
        self.add_trace_entry(
            category="Thermischer Widerstand",
            title="Summe der Widerstände",
            formula="ΣR_th = Σ ln(r_2 / r_1) / (2 π λ)",
            variables={"ΣR_th": f"{total_thermal_resistance:.6f} K·m/W"},
            result=total_thermal_resistance,
            unit="K·m/W"
        )

        temperature_rise = total_losses * total_thermal_resistance
        conductor_temp = ambient_temp + temperature_rise
        safety_margin = max_temp - conductor_temp

        self.add_trace_entry(
            category="Temperaturbewertung",
            title="Leitertemperatur",
            formula="θ_L = θ_U + P_total · ΣR_th",
            variables={
                "θ_U": f"{ambient_temp:.2f} °C",
                "P_total": f"{total_losses:.4f} W/m",
                "ΣR_th": f"{total_thermal_resistance:.6f} K·m/W"
            },
            result=conductor_temp,
            unit="°C"
        )

        self.add_trace_entry(
            category="Temperaturbewertung",
            title="Sicherheitsmarge",
            formula="Δθ = θ_max - θ_L",
            variables={
                "θ_max": f"{max_temp:.2f} °C",
                "θ_L": f"{conductor_temp:.2f} °C"
            },
            result=safety_margin,
            unit="K"
        )

        results = {
            'system_type': system_type,
            'voltage': voltage,
            'current': current,
            'conductor_losses': conductor_losses,
            'dielectric_losses': dielectric_losses,
            'sheath_losses': sheath_losses,
            'total_losses': total_losses,
            'thermal_resistances': thermal_resistances,
            'thermal_resistance_details': thermal_details,
            'total_thermal_resistance': total_thermal_resistance,
            'temperature_rise': temperature_rise,
            'conductor_temp': conductor_temp,
            'ambient_temp': ambient_temp,
            'max_temp': max_temp,
            'burial_depth': burial_depth,
            'conductor_details': conductor_details,
            'dielectric_details': dielectric_details,
            'sheath_details': sheath_details,
            'safety_margin': safety_margin
        }
        self.calculation_results = results
        return results

    def calc_conductor_losses(self, system_type, current, diameter, temperature):
        conductor_type = self.conductor_var.get()
        radius = diameter / 2000  # mm to m
        area = math.pi * radius**2

        self.add_trace_entry(
            category="Elektrische Parameter",
            title="Leiterquerschnitt",
            formula="A = π · r^2",
            variables={"r": f"{radius:.6f} m"},
            result=area,
            unit="m²"
        )

        resistivity_data = {
            'Kupfer (Cu)': {'rho20': 1.724e-8, 'alpha': 0.00393},
            'Aluminium (Al)': {'rho20': 2.826e-8, 'alpha': 0.00403}
        }
        rho_props = resistivity_data.get(conductor_type, resistivity_data['Kupfer (Cu)'])
        rho_20 = rho_props['rho20']
        alpha = rho_props['alpha']

        rho_temp = rho_20 * (1 + alpha * (temperature - 20))
        self.add_trace_entry(
            category="Elektrische Parameter",
            title="Temperaturabhängiger spezifischer Widerstand",
            formula="ρ_θ = ρ_20 · (1 + α · (θ - 20°C))",
            variables={
                "ρ_20": f"{rho_20:.3e} Ω·m",
                "α": f"{alpha:.5f} 1/°C",
                "θ": f"{temperature:.2f} °C"
            },
            result=rho_temp,
            unit="Ω·m"
        )

        r_dc = rho_temp / area
        self.add_trace_entry(
            category="Elektrische Verluste",
            title="Gleichstromwiderstand",
            formula="R_DC = ρ_θ / A",
            variables={
                "ρ_θ": f"{rho_temp:.3e} Ω·m",
                "A": f"{area:.6e} m²"
            },
            result=r_dc,
            unit="Ω/m"
        )

        resistance_label = "R_DC"
        resistance_value = r_dc
        ac_skin_factor = 1.0
        ac_proximity_factor = 1.0
        ac_applied = False

        if system_type == 'AC' and self.calc_options['ac_losses'].get():
            ac_skin_factor = 1.08
            ac_proximity_factor = 1.05
            resistance_value = r_dc * ac_skin_factor * ac_proximity_factor
            resistance_label = "R_AC"
            ac_applied = True
            self.add_trace_entry(
                category="Elektrische Verluste",
                title="AC-Korrekturfaktoren",
                formula="R_AC = R_DC · k_skin · k_prox",
                variables={
                    "R_DC": f"{r_dc:.6f} Ω/m",
                    "k_skin": f"{ac_skin_factor:.2f}",
                    "k_prox": f"{ac_proximity_factor:.2f}"
                },
                result=resistance_value,
                unit="Ω/m"
            )
        elif system_type == 'AC' and not self.calc_options['ac_losses'].get():
            self.add_trace_entry(
                category="Elektrische Verluste",
                title="AC-Korrektur deaktiviert",
                formula="R = R_DC",
                variables={"R_DC": f"{r_dc:.6f} Ω/m"},
                result=resistance_value,
                unit="Ω/m",
                notes="Benutzeroption: Skineffekt & Proximity wurden deaktiviert."
            )
        else:
            self.add_trace_entry(
                category="Elektrische Verluste",
                title="DC-System",
                formula="R = R_DC",
                variables={"R_DC": f"{r_dc:.6f} Ω/m"},
                result=resistance_value,
                unit="Ω/m",
                notes="DC-Betrieb: Skineffekt und Proximityverlust vernachlässigt."
            )

        conductor_losses = current**2 * resistance_value
        self.add_trace_entry(
            category="Elektrische Verluste",
            title="Leiterverluste",
            formula="P_leiter = I^2 · R",
            variables={
                "I": f"{current:.2f} A",
                "R": f"{resistance_value:.6f} Ω/m"
            },
            result=conductor_losses,
            unit="W/m"
        )

        details = {
            'conductor_type': conductor_type,
            'area': area,
            'rho_temp': rho_temp,
            'r_dc': r_dc,
            'resistance_value': resistance_value,
            'resistance_label': resistance_label,
            'ac_skin_factor': ac_skin_factor,
            'ac_proximity_factor': ac_proximity_factor,
            'ac_applied': ac_applied
        }
        return conductor_losses, details

    def calc_dielectric_losses(self, system_type, voltage):
        if system_type == 'DC':
            self.add_trace_entry(
                category="Elektrische Verluste",
                title="Dielektrische Verluste",
                formula="P_diel = 0",
                variables={"System": "DC"},
                result=0.0,
                unit="W/m",
                notes="DC-System: dielektrische Verluste werden vernachlässigt."
            )
            return 0.0, {'applied': False, 'reason': 'DC system'}

        if not self.calc_options['dielectric_losses'].get():
            self.add_trace_entry(
                category="Elektrische Verluste",
                title="Dielektrische Verluste deaktiviert",
                formula="P_diel = 0",
                variables={"Benutzer": "Checkbox deaktiviert"},
                result=0.0,
                unit="W/m"
            )
            return 0.0, {'applied': False, 'reason': 'User disabled'}

        if voltage <= 10:
            losses = 0.8 + voltage * 0.1
            segment = "≤10 kV"
        elif voltage <= 20:
            losses = 1.5 + (voltage - 10) * 0.25
            segment = "10-20 kV"
        else:
            losses = 4.0 + (voltage - 20) * 0.4
            segment = ">20 kV"

        self.add_trace_entry(
            category="Elektrische Verluste",
            title="Dielektrische Verluste",
            formula="IEC 60287 Näherung",
            variables={
                "U": f"{voltage:.2f} kV",
                "Segment": segment
            },
            result=losses,
            unit="W/m"
        )
        return losses, {'applied': True, 'segment': segment, 'voltage': voltage}

    def calc_sheath_losses(self, system_type, current, voltage):
        if system_type == 'DC':
            self.add_trace_entry(
                category="Elektrische Verluste",
                title="Mantelverluste",
                formula="P_mantel = 0",
                variables={"System": "DC"},
                result=0.0,
                unit="W/m",
                notes="DC-System: induzierte Mantelströme vernachlässigt."
            )
            return 0.0, {'applied': False, 'reason': 'DC system'}

        if not self.calc_options['sheath_losses'].get():
            self.add_trace_entry(
                category="Elektrische Verluste",
                title="Mantelverluste deaktiviert",
                formula="P_mantel = 0",
                variables={"Benutzer": "Checkbox deaktiviert"},
                result=0.0,
                unit="W/m"
            )
            return 0.0, {'applied': False, 'reason': 'User disabled'}

        if voltage >= 10:
            losses = 0.8 + current / 300 + voltage / 25
            formula_range = "U ≥ 10 kV"
        else:
            losses = 0.3 + current / 500
            formula_range = "U < 10 kV"

        self.add_trace_entry(
            category="Elektrische Verluste",
            title="Mantelverluste",
            formula="IEC 60287 Näherung",
            variables={
                "I": f"{current:.2f} A",
                "U": f"{voltage:.2f} kV",
                "Bereich": formula_range
            },
            result=losses,
            unit="W/m"
        )
        return losses, {'applied': True, 'formula_range': formula_range}

    def calc_thermal_resistances(self):
        resistances = []
        details = []

        for idx, layer in enumerate(self.cable_layers, 1):
            r_inner = layer.inner_radius_mm / 1000
            r_outer = layer.outer_radius_mm / 1000
            resistance = math.log(r_outer / r_inner) / (2 * math.pi * layer.thermal_conductivity)
            resistances.append(resistance)
            details.append({
                'layer_index': idx,
                'layer_name': layer.name,
                'material': layer.material,
                'r_inner_m': r_inner,
                'r_outer_m': r_outer,
                'lambda_value': layer.thermal_conductivity,
                'resistance': resistance
            })

            self.add_trace_entry(
                category="Thermischer Widerstand",
                title=f"{layer.name} (Schicht {idx})",
                formula="R_th = ln(r_2 / r_1) / (2 π λ)",
                variables={
                    "r_1": f"{r_inner:.4f} m",
                    "r_2": f"{r_outer:.4f} m",
                    "λ": f"{layer.thermal_conductivity:.3f} W/(m·K)"
                },
                result=resistance,
                unit="K·m/W"
            )

        if not resistances:
            self.add_trace_entry(
                category="Thermischer Widerstand",
                title="Keine Schichten",
                formula="—",
                variables={},
                result=0.0,
                unit="K·m/W",
                notes="Für eine Analyse sind Schichten erforderlich."
            )
        return resistances, details

    # ------------------------------------------------------------------
    # Trace-Unterstützung
    # ------------------------------------------------------------------
    def init_trace_log(self, system_type):
        self.trace_log = []
        self.add_trace_entry(
            category="Eingangsparameter",
            title="Systemauswahl",
            formula="—",
            variables={"Systemtyp": system_type},
            result=None,
            unit=""
        )

    def add_trace_entry(self, category, title, formula, variables, result, unit, notes=""):
        entry = {
            'category': category,
            'title': title,
            'formula': formula,
            'variables': variables,
            'result': result,
            'unit': unit,
            'notes': notes
        }
        self.trace_log.append(entry)

    def format_variables(self, variables):
        if not variables:
            return "—"
        return ", ".join(f"{key}={value}" for key, value in variables.items())

    def format_value(self, value, decimals=4):
        if value is None:
            return "—"
        if isinstance(value, (int, float)):
            return f"{value:.{decimals}f}"
        return str(value)

    # ------------------------------------------------------------------
    # Ergebnisdarstellung
    # ------------------------------------------------------------------
    def display_results(self, results):
        self.results_text.delete(1.0, tk.END)

        conductor_details = results.get('conductor_details', {})
        dielectric_details = results.get('dielectric_details', {})
        sheath_details = results.get('sheath_details', {})

        dielectric_descriptor = dielectric_details.get('segment') or dielectric_details.get('reason', '—')
        sheath_descriptor = sheath_details.get('formula_range') or sheath_details.get('reason', '—')

        report = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    ARCADIS PROFESSIONAL THERMAL ANALYSIS REPORT              ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Report Generated: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Analysis Standard: IEC 60287-1-1 & IEC 60287-2-1
Software: ARCADIS Professional HGÜ Thermal Calculator v2.2

INPUT PARAMETERS:
═══════════════════════════════════════════════════════════════════════════════
System Type:              {results['system_type']:<8s}
Nominal Voltage:           {results['voltage']:8.1f} kV
Operating Current:         {results['current']:8.1f} A
Maximum Conductor Temp:    {results['max_temp']:8.1f} °C
Ambient Temperature:       {results['ambient_temp']:8.1f} °C
Burial Depth:              {results['burial_depth']:8.2f} m
Cable Layers Configured:   {len(self.cable_layers):8d}

CABLE CONFIGURATION:
═══════════════════════════════════════════════════════════════════════════════
"""

        for idx, layer in enumerate(self.cable_layers, 1):
            report += (
                f"Layer {idx:2d}: {layer.name}\n"
                f"   Material:               {layer.material}\n"
                f"   Thickness:              {layer.thickness_mm:6.1f} mm\n"
                f"   Inner Radius:           {layer.inner_radius_mm:6.1f} mm\n"
                f"   Outer Radius:           {layer.outer_radius_mm:6.1f} mm\n"
                f"   Thermal Conductivity:   {layer.thermal_conductivity:6.3f} W/(m·K)\n\n"
            )

        report += f"""THERMAL LOSS CALCULATION (IEC 60287-1-1):
═══════════════════════════════════════════════════════════════════════════════
Conductor Losses:          {results['conductor_losses']:8.2f} W/m
Dielectric Losses:         {results['dielectric_losses']:8.2f} W/m
Sheath Losses:             {results['sheath_losses']:8.2f} W/m
Equivalent Resistance ({conductor_details.get('resistance_label', 'R')}): {conductor_details.get('resistance_value', 0):8.6f} Ω/m
Conductor Cross Section:  {conductor_details.get('area', 0):8.6e} m²
Dielectric Model:          {dielectric_descriptor}
Sheath Model:              {sheath_descriptor}

TOTAL POWER LOSSES:        {results['total_losses']:8.2f} W/m

THERMAL RESISTANCE ANALYSIS (IEC 60287-2-1):
═══════════════════════════════════════════════════════════════════════════════
Total Thermal Resistance:  {results['total_thermal_resistance']:8.4f} K·m/W

TEMPERATURE CALCULATION:
═══════════════════════════════════════════════════════════════════════════════
Ambient Temperature:       {results['ambient_temp']:8.1f} °C
Temperature Rise:          {results['temperature_rise']:8.1f} K
CONDUCTOR TEMPERATURE:     {results['conductor_temp']:8.1f} °C

SAFETY ASSESSMENT:
═══════════════════════════════════════════════════════════════════════════════
Temperature Limit:         {results['max_temp']:8.1f} °C
Safety Margin:             {results['safety_margin']:8.1f} K
Operating Status:          {'SAFE OPERATION' if results['conductor_temp'] < results['max_temp'] else 'CRITICAL - EXCEEDS LIMIT'}

DECISION BASIS & FORMULA TRACE:
═══════════════════════════════════════════════════════════════════════════════
"""

        grouped_entries = defaultdict(list)
        for entry in self.trace_log:
            grouped_entries[entry['category']].append(entry)

        for category, entries in grouped_entries.items():
            report += f"{category}:\n"
            for idx, entry in enumerate(entries, 1):
                report += f"  {idx:02d}) {entry['title']}\n"
                if entry['formula'] and entry['formula'] != "—":
                    report += f"       Formel: {entry['formula']}\n"
                if entry['variables']:
                    report += f"       Eingesetzte Werte: {self.format_variables(entry['variables'])}\n"
                if entry['result'] is not None:
                    report += f"       Ergebnis: {self.format_value(entry['result'])} {entry['unit']}\n"
                if entry.get('notes'):
                    report += f"       Hinweis: {entry['notes']}\n"
                report += "\n"

        report += """
═══════════════════════════════════════════════════════════════════════════════
© ARCADIS 2025 - Professional Engineering Solutions
═══════════════════════════════════════════════════════════════════════════════
        """

        self.results_text.insert(tk.END, report)
        self.notebook.select(2)

    def plot_temperature_profile(self, results):
        self.temp_ax.clear()

        radii = [float(self.param_vars['conductor_diameter'].get()) / 2]
        temperatures = [results['conductor_temp']]

        current_temp = results['conductor_temp']
        for idx, layer in enumerate(self.cable_layers):
            radii.append(layer.outer_radius_mm)
            if idx < len(results['thermal_resistances']):
                current_temp -= results['total_losses'] * results['thermal_resistances'][idx]
            temperatures.append(current_temp)

        self.temp_ax.plot(
            radii,
            temperatures,
            color=ARCADIS_ORANGE,
            linewidth=3,
            marker='o',
            markersize=6,
            markerfacecolor=ARCADIS_BLUE,
            markeredgecolor='white',
            markeredgewidth=1
        )

        self.temp_ax.axhline(
            y=results['max_temp'],
            color='red',
            linestyle='--',
            linewidth=2,
            label=f"Max. Temperatur: {results['max_temp']:.1f}°C"
        )
        self.temp_ax.axhline(
            y=results['ambient_temp'],
            color='blue',
            linestyle='--',
            linewidth=2,
            label=f"Umgebungstemperatur: {results['ambient_temp']:.1f}°C"
        )

        self.temp_ax.set_xlabel('Radius [mm]', fontsize=11, weight='bold', color=ARCADIS_BLUE)
        self.temp_ax.set_ylabel('Temperatur [°C]', fontsize=11, weight='bold', color=ARCADIS_BLUE)
        self.temp_ax.set_title('ARCADIS Radiale Temperaturverteilung', fontsize=12, weight='bold', color=ARCADIS_BLUE)
        self.temp_ax.grid(True, alpha=0.3)
        self.temp_ax.legend()

        self.temp_canvas.draw()
        self.notebook.select(1)

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------
    def update_status(self, message):
        self.status_label.config(text=f"ARCADIS Professional - {message}")
        self.window.update_idletasks()

    def load_demo_configuration(self):
        demo_layers = [
            ("Isolation", "XLPE", 8.0),
            ("Mantel", "PE-Mantel", 2.5),
            ("Schutzrohr", "PE-Rohr", 3.0),
            ("Bettung", "Sand feucht", 100.0),
            ("Erdreich", "Erdreich normal", 500.0)
        ]

        conductor_radius = float(self.param_vars['conductor_diameter'].get()) / 2
        current_radius = conductor_radius
        self.cable_layers.clear()

        for name, material, thickness in demo_layers:
            layer = CableLayer(name, material, current_radius, thickness)
            self.cable_layers.append(layer)
            current_radius = layer.outer_radius_mm

        self.update_layer_display()
        self.update_schematic()
        self.update_status("Demo-Konfiguration geladen")

    def run(self):
        welcome = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    ARCADIS PROFESSIONAL HGÜ THERMAL CALCULATOR               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Willkommen zur professionellen Ingenieurssoftware für thermische Kabelberechnungen!

Version: 2.2 Professional
Standards: IEC 60287-1-1 & IEC 60287-2-1
Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

FUNKTIONEN:
• Schichtkonfiguration mit Materialdatenbank
• AC/DC Differenzierung inkl. Formelklassifizierung
• Professionelle Visualisierung (Schema & Temperaturprofil)
• Vollständiger Berechnungs- und Entscheidungsnachweis

Die Demo-Konfiguration wurde geladen. Bitte Parameter prüfen und anschließend die thermische Analyse starten.

© ARCADIS 2025 - Professional Engineering Solutions
        """
        self.results_text.insert(tk.END, welcome)
        print("ARCADIS Professional HGÜ Thermal Calculator - GUI gestartet")
        self.window.mainloop()


if __name__ == "__main__":
    try:
        app = ARCADISSimpleThermalGUI()
        app.run()
    except Exception as exc:
        print(f"Fehler beim Starten der Anwendung: {exc}")
        input("Drücken Sie Enter zum Beenden...")
