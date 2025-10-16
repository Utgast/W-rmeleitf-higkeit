# Wärmeleitfähigkeit - Thermal Conductivity Calculator
# Python Engineering Application for ARCADIS

Ein professionelles Python-Tool zur Berechnung der Wärmeleitfähigkeit von Materialien und thermischen Analysen.

## 🎯 Funktionen

- **Wärmeleitfähigkeitsberechnungen** für verschiedene Materialien
- **Wärmeübertragungsberechnungen** (Konduktion, Konvektion, Strahlung)
- **Temperaturverteilungsanalyse**
- **Material-Datenbank** mit gängigen Baumaterialien
- **Grafische Visualisierung** von Temperaturverläufen
- **Export-Funktionen** (Excel, PDF, JSON)
- **GUI-Benutzeroberfläche** mit tkinter

## 📦 Installation

```bash
# Virtual Environment erstellen
python -m venv venv

# Virtual Environment aktivieren (Windows)
venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## 🚀 Verwendung

```bash
# Hauptanwendung starten
python main.py

# CLI-Version
python cli.py --material "Beton" --thickness 0.2 --temp-diff 20
```

## 📊 Berechnungen

### Wärmeleitung (Fourier'sches Gesetz)
```
Q = λ × A × ΔT / d
```

- Q: Wärmestrom (W)
- λ: Wärmeleitfähigkeit (W/m·K)
- A: Fläche (m²)
- ΔT: Temperaturdifferenz (K)
- d: Dicke (m)

### Wärmedurchgangskoeffizient (U-Wert)
```
U = 1 / (Rsi + R1 + R2 + ... + Rse)
```

## 🛠️ Entwickelt für ARCADIS
Ingenieuranwendung für thermische Berechnungen und Analysen.

## 📄 Lizenz
© 2025 ARCADIS