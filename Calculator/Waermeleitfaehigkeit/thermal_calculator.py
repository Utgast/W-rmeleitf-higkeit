"""
Wärmeleitfähigkeit Calculator - Thermal Calculations
Berechnungsmodul für thermische Analysen
"""

import math
from material_database import MaterialDatabase


class ThermalCalculator:
    """Klasse für thermische Berechnungen"""
    
    def __init__(self):
        self.db = MaterialDatabase()
    
    def calculate_heat_flow(self, material_name, area, thickness, temp_diff):
        """
        Berechnet den Wärmestrom durch ein Material (Fourier'sches Gesetz)
        
        Q = λ × A × ΔT / d
        
        Args:
            material_name: Name des Materials
            area: Fläche in m²
            thickness: Dicke in m
            temp_diff: Temperaturdifferenz in K
            
        Returns:
            dict: Wärmestrom in W und weitere Details
        """
        # Eingabevalidierung
        if not material_name or not isinstance(material_name, str):
            raise ValueError("Materialname muss ein nicht-leerer String sein")
        
        if area <= 0:
            raise ValueError("Fläche muss größer als 0 sein")
        
        if thickness <= 0:
            raise ValueError("Dicke muss größer als 0 sein")
        
        lambda_value = self.db.get_lambda(material_name)
        
        if lambda_value is None:
            raise ValueError(f"Material '{material_name}' nicht gefunden")
        
        if lambda_value <= 0:
            raise ValueError(f"Ungültiger λ-Wert für Material '{material_name}': {lambda_value}")
        
        # Wärmestrom Q in Watt
        heat_flow = lambda_value * area * temp_diff / thickness
        
        # Wärmestromdichte q in W/m²
        heat_flux = heat_flow / area if area > 0 else 0
        
        # Wärmedurchlasswiderstand R in m²K/W
        thermal_resistance = thickness / lambda_value
        
        return {
            "heat_flow_W": heat_flow,
            "heat_flux_W_m2": heat_flux,
            "thermal_resistance_m2K_W": thermal_resistance,
            "lambda_W_mK": lambda_value,
            "material": material_name
        }
    
    def calculate_u_value(self, layers):
        """
        Berechnet den Wärmedurchgangskoeffizienten (U-Wert)
        
        U = 1 / (Rsi + R1 + R2 + ... + Rse)
        
        Args:
            layers: Liste von Schichten [(material_name, thickness), ...]
            
        Returns:
            dict: U-Wert und weitere Details
        """
        # Eingabevalidierung
        if not layers or len(layers) == 0:
            raise ValueError("Layer-Liste darf nicht leer sein")
        
        # Wärmeübergangswiderstände (DIN EN ISO 6946)
        R_si = 0.13  # Innerer Wärmeübergangswiderstand (m²K/W)
        R_se = 0.04  # Äußerer Wärmeübergangswiderstand (m²K/W)
        
        # Summe der Wärmedurchlasswiderstände
        R_total = R_si + R_se
        layer_details = []
        
        for material_name, thickness in layers:
            lambda_value = self.db.get_lambda(material_name)
            
            if lambda_value is None:
                raise ValueError(f"Material '{material_name}' nicht gefunden")
            
            R = thickness / lambda_value
            R_total += R
            
            layer_details.append({
                "material": material_name,
                "thickness_m": thickness,
                "lambda_W_mK": lambda_value,
                "resistance_m2K_W": R
            })
        
        # U-Wert in W/(m²K)
        u_value = 1.0 / R_total if R_total > 0 else float('inf')
        
        return {
            "u_value_W_m2K": u_value,
            "total_resistance_m2K_W": R_total,
            "R_si": R_si,
            "R_se": R_se,
            "layers": layer_details
        }
    
    def calculate_temperature_distribution(self, layers, temp_inside, temp_outside):
        """
        Berechnet die Temperaturverteilung durch mehrere Schichten
        
        Args:
            layers: Liste von Schichten [(material_name, thickness, points), ...]
            temp_inside: Innentemperatur in °C
            temp_outside: Außentemperatur in °C
            
        Returns:
            dict: Temperaturverteilung und Details
        """
        # Eingabevalidierung
        if not layers or len(layers) == 0:
            raise ValueError("Layer-Liste für Temperaturverteilung darf nicht leer sein")
        
        for i, layer in enumerate(layers):
            if len(layer) != 3:
                raise ValueError(f"Layer {i} muss 3 Werte haben: (material, thickness, points)")
            material, thickness, points = layer
            if thickness <= 0:
                raise ValueError(f"Dicke in Layer {i} muss größer als 0 sein")
            if points <= 0:
                raise ValueError(f"Anzahl Punkte in Layer {i} muss größer als 0 sein")
        
        u_result = self.calculate_u_value([(mat, thick) for mat, thick, _ in layers])
        u_value = u_result["u_value_W_m2K"]
        
        # Gesamtwärmestrom pro m²
        q = u_value * (temp_inside - temp_outside)
        
        # Temperaturverteilung berechnen
        temperatures = [temp_inside]
        positions = [0]
        current_position = 0
        
        # Innerer Wärmeübergangswiderstand
        R_si = 0.13
        temp_surface_inside = temp_inside - q * R_si
        temperatures.append(temp_surface_inside)
        positions.append(current_position)
        
        # Durch alle Schichten
        for material_name, thickness, points in layers:
            lambda_value = self.db.get_lambda(material_name)
            
            # Temperaturverlauf in der Schicht
            for i in range(points):
                x = (i + 1) / points * thickness
                current_position += thickness / points
                
                # Temperatur an Position x
                temp = temperatures[-1] - (q * x / lambda_value)
                temperatures.append(temp)
                positions.append(current_position)
        
        # Äußerer Wärmeübergangswiderstand
        R_se = 0.04
        temp_surface_outside = temperatures[-1] - q * R_se
        temperatures.append(temp_outside)
        positions.append(current_position)
        
        return {
            "positions_m": positions,
            "temperatures_C": temperatures,
            "heat_flux_W_m2": q,
            "u_value_W_m2K": u_value,
            "temp_drop_inside": temp_inside - temp_surface_inside,
            "temp_drop_outside": temp_surface_outside - temp_outside
        }
    
    def calculate_thermal_mass(self, material_name, volume):
        """
        Berechnet die thermische Masse (Wärmespeicherfähigkeit)
        
        C = ρ × c × V
        
        Args:
            material_name: Name des Materials
            volume: Volumen in m³
            
        Returns:
            dict: Thermische Masse und Details
        """
        density = self.db.get_density(material_name)
        specific_heat = self.db.get_specific_heat(material_name)
        
        if density is None or specific_heat is None:
            raise ValueError(f"Material '{material_name}' nicht gefunden")
        
        # Masse in kg
        mass = density * volume
        
        # Wärmespeicherfähigkeit in J/K
        thermal_mass = density * specific_heat * volume
        
        return {
            "thermal_mass_J_K": thermal_mass,
            "mass_kg": mass,
            "density_kg_m3": density,
            "specific_heat_J_kgK": specific_heat,
            "volume_m3": volume
        }
    
    def calculate_cooling_heating_time(self, material_name, volume, temp_change, power):
        """
        Berechnet die Zeit zum Aufheizen/Abkühlen
        
        t = (m × c × ΔT) / P
        
        Args:
            material_name: Name des Materials
            volume: Volumen in m³
            temp_change: Temperaturänderung in K
            power: Heiz-/Kühlleistung in W
            
        Returns:
            dict: Zeit und Details
        """
        thermal_mass_result = self.calculate_thermal_mass(material_name, volume)
        thermal_mass = thermal_mass_result["thermal_mass_J_K"]
        
        # Benötigte Energie in Joule
        energy_required = thermal_mass * temp_change
        
        # Zeit in Sekunden
        time_seconds = energy_required / power if power > 0 else float('inf')
        time_hours = time_seconds / 3600
        time_minutes = time_seconds / 60
        
        return {
            "time_seconds": time_seconds,
            "time_minutes": time_minutes,
            "time_hours": time_hours,
            "energy_required_J": energy_required,
            "energy_required_kWh": energy_required / 3600000,
            "power_W": power,
            "temp_change_K": temp_change
        }
    
    def calculate_condensation_risk(self, layers, temp_inside, temp_outside, 
                                   humidity_inside, humidity_outside):
        """
        Berechnet das Risiko für Tauwasserbildung (vereinfachte Glaser-Methode)
        
        Args:
            layers: Liste von Schichten
            temp_inside: Innentemperatur in °C
            temp_outside: Außentemperatur in °C
            humidity_inside: Relative Luftfeuchtigkeit innen in %
            humidity_outside: Relative Luftfeuchtigkeit außen in %
            
        Returns:
            dict: Kondensationsrisiko und Details
        """
        # Temperaturverteilung berechnen
        temp_dist = self.calculate_temperature_distribution(
            layers, temp_inside, temp_outside
        )
        
        # Sättigungsdampfdruck berechnen (vereinfachte Magnus-Formel)
        def saturation_pressure(temp):
            return 610.7 * math.exp((17.27 * temp) / (237.3 + temp))
        
        # Taupunkt berechnen
        def dew_point(temp, humidity):
            ps = saturation_pressure(temp)
            pv = ps * humidity / 100
            return 237.3 * math.log(pv / 610.7) / (17.27 - math.log(pv / 610.7))
        
        dew_point_inside = dew_point(temp_inside, humidity_inside)
        dew_point_outside = dew_point(temp_outside, humidity_outside)
        
        # Prüfen, ob Temperatur unter Taupunkt fällt
        condensation_risk = False
        risk_positions = []
        
        for i, temp in enumerate(temp_dist["temperatures_C"]):
            if temp < dew_point_inside:
                condensation_risk = True
                risk_positions.append({
                    "position_m": temp_dist["positions_m"][i],
                    "temperature_C": temp,
                    "dew_point_C": dew_point_inside
                })
        
        return {
            "condensation_risk": condensation_risk,
            "risk_positions": risk_positions,
            "dew_point_inside_C": dew_point_inside,
            "dew_point_outside_C": dew_point_outside,
            "temp_distribution": temp_dist
        }
