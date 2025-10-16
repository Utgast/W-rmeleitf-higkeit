"""
Enhanced Cable Model - Erweiterte Kabelberechnung
Kombiniert IEC 60287 mit erweiterten physikalischen Modellen

Neue Features:
- Konvektion und Strahlung für Luftverlegung
- Transiente Berechnungen
- Skin- und Proximity-Effekte
- Schirmverluste
- Mehrere Kabel und Gruppenfaktoren
- Verlegearten und Bodenfeuchte
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np

from cable_model_iec60287 import CableLayer, CableConfiguration
from advanced_thermal_physics import (
    ConvectionModel, RadiationModel, SkinEffectModel, 
    ProximityEffectModel, TransientThermalModel, ShieldLossModel,
    InstallationFactors, ConvectionParameters, RadiationParameters
)


@dataclass
class EnhancedCableConfiguration(CableConfiguration):
    """Erweiterte Kabelkonfiguration mit zusätzlichen Parametern"""
    
    # Basis-Eigenschaften (geerbt von CableConfiguration, aber explizit deklariert)
    layers: List[CableLayer] = field(default_factory=list)
    external_layers: List[CableLayer] = field(default_factory=list)
    current: float = 0.0
    ambient_temp: float = 20.0
    
    # Erweiterte Umgebungsbedingungen
    convection_params: Optional[ConvectionParameters] = None
    radiation_params: Optional[RadiationParameters] = None
    
    # AC-spezifische Parameter
    frequency: float = 50.0  # Hz
    phase_angle: float = 0.0  # Grad (für Proximity-Effekt)
    
    # Gruppierung
    num_cables: int = 1
    cable_spacing: float = 0.5  # m
    installation_method: str = 'direct_buried'  # 'direct_buried', 'in_duct', 'in_air'
    
    # Boden/Umgebung
    soil_type: str = 'sand'
    soil_moisture: float = 0.1  # 0-1
    burial_depth: float = 1.0  # m
    
    # Schirm
    has_shield: bool = False
    shield_resistance: float = 0.0  # Ohm/m
    shield_radius: float = 0.0  # m
    
    # Transiente Berechnung
    enable_transient: bool = False
    thermal_capacitance: float = 0.0  # J/K (wird berechnet wenn 0)
    
    def calculate_enhanced_losses(self, current: float, temperature: float) -> dict:
        """
        Berechnet erweiterte Verluste inkl. Skin-Effekt, Proximity, Schirm
        
        Returns:
            dict mit verschiedenen Verlustkomponenten
        """
        results = {}
        
        # Basis-Leiterverluste (DC)
        conductor = self.layers[0]
        r_dc = conductor.get_electrical_resistance(temperature)
        losses_dc = current**2 * r_dc
        results['losses_dc'] = losses_dc
        
        # Skin-Effekt
        if self.frequency > 0:
            r_ac = SkinEffectModel.calculate_ac_resistance(
                r_dc=r_dc,
                conductor_radius=conductor.outer_radius / 1000,  # mm -> m
                frequency=self.frequency,
                resistivity=conductor.resistivity
            )
            losses_ac = current**2 * r_ac
            results['losses_ac'] = losses_ac
            results['skin_factor'] = r_ac / r_dc if r_dc > 0 else 1.0
        else:
            results['losses_ac'] = losses_dc
            results['skin_factor'] = 1.0
        
        # Proximity-Effekt
        if self.num_cables > 1:
            k_proximity = ProximityEffectModel.calculate_proximity_factor(
                conductor_radius=conductor.outer_radius / 1000,
                axis_distance=self.cable_spacing,
                num_conductors=self.num_cables
            )
            losses_proximity = results['losses_ac'] * k_proximity
            results['losses_proximity'] = losses_proximity
            results['proximity_factor'] = k_proximity
        else:
            results['losses_proximity'] = results['losses_ac']
            results['proximity_factor'] = 1.0
        
        # Schirmverluste
        if self.has_shield and self.shield_radius > 0:
            mutual_inductance = ShieldLossModel.calculate_mutual_inductance(
                conductor_radius=conductor.outer_radius / 1000,
                shield_radius=self.shield_radius / 1000
            )
            shield_losses = ShieldLossModel.calculate_shield_losses(
                conductor_current=current,
                shield_resistance=self.shield_resistance,
                mutual_inductance=mutual_inductance,
                frequency=self.frequency
            )
            results['losses_shield'] = shield_losses
        else:
            results['losses_shield'] = 0.0
        
        # Gesamtverluste
        results['losses_total'] = (results['losses_proximity'] + 
                                  results['losses_shield'])
        
        return results
    
    def calculate_enhanced_thermal_resistance(self) -> dict:
        """
        Berechnet erweiterte thermische Widerstände inkl. Konvektion und Strahlung
        """
        results = {}
        
        # Basis: Konduktion durch Kabelschichten
        r_conduction = sum(layer.get_thermal_resistance() for layer in self.layers)
        results['r_conduction'] = r_conduction
        
        # Externe Schichten (Boden)
        r_external = sum(layer.get_thermal_resistance() for layer in self.external_layers)
        results['r_external'] = r_external
        
        # Konvektion (für Luftverlegung)
        if self.installation_method == 'in_air' and self.convection_params:
            # Annahme: Oberflächentemperatur = Manteltemperatur (wird iteriert)
            surface_temp = self.ambient_temp + 20  # Erste Schätzung
            
            h_conv = ConvectionModel.calculate_heat_transfer_coefficient(
                self.convection_params, surface_temp
            )
            
            # Umrechnung in thermischen Widerstand
            outer_radius = self.layers[-1].outer_radius / 1000  # mm -> m
            surface_area = 2 * math.pi * outer_radius * 1.0  # pro Meter
            
            if h_conv > 0:
                r_convection = 1 / (h_conv * surface_area)
            else:
                r_convection = 10.0  # Fallback
            
            results['r_convection'] = r_convection
        else:
            results['r_convection'] = 0.0
        
        # Strahlung
        if self.installation_method == 'in_air' and self.radiation_params:
            surface_temp = self.ambient_temp + 20
            
            h_rad = RadiationModel.calculate_radiation_coefficient(
                self.radiation_params, surface_temp
            )
            
            outer_radius = self.layers[-1].outer_radius / 1000
            surface_area = 2 * math.pi * outer_radius * 1.0
            
            if h_rad > 0:
                r_radiation = 1 / (h_rad * surface_area)
            else:
                r_radiation = 100.0
            
            results['r_radiation'] = r_radiation
        else:
            results['r_radiation'] = 0.0
        
        # Parallele Widerstände für Konvektion und Strahlung
        if results['r_convection'] > 0 or results['r_radiation'] > 0:
            if results['r_convection'] > 0 and results['r_radiation'] > 0:
                r_parallel = 1 / (1/results['r_convection'] + 1/results['r_radiation'])
            elif results['r_convection'] > 0:
                r_parallel = results['r_convection']
            else:
                r_parallel = results['r_radiation']
            
            results['r_external_enhanced'] = r_parallel
        else:
            results['r_external_enhanced'] = r_external
        
        # Verlegefaktoren
        grouping_factor = InstallationFactors.get_grouping_factor(
            self.num_cables,
            self.cable_spacing / (2 * self.layers[-1].outer_radius / 1000)
        )
        
        installation_factor = InstallationFactors.get_installation_method_factor(
            self.installation_method
        )
        
        results['grouping_factor'] = grouping_factor
        results['installation_factor'] = installation_factor
        
        # Effektiver thermischer Bodenwiderstand
        soil_thermal_resistivity = InstallationFactors.get_soil_thermal_resistivity(
            self.soil_type, self.soil_moisture
        )
        results['soil_thermal_resistivity'] = soil_thermal_resistivity
        
        # Gesamtwiderstand
        if self.installation_method == 'in_air':
            r_total = r_conduction + results['r_external_enhanced']
        else:
            # Bodenwiderstand für vergrabene Kabel (vereinfacht)
            r_soil = soil_thermal_resistivity / (2 * math.pi) * math.log(
                2 * self.burial_depth / (self.layers[-1].outer_radius / 1000)
            )
            results['r_soil'] = r_soil
            r_total = r_conduction + r_soil
        
        # Gruppenfaktor anwenden
        r_total = r_total / (grouping_factor * installation_factor)
        results['r_total'] = r_total
        
        return results
    
    def calculate_conductor_temperature_enhanced(self) -> dict:
        """
        Erweiterte Leitertemperaturberechnung mit allen Effekten
        """
        results = {}
        
        # Iteration für gekoppelte Berechnungen
        t_conductor = self.ambient_temp + 50  # Startwert
        
        for iteration in range(20):
            # Verluste berechnen
            loss_results = self.calculate_enhanced_losses(self.current, t_conductor)
            losses_total = loss_results['losses_total']
            
            # Thermische Widerstände
            thermal_results = self.calculate_enhanced_thermal_resistance()
            r_total = thermal_results['r_total']
            
            # Neue Leitertemperatur
            t_new = self.ambient_temp + losses_total * r_total
            
            # Konvergenzprüfung
            if abs(t_new - t_conductor) < 0.05:
                t_conductor = t_new
                break
            
            t_conductor = 0.5 * t_new + 0.5 * t_conductor  # Dämpfung
        
        # Ergebnisse zusammenstellen
        results.update(loss_results)
        results.update(thermal_results)
        results['conductor_temperature'] = t_conductor
        results['temperature_rise'] = t_conductor - self.ambient_temp
        results['iterations'] = iteration + 1
        
        return results
    
    def calculate_ampacity_enhanced(self, max_temp: float = 90.0) -> dict:
        """
        Berechnet Strombelastbarkeit mit erweiterten Modellen
        """
        # Binäre Suche
        i_min, i_max = 0.0, 10000.0
        
        for iteration in range(30):
            i_test = (i_min + i_max) / 2
            self.current = i_test
            
            result = self.calculate_conductor_temperature_enhanced()
            t_cond = result['conductor_temperature']
            
            if abs(t_cond - max_temp) < 0.1:
                break
            
            if t_cond > max_temp:
                i_max = i_test
            else:
                i_min = i_test
        
        result['ampacity'] = i_test
        result['max_temperature'] = max_temp
        
        return result
    
    def calculate_transient_response(self, duration: float = 3600, 
                                    time_steps: int = 100) -> dict:
        """
        Berechnet zeitabhängige Erwärmung
        """
        if self.thermal_capacitance == 0:
            # Berechne thermische Kapazität
            self.thermal_capacitance = TransientThermalModel.calculate_thermal_capacitance(
                self.layers
            )
        
        # Stationäre Endtemperatur
        steady_result = self.calculate_conductor_temperature_enhanced()
        t_final = steady_result['conductor_temperature']
        r_total = steady_result['r_total']
        
        # Zeitkonstante
        tau = TransientThermalModel.calculate_time_constant(
            r_total, self.thermal_capacitance
        )
        
        # Aufheizkurve
        times, temps = TransientThermalModel.calculate_heating_curve(
            self.ambient_temp,
            steady_result['losses_total'],
            r_total,
            self.thermal_capacitance,
            time_steps,
            duration
        )
        
        return {
            'times': times.tolist(),
            'temperatures': temps.tolist(),
            'time_constant': tau,
            'steady_state_temp': t_final,
            'thermal_capacitance': self.thermal_capacitance
        }


def create_enhanced_mv_cable_in_air(current: float = 400, ambient_temp: float = 25,
                                   air_velocity: float = 1.0) -> EnhancedCableConfiguration:
    """Erstellt MV-Kabel für Luftverlegung mit Konvektion und Strahlung"""
    
    # Materialparameter direkt definieren
    layers = [
        CableLayer("Leiter (Cu)", "Kupfer", 0, 9.79, 380, 0.01724, 0.00393),
        CableLayer("Leiter-Halbleiter", "XLPE", 9.79, 11.29, 0.286),
        CableLayer("Isolierung (XLPE)", "XLPE", 11.29, 20.79, 0.286),
        CableLayer("Isolierungs-Halbleiter", "XLPE", 20.79, 22.29, 0.286),
        CableLayer("Kupferschirm", "Kupfer", 22.29, 23.29, 380),
        CableLayer("Außenmantel (PVC)", "PVC", 23.29, 25.79, 0.16),
    ]
    
    conv_params = ConvectionParameters(
        air_velocity=air_velocity,
        air_temp=ambient_temp,
        characteristic_length=0.052  # 2 * 25.79mm
    )
    
    rad_params = RadiationParameters(
        emissivity=0.9,
        surrounding_temp=ambient_temp
    )
    
    return EnhancedCableConfiguration(
        layers=layers,
        external_layers=[],
        current=current,
        ambient_temp=ambient_temp,
        convection_params=conv_params,
        radiation_params=rad_params,
        installation_method='in_air',
        frequency=50.0,
        has_shield=True,
        shield_resistance=0.0001,
        shield_radius=23.29
    )


# Validierung
def validate_enhanced_model():
    """Validiert erweitertes Modell"""
    
    print("\n=== VALIDIERUNG ERWEITERTES KABELMODELL ===\n")
    
    # Test 1: Kabel in Luft mit Konvektion
    print("Test 1: 240mm² MV-Kabel in Luft (1 m/s Wind)")
    cable_air = create_enhanced_mv_cable_in_air(400, 25, 1.0)
    result = cable_air.calculate_conductor_temperature_enhanced()
    
    print(f"Leitertemperatur: {result['conductor_temperature']:.1f}°C")
    print(f"Verluste DC: {result['losses_dc']:.2f} W/m")
    print(f"Verluste AC (Skin): {result['losses_ac']:.2f} W/m")
    print(f"Skin-Faktor: {result['skin_factor']:.3f}")
    print(f"R_konduktion: {result['r_conduction']:.3f} K·m/W")
    print(f"R_konvektion: {result['r_convection']:.3f} K·m/W")
    print(f"R_strahlung: {result['r_radiation']:.3f} K·m/W")
    print(f"R_gesamt: {result['r_total']:.3f} K·m/W")
    print(f"Iterationen: {result['iterations']}")
    print()
    
    # Test 2: Ampacity
    print("Test 2: Strombelastbarkeit mit erweiterten Modellen")
    ampacity_result = cable_air.calculate_ampacity_enhanced(90.0)
    print(f"Ampacity bei 90°C: {ampacity_result['ampacity']:.0f} A")
    print()
    
    # Test 3: Transiente Berechnung
    print("Test 3: Transiente Erwärmung")
    cable_air.current = 400
    transient = cable_air.calculate_transient_response(duration=7200, time_steps=50)
    print(f"Zeitkonstante: {transient['time_constant']/60:.1f} Minuten")
    print(f"Stationäre Temperatur: {transient['steady_state_temp']:.1f}°C")
    print(f"Temperatur nach 1h: {transient['temperatures'][25]:.1f}°C")
    print()
    
    print("=== VALIDIERUNG ABGESCHLOSSEN ===\n")


if __name__ == "__main__":
    validate_enhanced_model()
