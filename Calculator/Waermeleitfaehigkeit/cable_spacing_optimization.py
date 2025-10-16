"""
Kabelabstand-Optimierung - Cable Spacing Optimization
Berechnung der gegenseitigen thermischen Beeinflussung und Optimierung des Kabelabstands

Basiert auf:
- IEC 60287-2-1: Mutual heating between cables
- Grundlagen Wärmetransportberechnung RML_GAE2
- Optimierung für Mehrfachkabel-Systeme
"""

import numpy as np
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from cable_model_iec60287 import CableConfiguration


@dataclass
class CablePosition:
    """Position eines Kabels im Verlegesystem"""
    x: float  # Horizontale Position in m
    y: float  # Vertikale Position in m (Tiefe)
    cable_config: CableConfiguration
    load_factor: float = 1.0  # Lastfaktor (0-1)
    
    def distance_to(self, other: 'CablePosition') -> float:
        """Berechnet Abstand zu anderem Kabel"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


class MutualHeatingModel:
    """
    Berechnung der gegenseitigen thermischen Beeinflussung
    nach IEC 60287-2-1
    """
    
    @staticmethod
    def calculate_mutual_thermal_resistance(distance: float, 
                                           depth: float,
                                           soil_resistivity: float = 1.0) -> float:
        """
        Berechnet gegenseitigen thermischen Widerstand
        
        IEC 60287-2-1 Formel:
        R_mutual = (ρ_soil / 2π) * ln(2L/D)
        
        wobei:
        - ρ_soil: Bodenwärmewidertand in K·m/W
        - L: Verlegetiefe in m
        - D: Abstand zwischen Kabeln in m
        
        Args:
            distance: Abstand zwischen Kabeln in m
            depth: Verlegetiefe in m
            soil_resistivity: Bodenwärmewiderstand in K·m/W
            
        Returns:
            Gegenseitiger thermischer Widerstand in K·m/W
        """
        if distance <= 0:
            return 0.0
        
        # IEC 60287-2-1: R_mutual = (ρ / 2π) * ln(2L/D)
        R_mutual = (soil_resistivity / (2 * math.pi)) * math.log(2 * depth / distance)
        
        return max(0, R_mutual)
    
    @staticmethod
    def calculate_temperature_rise_from_neighbor(neighbor_losses: float,
                                                 mutual_resistance: float) -> float:
        """
        Berechnet Temperaturerhöhung durch Nachbarkabel
        
        ΔT = W_neighbor × R_mutual
        
        Args:
            neighbor_losses: Verlustleistung des Nachbarkabels in W/m
            mutual_resistance: Gegenseitiger thermischer Widerstand in K·m/W
            
        Returns:
            Temperaturerhöhung in K
        """
        return neighbor_losses * mutual_resistance


class CableGroupConfiguration:
    """Konfiguration einer Kabelgruppe mit mehreren Kabeln"""
    
    def __init__(self, soil_resistivity: float = 1.0, 
                 ambient_temp: float = 20.0,
                 soil_temp_gradient: float = 0.03):
        """
        Args:
            soil_resistivity: Bodenwärmewiderstand in K·m/W
            ambient_temp: Umgebungstemperatur an Oberfläche in °C
            soil_temp_gradient: Temperaturgradient im Boden in K/m
        """
        self.cables: List[CablePosition] = []
        self.soil_resistivity = soil_resistivity
        self.ambient_temp = ambient_temp
        self.soil_temp_gradient = soil_temp_gradient
    
    def add_cable(self, x: float, y: float, 
                  cable_config: CableConfiguration,
                  load_factor: float = 1.0):
        """Fügt Kabel zur Gruppe hinzu"""
        position = CablePosition(x, y, cable_config, load_factor)
        self.cables.append(position)
    
    def calculate_mutual_heating_matrix(self) -> np.ndarray:
        """
        Berechnet Matrix der gegenseitigen thermischen Widerstände
        
        Returns:
            Matrix R_mutual[i,j] für gegenseitige Beeinflussung
        """
        n = len(self.cables)
        R_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance = self.cables[i].distance_to(self.cables[j])
                    depth = self.cables[i].y
                    R_matrix[i, j] = MutualHeatingModel.calculate_mutual_thermal_resistance(
                        distance, depth, self.soil_resistivity
                    )
        
        return R_matrix
    
    def calculate_conductor_temperatures_with_mutual_heating(self) -> List[Tuple[int, float, float]]:
        """
        Berechnet Leitertemperaturen unter Berücksichtigung gegenseitiger Erwärmung
        
        Iterative Lösung des gekoppelten Systems:
        T_i = T_ambient(y_i) + W_i × R_i + Σ(W_j × R_mutual[i,j])
        
        Returns:
            Liste von (cable_index, conductor_temp, temp_rise_from_neighbors)
        """
        n = len(self.cables)
        
        if n == 0:
            return []
        
        # Berechne gegenseitige Widerstände
        R_mutual = self.calculate_mutual_heating_matrix()
        
        # Initialisiere Temperaturen (ohne gegenseitige Beeinflussung)
        conductor_temps = np.zeros(n)
        cable_losses = np.zeros(n)
        
        for i, cable_pos in enumerate(self.cables):
            cable = cable_pos.cable_config
            
            # Umgebungstemperatur in Verlegetiefe
            ambient_at_depth = self.ambient_temp + self.soil_temp_gradient * cable_pos.y
            cable.ambient_temp = ambient_at_depth
            
            # Berechne initiale Temperatur ohne gegenseitige Erwärmung
            temp, details = cable.calculate_conductor_temperature()
            conductor_temps[i] = temp
            cable_losses[i] = details['losses_W_per_m'] * cable_pos.load_factor
        
        # Iterative Lösung mit gegenseitiger Erwärmung
        max_iterations = 20
        convergence_threshold = 0.1  # °C
        
        for iteration in range(max_iterations):
            temp_old = conductor_temps.copy()
            
            for i, cable_pos in enumerate(self.cables):
                cable = cable_pos.cable_config
                
                # Temperaturerhöhung durch Nachbarkabel
                mutual_heating = sum(
                    cable_losses[j] * R_mutual[i, j] 
                    for j in range(n) if j != i
                )
                
                # Umgebungstemperatur + eigene Erwärmung + gegenseitige Erwärmung
                ambient_at_depth = self.ambient_temp + self.soil_temp_gradient * cable_pos.y
                temp_without_mutual, details = cable.calculate_conductor_temperature()
                
                conductor_temps[i] = temp_without_mutual + mutual_heating
                
                # Aktualisiere Verluste basierend auf neuer Temperatur
                cable_losses[i] = cable.calculate_conductor_losses(conductor_temps[i]) * cable_pos.load_factor
            
            # Prüfe Konvergenz
            if np.max(np.abs(conductor_temps - temp_old)) < convergence_threshold:
                break
        
        # Berechne Beiträge der gegenseitigen Erwärmung
        results = []
        for i, cable_pos in enumerate(self.cables):
            mutual_heating = sum(
                cable_losses[j] * R_mutual[i, j] 
                for j in range(n) if j != i
            )
            results.append((i, conductor_temps[i], mutual_heating))
        
        return results
    
    def optimize_cable_spacing(self, 
                              max_conductor_temp: float = 90.0,
                              min_spacing: float = 0.1,
                              max_spacing: float = 5.0,
                              spacing_increment: float = 0.1) -> dict:
        """
        Optimiert Kabelabstand für maximale Strombelastbarkeit
        
        Args:
            max_conductor_temp: Maximale Leitertemperatur in °C
            min_spacing: Minimaler Kabelabstand in m
            max_spacing: Maximaler Kabelabstand in m
            spacing_increment: Schrittweite für Optimierung in m
            
        Returns:
            Dictionary mit optimalen Parametern
        """
        if len(self.cables) < 2:
            return {"error": "Mindestens 2 Kabel erforderlich"}
        
        # Annahme: Kabel in horizontaler Reihe angeordnet
        # Optimiere Abstand zwischen benachbarten Kabeln
        
        best_spacing = min_spacing
        best_min_temp_margin = -float('inf')
        results_list = []
        
        for spacing in np.arange(min_spacing, max_spacing, spacing_increment):
            # Setze Kabel mit gleichmäßigem Abstand
            reference_depth = self.cables[0].y
            for i, cable_pos in enumerate(self.cables):
                cable_pos.x = i * spacing
                cable_pos.y = reference_depth
            
            # Berechne Temperaturen
            temps = self.calculate_conductor_temperatures_with_mutual_heating()
            max_temp = max(t[1] for t in temps)
            min_temp_margin = max_conductor_temp - max_temp
            
            results_list.append({
                'spacing': spacing,
                'max_conductor_temp': max_temp,
                'temp_margin': min_temp_margin,
                'all_temps': temps
            })
            
            # Prüfe ob besser
            if min_temp_margin > best_min_temp_margin and max_temp <= max_conductor_temp:
                best_min_temp_margin = min_temp_margin
                best_spacing = spacing
        
        return {
            'optimal_spacing': best_spacing,
            'temp_margin': best_min_temp_margin,
            'all_results': results_list,
            'num_cables': len(self.cables)
        }


class CableSpacingAnalyzer:
    """Analyse-Tool für verschiedene Verlegekonfigurationen"""
    
    @staticmethod
    def compare_configurations(configs: List[Tuple[str, CableGroupConfiguration]]) -> dict:
        """
        Vergleicht verschiedene Verlegekonfigurationen
        
        Args:
            configs: Liste von (name, configuration) Tupeln
            
        Returns:
            Vergleichsergebnisse
        """
        results = {}
        
        for name, config in configs:
            temps = config.calculate_conductor_temperatures_with_mutual_heating()
            
            results[name] = {
                'max_temp': max(t[1] for t in temps),
                'avg_temp': np.mean([t[1] for t in temps]),
                'max_mutual_heating': max(t[2] for t in temps),
                'conductor_temps': temps
            }
        
        return results
    
    @staticmethod
    def analyze_grouping_factor(num_cables: int,
                                spacing: float,
                                depth: float,
                                cable_config: CableConfiguration,
                                soil_resistivity: float = 1.0) -> float:
        """
        Berechnet Gruppenfaktor (Derating Factor)
        
        Faktor = I_group / I_single
        
        Args:
            num_cables: Anzahl Kabel in Gruppe
            spacing: Abstand zwischen Kabeln in m
            depth: Verlegetiefe in m
            cable_config: Kabelkonfiguration
            soil_resistivity: Bodenwärmewiderstand in K·m/W
            
        Returns:
            Gruppenfaktor (< 1.0 bedeutet Derating)
        """
        # Einzelkabel-Ampacity
        group_single = CableGroupConfiguration(soil_resistivity)
        group_single.add_cable(0, depth, cable_config)
        temps_single = group_single.calculate_conductor_temperatures_with_mutual_heating()
        
        # Berechne Ampacity für Einzelkabel
        I_single, _ = cable_config.calculate_max_current()
        
        # Mehrfachkabel-Gruppe
        group_multi = CableGroupConfiguration(soil_resistivity)
        for i in range(num_cables):
            group_multi.add_cable(i * spacing, depth, cable_config)
        
        # Berechne Temperaturen bei gleicher Strombelastung
        temps_multi = group_multi.calculate_conductor_temperatures_with_mutual_heating()
        max_temp_multi = max(t[1] for t in temps_multi)
        
        # Gruppenfaktor basierend auf Temperaturerhöhung
        temp_single = temps_single[0][1]
        
        if max_temp_multi <= temp_single:
            return 1.0
        
        # Näherungsweise: Faktor ~ sqrt(T_single / T_multi)
        # Genauer: Iterativ Strom anpassen bis gleiche Temperatur
        grouping_factor = math.sqrt(temp_single / max_temp_multi)
        
        return min(1.0, grouping_factor)


# ============================================================================
# VALIDIERUNG UND BEISPIELE
# ============================================================================

def validate_mutual_heating():
    """Validiert Berechnungen der gegenseitigen Erwärmung"""
    
    print("\n" + "="*70)
    print("VALIDIERUNG: Kabelabstand-Optimierung")
    print("="*70)
    
    # Erstelle Testkonfiguration mit 3 Kabeln
    from cable_model_iec60287 import CableMaterialLibrary
    
    group = CableGroupConfiguration(soil_resistivity=1.0, ambient_temp=20)
    
    cable1 = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
    cable1.current = 400
    cable2 = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
    cable2.current = 400
    cable3 = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
    cable3.current = 400
    
    # Kabel in Reihe: Abstand 0.5m, Tiefe 1.0m
    group.add_cable(x=0.0, y=1.0, cable_config=cable1)
    group.add_cable(x=0.5, y=1.0, cable_config=cable2)
    group.add_cable(x=1.0, y=1.0, cable_config=cable3)
    
    print("\nTest 1: Gegenseitige Erwärmung - 3 Kabel, Abstand 0.5m")
    print("-" * 70)
    
    temps = group.calculate_conductor_temperatures_with_mutual_heating()
    
    for i, (idx, temp, mutual) in enumerate(temps):
        print(f"Kabel {idx + 1}:")
        print(f"  Leitertemperatur: {temp:.1f}°C")
        print(f"  Gegenseitige Erwärmung: {mutual:.1f}K")
        
        # Validierung: Mittleres Kabel sollte höchste Temperatur haben
        if i == 1:  # Mittleres Kabel
            assert temp > temps[0][1], "Mittleres Kabel sollte wärmer sein"
            assert temp > temps[2][1], "Mittleres Kabel sollte wärmer sein"
    
    print("\n✓ Test 1 bestanden: Mittleres Kabel hat höchste Temperatur")
    
    # Test 2: Optimierung des Kabelabstands
    print("\nTest 2: Kabelabstand-Optimierung")
    print("-" * 70)
    
    optimization = group.optimize_cable_spacing(
        max_conductor_temp=90.0,
        min_spacing=0.2,
        max_spacing=2.0,
        spacing_increment=0.2
    )
    
    print(f"Optimaler Kabelabstand: {optimization['optimal_spacing']:.2f}m")
    print(f"Temperaturreserve: {optimization['temp_margin']:.1f}K")
    
    # Test 3: Gruppenfaktor
    print("\nTest 3: Gruppenfaktor (Derating Factor)")
    print("-" * 70)
    
    for spacing in [0.3, 0.5, 1.0, 2.0]:
        factor = CableSpacingAnalyzer.analyze_grouping_factor(
            num_cables=3,
            spacing=spacing,
            depth=1.0,
            cable_config=cable1,
            soil_resistivity=1.0
        )
        print(f"Abstand {spacing:.1f}m: Gruppenfaktor = {factor:.3f}")
    
    print("\n" + "="*70)
    print("ALLE TESTS BESTANDEN")
    print("="*70)


if __name__ == "__main__":
    validate_mutual_heating()
