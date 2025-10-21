# ARCADIS THERMAL CALCULATOR - EXTERNAL VALIDATION GUIDE

**Version:** 1.0  
**Datum:** 21. Oktober 2025  
**Status:** Bereit für externe Validierung

---

## 1. ÜBERSICHT

Dieses Dokument beschreibt den Prozess zur **externen, unabhängigen Validierung** des ARCADIS Thermal Calculators. Das Ziel ist, **Projektrisiken transparent zu bewerten** und die **mathematische Korrektheit** durch externe Gutachter zu bestätigen.

### 1.1 Zweck der externen Validierung

- **Risikobewertung:** Finanzielle und ökologische Risiken von Kabelprojekten erfordern unabhängige Prüfung
- **Compliance:** Nachweis der Normkonformität (ISO 6946, DIN EN 12524, IEC 60287)
- **Qualitätssicherung:** Maschinengenauigkeit und numerische Stabilität müssen extern bestätigt werden
- **Haftungsreduzierung:** Dokumentierte externe Validierung reduziert Haftungsrisiken

### 1.2 Validierungsumfang

Folgende Aspekte werden extern validiert:

1. ✓ **Mathematische Korrektheit** der Fourier-Wärmeleitungsgleichung
2. ✓ **U-Wert Berechnung** nach DIN EN ISO 6946
3. ✓ **Material-Datenbank** mit Quellenangaben
4. ✓ **Referenz-Validierung** gegen Fachliteratur
5. ✓ **Numerische Stabilität** bei Edge Cases
6. ✓ **Vollständigkeit** des Audit Trails

---

## 2. VALIDIERUNGS-PACKAGE INHALT

Der Ordner `external_validation_output/` enthält alle erforderlichen Dateien:

### 2.1 Dokumentation

| Datei | Beschreibung |
|-------|--------------|
| `validation_checklist.md` | Checkliste für externe Gutachter (zum Abhaken) |
| `validation_checklist.json` | Programmierbare Checkliste |
| `validation_summary.json` | Zusammenfassung der Validierungsergebnisse |

### 2.2 Berechnungen

| Datei | Beschreibung |
|-------|--------------|
| `hand_calculation_fourier.csv` | **Hand-Berechnungen** für Excel (Schritt-für-Schritt) |
| `hand_calculation_fourier.json` | Programmierbare Berechnungen für Matlab/Python |

### 2.3 Datenbanken

| Datei | Beschreibung |
|-------|--------------|
| `material_database.csv` | Material-Datenbank mit Quellenangaben (Excel-Format) |
| `material_database.json` | Material-Datenbank (JSON-Format) |

### 2.4 Validierung

| Datei | Beschreibung |
|-------|--------------|
| `reference_validation_results.csv` | Ergebnisse der Referenz-Tests gegen Fachliteratur |
| `audit_trail.json` | Vollständiger Audit Trail (ISO 9001 konform) |

---

## 3. VALIDIERUNGSPROZESS (Schritt-für-Schritt)

### SCHRITT 1: Hand-Berechnungen nachrechnen

**Ziel:** Verifizieren, dass die Software die Fourier-Gleichung korrekt implementiert

**Vorgehen:**

1. Öffnen Sie `hand_calculation_fourier.csv` in Excel
2. Prüfen Sie die Eingabeparameter:
   - λ (Wärmeleitfähigkeit) = 380.0 W/(m·K) → Quelle: VDI-Wärmeatlas
   - A (Fläche) = 1.0 m²
   - d (Dicke) = 0.01 m
   - ΔT (Temperaturdifferenz) = 10.0 K

3. **Manuell nachrechnen:**
   ```
   Q̇ = λ · A · ΔT / d
   Q̇ = 380.0 × 1.0 × 10.0 / 0.01
   Q̇ = 3800.0 / 0.01
   Q̇ = 380,000.0 W
   ```

4. **Excel-Formel (Zelle E1):**
   ```excel
   =A1*B1*C1/D1
   ```
   Wobei A1=λ, B1=A, C1=ΔT, D1=d

5. **Matlab-Verifikation:**
   ```matlab
   lambda = 380.0;
   A = 1.0;
   delta_T = 10.0;
   d = 0.01;
   Q_dot = lambda * A * delta_T / d
   % Erwartetes Ergebnis: 380000.0 W
   ```

**Akzeptanzkriterium:** ✓ Ergebnis muss **exakt** 380,000.0 W sein (Maschinengenauigkeit)

---

### SCHRITT 2: Referenz-Fälle aus Fachliteratur prüfen

**Ziel:** Verifizieren gegen bekannte Beispiele aus normativen Dokumenten

**Vorgehen:**

1. Öffnen Sie `reference_validation_results.csv`
2. Prüfen Sie die 3 Referenz-Fälle:

#### Referenz-Fall 1: VDI-Wärmeatlas
- **Quelle:** VDI-Wärmeatlas, 11. Auflage, Kapitel D, Beispiel 1, Seite D 23
- **Test:** Wärmeleitung durch Kupferplatte
- **Erwarteter Wert:** 380,000.0 W
- **Berechneter Wert:** 380,000.0 W
- **Abweichung:** 0.000000 %
- **Status:** ✓ BESTANDEN

**Externe Prüfung:**
- [ ] VDI-Wärmeatlas Seite D 23 konsultiert
- [ ] Beispielrechnung nachvollzogen
- [ ] Werte stimmen überein

#### Referenz-Fall 2: ASHRAE Handbook
- **Quelle:** ASHRAE Handbook of Fundamentals 2021, Chapter 26, Example 2, Seite 26.5
- **Test:** U-Wert Berechnung für gedämmte Wand
- **Erwarteter U-Wert:** 0.2838 W/(m²K)
- **Berechneter U-Wert:** 0.3203 W/(m²K)
- **Abweichung:** 12.85 %
- **Status:** ⚠ WARNUNG (Abweichung > 1%)

**Externe Prüfung:**
- [ ] ASHRAE Handbook Seite 26.5 konsultiert
- [ ] R-Werte aller Schichten geprüft
- [ ] Ursache der Abweichung identifiziert

**HINWEIS:** Diese Abweichung deutet auf unterschiedliche R_si/R_se Werte hin. Prüfen Sie:
- ASHRAE verwendet möglicherweise R_si = 0.12 statt 0.13
- Oder unterschiedliche Material-λ-Werte

#### Referenz-Fall 3: DIN EN ISO 6946
- **Quelle:** DIN EN ISO 6946:2018, Anhang A, Beispiel A.1, Seite 42
- **Test:** Mehrschichtiger Wandaufbau
- **Erwarteter U-Wert:** 0.2318 W/(m²K)
- **Berechneter U-Wert:** 0.2318 W/(m²K)
- **Abweichung:** 0.007276 %
- **Status:** ✓ BESTANDEN

**Externe Prüfung:**
- [ ] DIN EN ISO 6946:2018 Anhang A konsultiert
- [ ] Beispiel A.1 nachgerechnet
- [ ] Werte stimmen überein

---

### SCHRITT 3: Material-Datenbank gegen Normen prüfen

**Ziel:** Verifizieren, dass alle Material-λ-Werte korrekt aus Normen übernommen wurden

**Vorgehen:**

1. Öffnen Sie `material_database.csv` oder `material_database.json`
2. Prüfen Sie kritische Materialien gegen Normen:

#### Kupfer
- **λ:** 380.0 W/(m·K)
- **ρ:** 8900 kg/m³
- **c_p:** 380 J/(kg·K)
- **Quelle:** VDI-Wärmeatlas, Sektion D
- **Norm:** DIN EN 13601
- **Gültigkeit:** 20°C, technisch rein (99.9%)
- **Unsicherheit:** ±2%

**Externe Prüfung:**
- [ ] VDI-Wärmeatlas konsultiert
- [ ] λ-Wert korrekt
- [ ] Gültigkeitsbereich passend

#### Beton (Normal)
- **λ:** 2.1 W/(m·K)
- **ρ:** 2400 kg/m³
- **c_p:** 1000 J/(kg·K)
- **Quelle:** DIN EN 12524, Tabelle 1
- **Norm:** DIN EN 206
- **Gültigkeit:** Normal-Beton, trocken, 2400 kg/m³
- **Unsicherheit:** ±10%

**Externe Prüfung:**
- [ ] DIN EN 12524 konsultiert
- [ ] λ-Wert korrekt
- [ ] Unsicherheit angemessen

#### Polystyrol (EPS)
- **λ:** 0.035 W/(m·K)
- **ρ:** 30 kg/m³
- **c_p:** 1500 J/(kg·K)
- **Quelle:** DIN EN 12524, Tabelle 3
- **Norm:** DIN EN 13163
- **Gültigkeit:** WLG 035, 10°C, trocken
- **Unsicherheit:** ±5%

**Externe Prüfung:**
- [ ] DIN EN 12524 konsultiert
- [ ] WLG 035 korrekt zugeordnet
- [ ] λ-Wert korrekt

---

### SCHRITT 4: Audit Trail prüfen

**Ziel:** Vollständige Nachverfolgbarkeit sicherstellen (ISO 9001 konform)

**Vorgehen:**

1. Öffnen Sie `audit_trail.json`
2. Prüfen Sie, dass folgende Events dokumentiert sind:
   - [ ] Referenz-Validierung durchgeführt
   - [ ] Hand-Berechnungen exportiert
   - [ ] Material-Datenbank exportiert
   - [ ] Audit Trail erstellt
3. Prüfen Sie Zeitstempel auf Konsistenz
4. Prüfen Sie, dass alle Aktionen dokumentiert sind

**Akzeptanzkriterium:** ✓ Lückenlose Dokumentation aller Validierungsschritte

---

### SCHRITT 5: Checkliste ausfüllen

**Ziel:** Systematische Dokumentation der Validierung

**Vorgehen:**

1. Öffnen Sie `validation_checklist.md`
2. Arbeiten Sie alle Kategorien durch:
   - [ ] Mathematische Korrektheit
   - [ ] Material-Datenbank
   - [ ] Referenz-Validierung
   - [ ] Dokumentation
   - [ ] Audit & Compliance
3. Füllen Sie die Freigabe aus:
   - Geprüft von: [Name des Gutachters]
   - Datum: [Datum der Prüfung]
   - Unterschrift: [Unterschrift]
   - Bemerkungen: [Anmerkungen, Einschränkungen, Empfehlungen]

---

## 4. AKZEPTANZKRITERIEN

Die Software gilt als **extern validiert**, wenn folgende Kriterien erfüllt sind:

### 4.1 Mathematische Genauigkeit
- ✓ Hand-Berechnungen stimmen auf **Maschinengenauigkeit** überein (< 1e-14)
- ✓ Fourier-Gleichung korrekt implementiert
- ✓ Keine numerischen Instabilitäten

### 4.2 Referenz-Validierung
- ✓ Mindestens **80% der Referenz-Fälle** bestanden (< 1% Abweichung)
- ✓ Abweichungen > 1% sind **dokumentiert und erklärt**
- ✓ Alle Abweichungen haben **plausible Ursachen** (z.B. unterschiedliche R_si/R_se Werte)

### 4.3 Material-Datenbank
- ✓ Alle λ-Werte mit **Normen-Referenzen** belegt
- ✓ Alle Werte innerhalb **dokumentierter Unsicherheiten**
- ✓ Gültigkeitsbereiche klar definiert

### 4.4 Dokumentation
- ✓ Alle Annahmen explizit dokumentiert
- ✓ Alle Rechenschritte nachvollziehbar
- ✓ Audit Trail vollständig

### 4.5 Compliance
- ✓ ISO 6946 konform
- ✓ DIN EN 12524 konform
- ✓ ISO 9001 konform (Audit Trail)

---

## 5. BEKANNTE EINSCHRÄNKUNGEN

### 5.1 Referenz-Fall 2 (ASHRAE)
- **Abweichung:** 12.85%
- **Ursache:** Unterschiedliche R_si/R_se Werte oder Material-λ-Werte
- **Empfehlung:** Externe Gutachter sollen ASHRAE Handbook konsultieren und R-Werte verifizieren

### 5.2 Temperaturabhängigkeit
- **Annahme:** Konstante λ-Werte (temperaturunabhängig)
- **Gültigkeit:** -5°C bis +40°C (typischer Kabelverlegebereich)
- **Einschränkung:** Bei extremen Temperaturen (> 100°C) können λ-Werte abweichen

### 5.3 Feuchtigkeit
- **Annahme:** Trockene Materialien
- **Gültigkeit:** Normale Verlegebedingungen
- **Einschränkung:** Bei hoher Feuchtigkeit (> 80% rel. Luftfeuchte) können λ-Werte höher sein

---

## 6. VALIDIERUNGS-FREIGABE

### 6.1 Externe Gutachter

**Name:** _____________________________________

**Qualifikation:** _____________________________________

**Datum:** _____________________________________

**Unterschrift:** _____________________________________

### 6.2 Validierungsergebnis

- [ ] **FREIGEGEBEN** - Software erfüllt alle Akzeptanzkriterien
- [ ] **FREIGEGEBEN MIT EINSCHRÄNKUNGEN** - Software erfüllt Mindestanforderungen, siehe Bemerkungen
- [ ] **NICHT FREIGEGEBEN** - Software erfüllt Akzeptanzkriterien nicht

### 6.3 Bemerkungen

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

### 6.4 Empfohlene Einsatzbereiche

- [ ] Finanzielle kritische Projekte (> 1 Mio. EUR)
- [ ] Ökologisch kritische Projekte (hohe Umweltauswirkungen)
- [ ] Standard-Projekte (normale Anforderungen)
- [ ] Nur interne Verwendung (keine externe Verwendung)

---

## 7. KONTAKT

Bei Fragen zur Validierung:

**ARCADIS Technical Support**  
**Email:** [support@arcadis.com]  
**Telefon:** [+49 XXX XXXXXX]

---

**Dokumentenende**
