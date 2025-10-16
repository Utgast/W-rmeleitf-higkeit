"""
Wärmeleitfähigkeit Calculator - Material Database
Datenbank mit thermischen Eigenschaften von Baumaterialien
"""

class MaterialDatabase:
    """Datenbank für Materialeigenschaften"""
    
    # Wärmeleitfähigkeit λ (Lambda) in W/(m·K)
    MATERIALS = {
        # Beton und Mörtel
        "Beton (Normal)": {"lambda": 2.1, "density": 2400, "specific_heat": 1000},
        "Beton (Leicht)": {"lambda": 0.8, "density": 1800, "specific_heat": 1000},
        "Stahlbeton": {"lambda": 2.5, "density": 2500, "specific_heat": 1000},
        "Mörtel": {"lambda": 1.2, "density": 1900, "specific_heat": 1000},
        
        # Mauerwerk
        "Ziegel (Vollziegel)": {"lambda": 0.8, "density": 1800, "specific_heat": 1000},
        "Ziegel (Hochlochziegel)": {"lambda": 0.35, "density": 800, "specific_heat": 1000},
        "Porenbeton": {"lambda": 0.16, "density": 500, "specific_heat": 1000},
        "Kalksandstein": {"lambda": 0.8, "density": 1800, "specific_heat": 1000},
        
        # Dämmstoffe
        "Mineralwolle": {"lambda": 0.04, "density": 100, "specific_heat": 840},
        "Polystyrol (EPS)": {"lambda": 0.035, "density": 30, "specific_heat": 1500},
        "Polystyrol (XPS)": {"lambda": 0.032, "density": 35, "specific_heat": 1500},
        "Polyurethan (PUR)": {"lambda": 0.025, "density": 40, "specific_heat": 1400},
        "Steinwolle": {"lambda": 0.045, "density": 150, "specific_heat": 840},
        "Glaswolle": {"lambda": 0.04, "density": 100, "specific_heat": 840},
        
        # Holz
        "Holz (Weich)": {"lambda": 0.13, "density": 500, "specific_heat": 1600},
        "Holz (Hart)": {"lambda": 0.18, "density": 700, "specific_heat": 1600},
        "Sperrholz": {"lambda": 0.15, "density": 600, "specific_heat": 1600},
        "Spanplatte": {"lambda": 0.12, "density": 650, "specific_heat": 1600},
        
        # Metalle
        "Stahl": {"lambda": 50.0, "density": 7850, "specific_heat": 460},
        "Aluminium": {"lambda": 160.0, "density": 2700, "specific_heat": 880},
        "Kupfer": {"lambda": 380.0, "density": 8900, "specific_heat": 380},
        "Zink": {"lambda": 110.0, "density": 7200, "specific_heat": 380},
        
        # Kabel-Leiter (IEC 60287)
        "Kupferleiter": {"lambda": 380.0, "density": 8900, "specific_heat": 380},
        "Aluminiumleiter": {"lambda": 230.0, "density": 2700, "specific_heat": 880},
        
        # Glas
        "Glas (Normal)": {"lambda": 1.0, "density": 2500, "specific_heat": 840},
        "Isolierglas (2-fach)": {"lambda": 0.3, "density": 2500, "specific_heat": 840},
        "Isolierglas (3-fach)": {"lambda": 0.2, "density": 2500, "specific_heat": 840},
        
        # Sonstige
        "Gips": {"lambda": 0.35, "density": 1200, "specific_heat": 1000},
        "Gipskarton": {"lambda": 0.25, "density": 900, "specific_heat": 1000},
        "Lehm": {"lambda": 0.8, "density": 1600, "specific_heat": 1000},
        "Kork": {"lambda": 0.045, "density": 200, "specific_heat": 1800},
        "Bitumen": {"lambda": 0.17, "density": 1050, "specific_heat": 1000},
        "Kunststoff (PE)": {"lambda": 0.4, "density": 950, "specific_heat": 2300},
        
        # Kabel-Isolierungen (IEC 60287-2-1)
        "XLPE (Vernetztes Polyethylen)": {"lambda": 0.286, "density": 920, "specific_heat": 2400},
        "EPR (Ethylen-Propylen)": {"lambda": 0.4, "density": 1100, "specific_heat": 2000},
        "PVC (Polyvinylchlorid)": {"lambda": 0.16, "density": 1400, "specific_heat": 1000},
        "PE (Polyethylen)": {"lambda": 0.4, "density": 950, "specific_heat": 2300},
        "Halbleitende XLPE": {"lambda": 0.286, "density": 920, "specific_heat": 2400},
        
        # Schutzrohre
        "PE-Schutzrohr": {"lambda": 0.4, "density": 950, "specific_heat": 2300},
        "PVC-Schutzrohr": {"lambda": 0.16, "density": 1400, "specific_heat": 1000},
        "Stahlrohr": {"lambda": 50.0, "density": 7850, "specific_heat": 460},
        
        # Erdreich und Boden
        "Erdreich (trocken)": {"lambda": 0.5, "density": 1600, "specific_heat": 1000},
        "Erdreich (feucht)": {"lambda": 2.0, "density": 1800, "specific_heat": 1000},
        "Sand (trocken)": {"lambda": 0.4, "density": 1500, "specific_heat": 800},
        "Sand (feucht)": {"lambda": 1.5, "density": 1700, "specific_heat": 1000},
        
        # Luft
        "Luftschicht (ruhend)": {"lambda": 0.026, "density": 1.2, "specific_heat": 1000},
    }
    
    @classmethod
    def get_material(cls, name):
        """Gibt Materialeigenschaften zurück"""
        return cls.MATERIALS.get(name)
    
    @classmethod
    def get_all_materials(cls):
        """Gibt alle verfügbaren Materialien zurück"""
        return list(cls.MATERIALS.keys())
    
    @classmethod
    def get_lambda(cls, name):
        """Gibt Wärmeleitfähigkeit zurück"""
        material = cls.get_material(name)
        return material["lambda"] if material else None
    
    @classmethod
    def get_density(cls, name):
        """Gibt Dichte zurück"""
        material = cls.get_material(name)
        return material["density"] if material else None
    
    @classmethod
    def get_specific_heat(cls, name):
        """Gibt spezifische Wärmekapazität zurück"""
        material = cls.get_material(name)
        return material["specific_heat"] if material else None
    
    @classmethod
    def add_custom_material(cls, name, lambda_value, density, specific_heat):
        """Fügt benutzerdefiniertes Material hinzu"""
        cls.MATERIALS[name] = {
            "lambda": lambda_value,
            "density": density,
            "specific_heat": specific_heat
        }
    
    @classmethod
    def get_categories(cls):
        """Gibt Materialkategorien zurück"""
        return {
            "Beton": [k for k in cls.MATERIALS.keys() if "Beton" in k or "Mörtel" in k],
            "Mauerwerk": [k for k in cls.MATERIALS.keys() if any(x in k for x in ["Ziegel", "Porenbeton", "Kalksandstein"])],
            "Dämmstoffe": [k for k in cls.MATERIALS.keys() if any(x in k for x in ["Mineralwolle", "Polystyrol", "Polyurethan", "Steinwolle", "Glaswolle"])],
            "Holz": [k for k in cls.MATERIALS.keys() if "Holz" in k or any(x in k for x in ["Sperrholz", "Spanplatte"])],
            "Metalle": [k for k in cls.MATERIALS.keys() if any(x in k for x in ["Stahl", "Aluminium", "Kupfer", "Zink"])],
            "Glas": [k for k in cls.MATERIALS.keys() if "Glas" in k],
            "Erdreich": [k for k in cls.MATERIALS.keys() if any(x in k for x in ["Erdreich", "Sand"])],
            "Sonstige": [k for k in cls.MATERIALS.keys() if not any(cat in k for cat in ["Beton", "Ziegel", "Holz", "Stahl", "Aluminium", "Glas", "Erdreich", "Mineralwolle", "Polystyrol"])]
        }
