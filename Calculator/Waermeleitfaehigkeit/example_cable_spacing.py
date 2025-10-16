"""
Beispiel: Kabelabstand-Optimierung für HVDC-Projekte
Demonstriert die neuen Features zur Mehrfachkabel-Analyse

Basiert auf: Grundlagen_Waermetransportberechnung_Optimierung-Kabelabstand_RML_GAE2.pdf
"""

from cable_model_iec60287 import CableMaterialLibrary
from cable_spacing_optimization import (
    CableGroupConfiguration, 
    CableSpacingAnalyzer,
    MutualHeatingModel
)
import numpy as np
import matplotlib.pyplot as plt


def example_1_three_cables_in_row():
    """
    Beispiel 1: Drei Kabel in einer Reihe
    Vergleich verschiedener Abstände
    """
    print("\n" + "="*70)
    print("BEISPIEL 1: Drei 240mm² Kabel in einer Reihe")
    print("="*70)
    
    # Konfiguration
    spacings = [0.3, 0.5, 0.75, 1.0, 1.5, 2.0]
    results = []
    
    for spacing in spacings:
        group = CableGroupConfiguration(soil_resistivity=1.0, ambient_temp=20)
        
        # Drei identische Kabel
        for i in range(3):
            cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
            cable.current = 400  # 400A Belastung
            group.add_cable(x=i*spacing, y=1.0, cable_config=cable)
        
        # Berechne Temperaturen
        temps = group.calculate_conductor_temperatures_with_mutual_heating()
        
        max_temp = max(t[1] for t in temps)
        max_mutual = max(t[2] for t in temps)
        
        results.append({
            'spacing': spacing,
            'max_temp': max_temp,
            'max_mutual_heating': max_mutual
        })
        
        print(f"\nAbstand {spacing:.2f}m:")
        print(f"  Maximale Leitertemperatur: {max_temp:.1f}°C")
        print(f"  Maximale gegenseitige Erwärmung: {max_mutual:.1f}K")
        for idx, temp, mutual in temps:
            print(f"    Kabel {idx+1}: {temp:.1f}°C (gegenseitig: +{mutual:.1f}K)")
    
    # Visualisierung
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    spacings_plot = [r['spacing'] for r in results]
    max_temps = [r['max_temp'] for r in results]
    mutual_heating = [r['max_mutual_heating'] for r in results]
    
    ax1.plot(spacings_plot, max_temps, 'o-', color='#FF6600', linewidth=2, markersize=8)
    ax1.axhline(y=90, color='red', linestyle='--', label='Max. zulässig (90°C)')
    ax1.set_xlabel('Kabelabstand [m]', fontsize=12)
    ax1.set_ylabel('Maximale Leitertemperatur [°C]', fontsize=12)
    ax1.set_title('Temperatur vs. Kabelabstand', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    ax2.plot(spacings_plot, mutual_heating, 's-', color='#CC5200', linewidth=2, markersize=8)
    ax2.set_xlabel('Kabelabstand [m]', fontsize=12)
    ax2.set_ylabel('Gegenseitige Erwärmung [K]', fontsize=12)
    ax2.set_title('Mutual Heating vs. Kabelabstand', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('cable_spacing_analysis.png', dpi=150)
    print("\n[SAVED] Grafik gespeichert: cable_spacing_analysis.png")


def example_2_optimization():
    """
    Beispiel 2: Automatische Optimierung des Kabelabstands
    """
    print("\n" + "="*70)
    print("BEISPIEL 2: Automatische Kabelabstand-Optimierung")
    print("="*70)
    
    group = CableGroupConfiguration(soil_resistivity=1.0, ambient_temp=20)
    
    # Vier Kabel mit unterschiedlichen Belastungen
    currents = [500, 500, 500, 500]
    
    for i, current in enumerate(currents):
        cable = CableMaterialLibrary.create_hv_cable_630mm2_xlpe()
        cable.current = current
        group.add_cable(x=0, y=1.5, cable_config=cable, load_factor=current/1000)
    
    print(f"\n{len(currents)} Kabel @ {currents[0]}A")
    print(f"Verlegetiefe: 1.5m")
    print(f"Bodenwärmewiderstand: 1.0 K·m/W")
    
    # Optimierung durchführen
    optimization = group.optimize_cable_spacing(
        max_conductor_temp=90.0,
        min_spacing=0.3,
        max_spacing=3.0,
        spacing_increment=0.1
    )
    
    print(f"\nOptimierungsergebnis:")
    print(f"  Optimaler Kabelabstand: {optimization['optimal_spacing']:.2f}m")
    print(f"  Temperaturreserve: {optimization['temp_margin']:.1f}K")
    
    # Zeige Details
    optimal_result = None
    for result in optimization['all_results']:
        if result['spacing'] == optimization['optimal_spacing']:
            optimal_result = result
            break
    
    if optimal_result:
        print(f"\n  Bei optimalem Abstand:")
        for idx, temp, mutual in optimal_result['all_temps']:
            print(f"    Kabel {idx+1}: {temp:.1f}°C (gegenseitig: +{mutual:.1f}K)")


def example_3_grouping_factors():
    """
    Beispiel 3: Gruppenfaktoren für verschiedene Konfigurationen
    """
    print("\n" + "="*70)
    print("BEISPIEL 3: Gruppenfaktoren (Derating Factors)")
    print("="*70)
    
    cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
    cable.current = 600
    
    configurations = [
        (2, 0.5, "Zwei Kabel, 0.5m Abstand"),
        (3, 0.5, "Drei Kabel, 0.5m Abstand"),
        (3, 1.0, "Drei Kabel, 1.0m Abstand"),
        (4, 0.5, "Vier Kabel, 0.5m Abstand"),
        (4, 1.0, "Vier Kabel, 1.0m Abstand"),
    ]
    
    print("\nGruppenfaktoren für verschiedene Konfigurationen:")
    print("-" * 70)
    
    for num_cables, spacing, description in configurations:
        factor = CableSpacingAnalyzer.analyze_grouping_factor(
            num_cables=num_cables,
            spacing=spacing,
            depth=1.0,
            cable_config=cable,
            soil_resistivity=1.0
        )
        
        derating_percent = (1 - factor) * 100
        print(f"{description:40s} → Faktor: {factor:.3f} (Derating: {derating_percent:.1f}%)")


def example_4_compare_layouts():
    """
    Beispiel 4: Vergleich verschiedener Verlegeanordnungen
    """
    print("\n" + "="*70)
    print("BEISPIEL 4: Vergleich von Verlegeanordnungen")
    print("="*70)
    
    configs = []
    
    # Layout 1: Horizontal in einer Reihe
    group1 = CableGroupConfiguration(soil_resistivity=1.0, ambient_temp=20)
    for i in range(3):
        cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
        cable.current = 500
        group1.add_cable(x=i*0.5, y=1.0, cable_config=cable)
    configs.append(("Horizontal (0.5m Abstand)", group1))
    
    # Layout 2: Horizontal mit größerem Abstand
    group2 = CableGroupConfiguration(soil_resistivity=1.0, ambient_temp=20)
    for i in range(3):
        cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
        cable.current = 500
        group2.add_cable(x=i*1.0, y=1.0, cable_config=cable)
    configs.append(("Horizontal (1.0m Abstand)", group2))
    
    # Layout 3: Dreieck-Formation
    group3 = CableGroupConfiguration(soil_resistivity=1.0, ambient_temp=20)
    positions = [(0, 1.0), (0.5, 1.0), (0.25, 1.3)]
    for x, y in positions:
        cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
        cable.current = 500
        group3.add_cable(x=x, y=y, cable_config=cable)
    configs.append(("Dreieck-Formation", group3))
    
    # Vergleich
    comparison = CableSpacingAnalyzer.compare_configurations(configs)
    
    print("\nVergleich der Verlegeanordnungen:")
    print("-" * 70)
    
    for name, results in comparison.items():
        print(f"\n{name}:")
        print(f"  Maximale Temperatur: {results['max_temp']:.1f}°C")
        print(f"  Durchschnittstemperatur: {results['avg_temp']:.1f}°C")
        print(f"  Maximale gegenseitige Erwärmung: {results['max_mutual_heating']:.1f}K")


def main():
    """Führt alle Beispiele aus"""
    print("\n" + "="*70)
    print("KABELABSTAND-OPTIMIERUNG - DEMONSTRATIONSBEISPIELE")
    print("ARCADIS - Basierend auf IEC 60287-2-1")
    print("="*70)
    
    example_1_three_cables_in_row()
    example_2_optimization()
    example_3_grouping_factors()
    example_4_compare_layouts()
    
    print("\n" + "="*70)
    print("ALLE BEISPIELE ABGESCHLOSSEN")
    print("="*70)


if __name__ == "__main__":
    main()
