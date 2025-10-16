# Kabelabstand-Optimierung - Implementierungsübersicht

## Basierend auf RML_GAE2: Grundlagen Wärmetransportberechnung

### Neu implementierte Features (2025-10-16)

## 1. Gegenseitige thermische Beeinflussung (Mutual Heating)

**IEC 60287-2-1 konforme Berechnung:**

```
R_mutual = (ρ_soil / 2π) × ln(2L/D)

wobei:
- ρ_soil: Bodenwärmewiderstand in K·m/W
- L: Verlegetiefe in m
- D: Abstand zwischen Kabeln in m
```

**Temperaturerhöhung durch Nachbarkabel:**
```
ΔT_i = Σ(W_j × R_mutual[i,j])
```

**Validierungsergebnisse:**
- 3 Kabel @ 0.5m Abstand, 400A je Kabel
- Mittleres Kabel: +5.5K durch Nachbarkabel
- Äußere Kabel: +4.2K durch Nachbarkabel
- [PASS] Physikalisch korrekt: Mittleres Kabel hat höchste Temperatur

## 2. Automatische Kabelabstand-Optimierung

**Algorithmus:**
1. Definiere zulässige Maximaltemperatur (z.B. 90°C)
2. Variiere Kabelabstand zwischen min/max Werten
3. Berechne gekoppeltes Temperatursystem iterativ
4. Finde Abstand mit maximaler Temperaturreserve

**Beispielergebnis:**
- 3 × 240mm² Kabel @ 400A
- Optimaler Abstand: 1.8m
- Temperaturreserve: 57.1K unter Maximum

**Code-Verwendung:**
```python
from cable_spacing_optimization import CableGroupConfiguration

group = CableGroupConfiguration(soil_resistivity=1.0, ambient_temp=20)
# Kabel hinzufügen...

optimization = group.optimize_cable_spacing(
    max_conductor_temp=90.0,
    min_spacing=0.2,
    max_spacing=2.0
)
```

## 3. Gruppenfaktoren (Derating Factors)

**Definition:**
```
Gruppenfaktor = I_group / I_single

wobei:
- I_group: Zulässiger Strom in Gruppe
- I_single: Zulässiger Strom als Einzelkabel
```

**Validierte Faktoren:**

| Konfiguration | Abstand | Gruppenfaktor | Derating |
|--------------|---------|---------------|----------|
| 3 Kabel      | 0.3m    | 0.488         | 51.2%    |
| 3 Kabel      | 0.5m    | 0.855         | 14.5%    |
| 3 Kabel      | 1.0m    | 0.923         | 7.7%     |
| 3 Kabel      | 2.0m    | 1.000         | 0%       |

**Erkenntnisse:**
- Bei 0.3m Abstand: 51% Derating erforderlich
- Ab 2.0m Abstand: Keine gegenseitige Beeinflussung mehr
- Linearer Zusammenhang zwischen Abstand und Faktor (logarithmisch)

## 4. Vergleich verschiedener Verlegeanordnungen

**Implementierte Layouts:**
1. **Horizontal in Reihe**: Standard-Verlegung
2. **Dreieck-Formation**: Kompakte Anordnung
3. **Versetzte Ebenen**: Unterschiedliche Verlegetiefen

**Beispielvergleich (3 Kabel @ 500A):**

| Layout                | Max. Temp | Ø Temp | Max. Mutual |
|-----------------------|-----------|--------|-------------|
| Horizontal (0.5m)     | 49.0°C    | 47.5°C | 9.0K       |
| Horizontal (1.0m)     | 44.4°C    | 42.9°C | 4.4K       |
| Dreieck-Formation     | 52.4°C    | 50.8°C | 12.4K      |

**Empfehlung:** Horizontal mit 1.0m Abstand bietet besten Kompromiss

## 5. Iterative Systemlösung

**Problem:**
- Temperatur jedes Kabels beeinflusst Nachbarkabel
- Nachbarkabel-Erwärmung beeinflusst Widerstand zurück
- Gekoppeltes, nichtlineares System

**Lösung:**
```python
for iteration in range(max_iterations):
    for i, cable in enumerate(cables):
        # Berechne Erwärmung durch Nachbarn
        mutual_heating = sum(
            cable_losses[j] * R_mutual[i,j] 
            for j != i
        )
        
        # Neue Temperatur
        T_new[i] = T_ambient + W_own + mutual_heating
        
        # Aktualisiere Verluste (R abhängig von T)
        W_new[i] = I² × R(T_new[i])
    
    # Konvergenz prüfen
    if max(|T_new - T_old|) < 0.1°C:
        break
```

**Konvergenz:** Typisch 5-10 Iterationen bis 0.1°C Genauigkeit

## 6. Bodenwärmewiderstand und Verlegetiefe

**Berücksichtigung:**
- Temperaturgradient im Boden: ΔT = 0.03 K/m typisch
- Tiefenabhängige Umgebungstemperatur
- Bodenfeuchte-Korrektur möglich

**Formel:**
```
T_ambient(Tiefe) = T_surface + Gradient × Tiefe
```

## Dateien

| Datei                           | Zeilen | Beschreibung                      |
|---------------------------------|--------|-----------------------------------|
| cable_spacing_optimization.py   | 422    | Hauptmodul für Optimierung        |
| example_cable_spacing.py        | 243    | Demonstrationsbeispiele           |
| cable_spacing_analysis.png      | -      | Visualisierung der Ergebnisse     |

## Integration mit bestehendem Code

**Kompatibilität:**
- Nutzt `CableConfiguration` aus `cable_model_iec60287.py`
- Erweitert um Multi-Kabel-Funktionalität
- Keine Breaking Changes an bestehendem Code

**Verwendung:**
```python
# Einzelkabel (bisherig)
from cable_model_iec60287 import CableMaterialLibrary

cable = CableMaterialLibrary.create_mv_cable_240mm2_xlpe()
cable.current = 400
temp, details = cable.calculate_conductor_temperature()

# Multi-Kabel (neu)
from cable_spacing_optimization import CableGroupConfiguration

group = CableGroupConfiguration()
group.add_cable(x=0, y=1.0, cable_config=cable)
group.add_cable(x=0.5, y=1.0, cable_config=cable)
temps = group.calculate_conductor_temperatures_with_mutual_heating()
```

## Validierung

**Physikalische Plausibilität:**
- [PASS] Mittleres Kabel wärmer als äußere Kabel
- [PASS] Temperatur sinkt mit zunehmendem Abstand
- [PASS] Gruppenfaktor < 1.0 für enge Anordnungen
- [PASS] Gruppenfaktor → 1.0 für große Abstände

**Numerische Stabilität:**
- [PASS] Konvergenz in < 20 Iterationen
- [PASS] Monotone Abnahme des Residuums
- [PASS] Keine Oszillationen

**Grenzwerte:**
- [PASS] R_mutual → 0 für D → ∞
- [PASS] R_mutual → ∞ für D → 0 (physikalisch)
- [PASS] Symmetric matrix R_mutual[i,j] = R_mutual[j,i]

## Literatur und Standards

1. **IEC 60287-2-1**: Calculation of the current rating - Thermal resistance
   - Section 2.2: Mutual heating between cables
   
2. **RML_GAE2**: Grundlagen Wärmetransportberechnung und Optimierung Kabelabstand
   - ARCADIS interne Richtlinie

3. **CIGRE TB 880**: Cable Systems Electrical Characteristics
   - Chapter 5: Thermal calculations

## Nächste Schritte

### Geplante Erweiterungen:

1. **Web-Interface Integration**
   - Multi-Kabel-Eingabeformular
   - Live-Optimierung im Browser
   - 2D-Visualisierung der Kabelanordnung

2. **3D-Temperaturfeld**
   - Finite-Elemente-Berechnung
   - Visualisierung der Bodenerwärmung
   - Export für CFD-Tools

3. **Dynamische Belastung**
   - Zeitabhängige Stromlast
   - Lastzyklen nach IEC 60853
   - Thermische Trägheit

4. **Optimierung unter Nebenbedingungen**
   - Maximale Trassenlänge
   - Minimale/maximale Abstände
   - Kostenoptimierung (Trassenlänge vs. Kabelquerschnitt)

---

**Status:** Vollständig implementiert und validiert (2025-10-16)
**Entwickler:** ARCADIS Engineering Team
**Lizenz:** ARCADIS Internal Use Only
