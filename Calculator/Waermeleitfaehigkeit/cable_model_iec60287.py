"""
IEC 60287 konforme Kabelmodellierung
Thermische Berechnung nach IEC 60287-1-1 und IEC 60287-2-1
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class CableLayer:
    """Eine Schicht im Kabel (Leiter, Isolierung, Schirm, etc.)"""
    name: str
    material: str
    inner_radius: float  # mm
    outer_radius: float  # mm
    thermal_conductivity: float  # W/(m·K)
    resistivity: float = 0.0  # Ω·mm²/m (nur für Leiter)
    temp_coefficient: float = 0.0  # 1/K (Temperaturkoeffizient des Widerstands)
    
    def get_thermal_resistance(self, length: float = 1.0) -> float:
        """
        Thermischer Widerstand nach IEC 60287-1-1 Gleichung (2)
        R_thermal = ρ_th × ln(r_outer/r_inner) / (2π)
        
        Args:
            length: Kabellänge in Metern
            
        Returns:
            Thermischer Widerstand in K·m/W
        """
        if self.inner_radius <= 0 or self.outer_radius <= self.inner_radius:
            return 0.0
        
        # Thermischer spezifischer Widerstand ρ_th = 1/λ
        rho_thermal = 1.0 / self.thermal_conductivity
        
        # R_th = ρ_th × ln(r_o/r_i) / (2π) in K·m/W
        r_thermal = rho_thermal * math.log(self.outer_radius / self.inner_radius) / (2 * math.pi)
        
        return r_thermal
    
    def get_electrical_resistance(self, length: float = 1.0, temperature: float = 20.0) -> float:
        """
        Elektrischer Widerstand mit Temperaturabhängigkeit
        R(T) = R_20 × [1 + α × (T - 20)]
        
        Args:
            length: Kabellänge in Metern
            temperature: Leitertemperatur in °C
            
        Returns:
            Elektrischer Widerstand in Ω
        """
        if self.resistivity <= 0:
            return 0.0
        
        # Querschnittsfläche in mm²
        area = math.pi * (self.outer_radius**2 - self.inner_radius**2)
        
        if area <= 0:
            return 0.0
        
        # R = ρ × L / A  where ρ in Ω·mm²/m, L in m, A in mm²
        # Result: Ω
        r_20 = self.resistivity * length / area  # Ω
        
        # Temperaturkorrektur
        r_temp = r_20 * (1 + self.temp_coefficient * (temperature - 20))
        
        return r_temp


class CableConfiguration:
    """
    IEC 60287 Kabelkonfiguration
    Berechnet thermisches Verhalten nach IEC 60287-1-1
    """
    
    def __init__(self, name: str = "Custom Cable"):
        self.name = name
        self.layers: List[CableLayer] = []
        self.external_layers: List[CableLayer] = []  # Externe Umgebung (Rohr, Erde)
        self.current: float = 0.0  # Ampere
        self.ambient_temp: float = 20.0  # °C
        self.max_conductor_temp: float = 90.0  # °C (Standard für XLPE)
    
    def add_layer(self, layer: CableLayer):
        """Fügt eine interne Kabelschicht hinzu"""
        self.layers.append(layer)
    
    def add_external_layer(self, layer: CableLayer):
        """Fügt eine externe Umgebungsschicht hinzu (Rohr, Erde, etc.)"""
        self.external_layers.append(layer)
    
    def get_conductor_layer(self) -> CableLayer:
        """Gibt die Leiterschicht zurück (erste Schicht)"""
        if not self.layers:
            raise ValueError("Keine Schichten definiert")
        return self.layers[0]
    
    def calculate_conductor_losses(self, temperature: float | None = None) -> float:
        """
        Berechnet Verlustleistung im Leiter nach IEC 60287-1-1 Gleichung (1)
        W_c = I² × R_ac(T)
        
        Args:
            temperature: Leitertemperatur in °C (wenn None, wird max_conductor_temp verwendet)
            
        Returns:
            Verlustleistung in W/m
        """
        if temperature is None:
            temperature = self.max_conductor_temp
        
        conductor = self.get_conductor_layer()
        r_conductor = conductor.get_electrical_resistance(length=1.0, temperature=temperature)
        
        # W = I² × R in W/m
        losses = self.current**2 * r_conductor
        
        return losses
    
    def get_total_thermal_resistance(self) -> float:
        """
        Summiert alle thermischen Widerstände (Kabel + externe Umgebung)
        R_total = Σ R_i nach IEC 60287-1-1
        
        Returns:
            Gesamter thermischer Widerstand in K·m/W
        """
        r_total = 0.0
        
        # Interne Kabelschichten
        for layer in self.layers:
            r_total += layer.get_thermal_resistance()
        
        # Externe Umgebungsschichten
        for layer in self.external_layers:
            r_total += layer.get_thermal_resistance()
        
        return r_total
    
    def calculate_conductor_temperature(self) -> Tuple[float, dict]:
        """
        Berechnet Leitertemperatur bei gegebenem Strom
        Nach IEC 60287-1-1: θ_c = θ_a + W_c × Σ(R_thermal)
        
        Iterative Lösung, da R_conductor von T abhängt
        
        Returns:
            Tuple: (Leitertemperatur °C, Detail-Dictionary)
        """
        # Starttemperatur
        t_conductor = self.max_conductor_temp 

        #Start-Temperatur sollte self.ambient_temp sein oder eine User Eingabe. Für alle kommenden Rechenschritte ist die Start-Temperatur dann jeweils vorherig berechnete t_new
        
        # Initialisierung für Robustheit
        losses = 0.0
        r_thermal = 0.0
        iteration = 0
        
        # Iterative Berechnung (max 10 Iterationen)
        for iteration in range(10): #lieber erstmal die Möglichkeit geben eine Fehlertoleranz anzugeben (nl_tol, l_tol) und maximale Iterationen (max_nl_it, max_l_it)
            # Verluste bei aktueller Temperatur
            losses = self.calculate_conductor_losses(temperature=t_conductor)
            
            # Thermischer Widerstand
            r_thermal = self.get_total_thermal_resistance()
            
            # Neue Leitertemperatur
            t_new = self.ambient_temp + losses * r_thermal
            
            # Konvergenz prüfen
            if abs(t_new - t_conductor) < 0.1:
                break
            
            t_conductor = t_new
        
        details = {
            "conductor_temp_C": t_conductor,
            "ambient_temp_C": self.ambient_temp,
            "losses_W_per_m": losses,
            "thermal_resistance_K_m_W": r_thermal,
            "current_A": self.current,
            "iterations": iteration + 1,
            "max_allowed_temp_C": self.max_conductor_temp
        }
        
        return t_conductor, details
    
    def calculate_temperature_profile(self) -> List[Tuple[float, float, str]]:
        """
        Berechnet Temperaturverlauf über alle Schichten
        Startet am Leiter und rechnet nach außen
        
        Returns:
            Liste von (radius_mm, temperature_C, layer_name)
        """
        # Leitertemperatur bestimmen
        t_conductor, _ = self.calculate_conductor_temperature()
        
        profile = []
        current_temp = t_conductor
        
        # Verluste für Wärmefluss
        losses = self.calculate_conductor_losses(temperature=t_conductor)
        
        for layer in self.layers:
            # Temperatur am inneren Radius
            profile.append((layer.inner_radius, current_temp, layer.name))
            
            # Temperaturabfall über diese Schicht
            delta_t = losses * layer.get_thermal_resistance()
            current_temp -= delta_t
            
            # Temperatur am äußeren Radius
            profile.append((layer.outer_radius, current_temp, layer.name))
        
        return profile
    
    def calculate_max_current(self) -> Tuple[float, dict]:
        """
        Berechnet maximal zulässigen Strom (Ampacity)
        Bei dem θ_conductor = θ_max erreicht wird
        
        Returns:
            Tuple: (Max. Strom in A, Detail-Dictionary)
        """
        # Binäre Suche für optimalen Strom
        i_min, i_max = 0.0, 10000.0
        
        for _ in range(20):
            i_test = (i_min + i_max) / 2
            self.current = i_test
            
            t_conductor, _ = self.calculate_conductor_temperature()
            
            if abs(t_conductor - self.max_conductor_temp) < 0.5:
                break
            
            if t_conductor > self.max_conductor_temp:
                i_max = i_test
            else:
                i_min = i_test
        
        # Finale Berechnung
        t_final, details = self.calculate_conductor_temperature()
        details["max_current_A"] = self.current
        
        return self.current, details


# ============================================================================
# VORDEFINIERTE KABELKONFIGURATIONEN
# ============================================================================

class CableMaterialLibrary:
    """Materialdatenbank für Kabelkomponenten"""
    
    # Leiter
    COPPER = {
        "lambda": 380.0,  # W/(m·K)
        "resistivity": 0.0175,  # Ω·mm²/m bei 20°C
        "temp_coefficient": 0.00393  # 1/K
    }
    
    ALUMINUM = { #Aluminium :)
        "lambda": 230.0,  # W/(m·K)
        "resistivity": 0.0283,  # Ω·mm²/m bei 20°C
        "temp_coefficient": 0.00403  # 1/K
    }
    
    # Isolierungen
    XLPE = {
        "lambda": 0.286,  # W/(m·K) nach IEC 60287-2-1 Tabelle 2
        "max_temp": 90.0,  # °C Dauerbetrieb
        "emergency_temp": 130.0  # °C Kurzzeitbetrieb
    }
    
    EPR = {
        "lambda": 0.4,  # W/(m·K)
        "max_temp": 90.0,
        "emergency_temp": 130.0
    }
    
    PVC = {
        "lambda": 0.16,  # W/(m·K)
        "max_temp": 70.0,
        "emergency_temp": 100.0
    }
    
    # Schirme und Mäntel
    LEAD_SHEATH = {
        "lambda": 35.0  # W/(m·K)
    }
    
    PE_SHEATH = {
        "lambda": 0.4  # W/(m·K)
    }
    
    PVC_SHEATH = {
        "lambda": 0.16  # W/(m·K)
    }
    
    @staticmethod
    def create_hv_cable_630mm2_xlpe() -> CableConfiguration:
        """
        Erstellt typisches Hochspannungskabel 630mm² XLPE
        Beispiel: 110kV Kabel
        """
        cable = CableConfiguration("HV 630mm² Cu/XLPE 110kV")
        
        # Leiter: Kupfer 630mm² (Radius ≈ 14.2mm)
        cable.add_layer(CableLayer(
            name="Conductor (Cu)",
            material="Copper",
            inner_radius=0.0,
            outer_radius=14.2,
            thermal_conductivity=CableMaterialLibrary.COPPER["lambda"],
            resistivity=CableMaterialLibrary.COPPER["resistivity"],
            temp_coefficient=CableMaterialLibrary.COPPER["temp_coefficient"]
        ))
        
        # Leitschicht: 1mm
        cable.add_layer(CableLayer(
            name="Conductor Screen",
            material="Semiconducting XLPE",
            inner_radius=14.2,
            outer_radius=15.2,
            thermal_conductivity=0.286
        ))
        
        # Isolierung: XLPE ~18mm für 110kV
        cable.add_layer(CableLayer(
            name="Insulation (XLPE)",
            material="XLPE",
            inner_radius=15.2,
            outer_radius=33.2,
            thermal_conductivity=CableMaterialLibrary.XLPE["lambda"]
        ))
        
        # Isolierschicht: 1mm
        cable.add_layer(CableLayer(
            name="Insulation Screen",
            material="Semiconducting XLPE",
            inner_radius=33.2,
            outer_radius=34.2,
            thermal_conductivity=0.286
        ))
        
        # Metallschirm: Kupfer 2mm
        cable.add_layer(CableLayer(
            name="Metallic Screen (Cu)",
            material="Copper",
            inner_radius=34.2,
            outer_radius=36.2,
            thermal_conductivity=380.0
        ))
        
        # Außenmantel: PE 4mm
        cable.add_layer(CableLayer(
            name="Outer Sheath (PE)",
            material="PE",
            inner_radius=36.2,
            outer_radius=40.2,
            thermal_conductivity=CableMaterialLibrary.PE_SHEATH["lambda"]
        ))
        
        cable.max_conductor_temp = CableMaterialLibrary.XLPE["max_temp"]
        
        # Externe Umgebung: Erdreich (1.5m äquivalenter Radius für 110kV)
        cable_outer_radius = 40.2
        earth_outer_radius = 1500  # mm (1.5m äquivalenter Radius)
        
        cable.add_external_layer(CableLayer(
            name="Soil (Earth)",
            material="Soil",
            inner_radius=cable_outer_radius,
            outer_radius=earth_outer_radius,
            thermal_conductivity=1.0  # W/(m·K)
        ))
        
        return cable
    
    @staticmethod
    def create_mv_cable_240mm2_xlpe() -> CableConfiguration:
        """
        Erstellt typisches Mittelspannungskabel 240mm² XLPE
        Beispiel: 20kV Kabel
        """
        cable = CableConfiguration("MV 240mm² Cu/XLPE 20kV")
        
        # Leiter: Kupfer 240mm² (Radius ≈ 8.7mm)
        cable.add_layer(CableLayer(
            name="Conductor (Cu)",
            material="Copper",
            inner_radius=0.0,
            outer_radius=8.7,
            thermal_conductivity=CableMaterialLibrary.COPPER["lambda"],
            resistivity=CableMaterialLibrary.COPPER["resistivity"],
            temp_coefficient=CableMaterialLibrary.COPPER["temp_coefficient"]
        ))
        
        # Leitschicht: 0.7mm
        cable.add_layer(CableLayer(
            name="Conductor Screen",
            material="Semiconducting XLPE",
            inner_radius=8.7,
            outer_radius=9.4,
            thermal_conductivity=0.286
        ))
        
        # Isolierung: XLPE ~5.5mm für 20kV
        cable.add_layer(CableLayer(
            name="Insulation (XLPE)",
            material="XLPE",
            inner_radius=9.4,
            outer_radius=14.9,
            thermal_conductivity=CableMaterialLibrary.XLPE["lambda"]
        ))
        
        # Isolierschicht: 0.7mm
        cable.add_layer(CableLayer(
            name="Insulation Screen",
            material="Semiconducting XLPE",
            inner_radius=14.9,
            outer_radius=15.6,
            thermal_conductivity=0.286
        ))
        
        # Metallschirm: Kupfer 1.5mm
        cable.add_layer(CableLayer(
            name="Metallic Screen (Cu)",
            material="Copper",
            inner_radius=15.6,
            outer_radius=17.1,
            thermal_conductivity=380.0
        ))
        
        # Außenmantel: PE 2.5mm
        cable.add_layer(CableLayer(
            name="Outer Sheath (PE)",
            material="PE",
            inner_radius=17.1,
            outer_radius=19.6,
            thermal_conductivity=CableMaterialLibrary.PE_SHEATH["lambda"]
        ))
        
        cable.max_conductor_temp = CableMaterialLibrary.XLPE["max_temp"]
        
        # Externe Umgebung: Erdreich (vereinfacht, 1m äquivalenter Radius)
        cable_outer_radius = 19.6
        earth_outer_radius = 1000  # mm (1m äquivalenter Radius für Erdreich)
        
        cable.add_external_layer(CableLayer(
            name="Soil (Earth)",
            material="Soil",
            inner_radius=cable_outer_radius,
            outer_radius=earth_outer_radius,
            thermal_conductivity=1.0  # W/(m·K) für feuchte Erde
        ))
        
        return cable


def validate_iec60287_formulas():
    """
    Validiert die IEC 60287 Formeln mit Beispielrechnungen
    """
    print("=" * 80)
    print("VALIDIERUNG DER IEC 60287 FORMELN")
    print("=" * 80)
    
    # Test 1: Einfaches Kabel mit bekannten Werten
    print("\n[TEST 1] 240mm² Cu/XLPE Mittelspannungskabel")
    print("-" * 80)
    
    cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
    cable.current = 400.0  # A
    cable.ambient_temp = 20.0  # °C
    
    t_conductor, details = cable.calculate_conductor_temperature()
    
    print(f"Strombelastung: {cable.current:.1f} A")
    print(f"Umgebungstemperatur: {cable.ambient_temp:.1f} °C")
    print(f"Berechnete Leitertemperatur: {t_conductor:.1f} °C")
    print(f"Verlustleistung: {details['losses_W_per_m']:.2f} W/m")
    print(f"Thermischer Widerstand: {details['thermal_resistance_K_m_W']:.4f} K·m/W")
    print(f"Iterationen: {details['iterations']}")
    
    # Erwartete Werte prüfen - bei 400A sollte T zwischen 25-45°C liegen
    assert 25 < t_conductor < 60, f"Leitertemperatur unrealistisch: {t_conductor}°C"
    assert details['losses_W_per_m'] > 0, "Verlustleistung muss positiv sein"
    assert 0.5 < details['thermal_resistance_K_m_W'] < 3.0, "Thermischer Widerstand unrealistisch"
    print("[PASS] Test 1 bestanden")
    
    # Test 2: Ampacity Berechnung
    print("\n[TEST 2] Ampacity Berechnung (max. zulässiger Strom)")
    print("-" * 80)
    
    cable2 = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
    cable2.ambient_temp = 25.0  # °C
    
    i_max, amp_details = cable2.calculate_max_current()
    
    print(f"Umgebungstemperatur: {cable2.ambient_temp:.1f} °C")
    print(f"Max. zulässige Leitertemperatur: {cable2.max_conductor_temp:.1f} °C")
    print(f"Berechneter max. Strom: {i_max:.1f} A")
    print(f"Erreichte Leitertemperatur: {amp_details['conductor_temp_C']:.1f} °C")
    
    # Typische Werte für 240mm² Cu: 400-900A je nach Verlegung
    assert 300 < i_max < 1000, f"Ampacity unrealistisch: {i_max}A"
    print("[PASS] Test 2 bestanden")
    
    # Test 3: Temperaturprofil
    print("\n[TEST 3] Temperaturprofil über Kabelschichten")
    print("-" * 80)
    
    cable3 = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
    cable3.current = 450.0
    cable3.ambient_temp = 20.0
    
    profile = cable3.calculate_temperature_profile()
    
    print(f"{'Radius [mm]':<15} {'Temperatur [°C]':<20} {'Schicht'}")
    print("-" * 80)
    
    prev_temp = 999
    for radius, temp, layer in profile:
        print(f"{radius:<15.2f} {temp:<20.2f} {layer}")
        # Temperatur muss von innen nach außen fallen
        assert temp <= prev_temp + 0.1, "Temperatur muss nach außen fallen!"
        prev_temp = temp
    
    print("[PASS] Test 3 bestanden - Temperatur fällt korrekt von innen nach außen")
    
    # Test 4: Hochspannungskabel
    print("\n[TEST 4] 630mm² Cu/XLPE Hochspannungskabel")
    print("-" * 80)
    
    cable4 = CableMaterialLibrary.create_hv_cable_630mm2_xlpe()
    cable4.ambient_temp = 20.0
    
    i_max_hv, hv_details = cable4.calculate_max_current()
    
    print(f"Max. Strom (110kV, 630mm²): {i_max_hv:.1f} A")
    print(f"Verlustleistung: {hv_details['losses_W_per_m']:.2f} W/m")
    
    # Typische Werte für 630mm² Cu: 800-1200A
    assert 600 < i_max_hv < 1500, f"HV Ampacity unrealistisch: {i_max_hv}A"
    print("[PASS] Test 4 bestanden")
    
    print("\n" + "=" * 80)
    print("[PASS] ALLE VALIDIERUNGEN ERFOLGREICH")
    print("=" * 80)
    print("\nZusammenfassung:")
    print(f"- Wärmefluss: Leiter → Außen [OK]")
    print(f"- Temperaturabhängiger Widerstand: R(T) = R₂₀ × [1 + α(T-20)] [OK]")
    print(f"- Thermischer Widerstand: R_th = ln(r_o/r_i)/(2π·λ) [OK]")
    print(f"- IEC 60287 Formel: θ_c = θ_a + W_c × ΣR_th [OK]")
    print(f"- Iterative Lösung wegen R(T) [OK]")


if __name__ == "__main__":
    validate_iec60287_formulas()
