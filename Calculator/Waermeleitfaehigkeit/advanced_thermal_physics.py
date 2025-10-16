"""
Advanced Thermal Physics Module
Erweiterte physikalische Modelle für Kabelberechnung

Ergänzt IEC 60287 um:
- Konvektion (natürlich und erzwungen)
- Strahlung (Stefan-Boltzmann)
- Transiente Effekte (zeitabhängig)
- Skin-Effekt (AC-Widerstand)
- Proximity-Effekt (Nachbarleiter)
- Schirm- und Mantelverluste
- Verlegearten und Gruppenfaktoren
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ConvectionParameters:
    """Parameter für Konvektion"""
    air_velocity: float = 0.0  # m/s (0 = natürliche Konvektion)
    air_temp: float = 20.0  # °C
    characteristic_length: float = 0.1  # m (Kabeldurchmesser)
    surface_roughness: float = 0.0001  # m
    
    # Lufteigenschaften bei 20°C
    air_density: float = 1.2  # kg/m³
    air_viscosity: float = 1.81e-5  # Pa·s
    air_conductivity: float = 0.026  # W/(m·K)
    air_prandtl: float = 0.71  # Prandtl-Zahl
    

@dataclass
class RadiationParameters:
    """Parameter für Wärmestrahlung"""
    emissivity: float = 0.9  # Emissionsgrad (0-1)
    surrounding_temp: float = 20.0  # °C
    view_factor: float = 1.0  # Sichtfaktor (0-1)
    stefan_boltzmann: float = 5.67e-8  # W/(m²·K⁴)


class ConvectionModel:
    """Berechnung des konvektiven Wärmeübergangs"""
    
    @staticmethod
    def calculate_nusselt_natural(grashof: float, prandtl: float) -> float:
        """
        Nusselt-Zahl für natürliche Konvektion (horizontaler Zylinder)
        
        Nu = C × (Gr × Pr)^n
        """
        rayleigh = grashof * prandtl
        
        if rayleigh < 1e-4:
            return 0.4
        elif rayleigh < 1e4:
            return 0.675 * rayleigh**0.058
        elif rayleigh < 1e9:
            return 0.54 * rayleigh**0.25
        else:
            return 0.135 * rayleigh**(1/3)
    
    @staticmethod
    def calculate_nusselt_forced(reynolds: float, prandtl: float) -> float:
        """
        Nusselt-Zahl für erzwungene Konvektion (Querstrom über Zylinder)
        
        Nu = C × Re^m × Pr^(1/3)
        """
        if reynolds < 4:
            return 0.989 * reynolds**0.330 * prandtl**(1/3)
        elif reynolds < 40:
            return 0.911 * reynolds**0.385 * prandtl**(1/3)
        elif reynolds < 4000:
            return 0.683 * reynolds**0.466 * prandtl**(1/3)
        elif reynolds < 40000:
            return 0.193 * reynolds**0.618 * prandtl**(1/3)
        else:
            return 0.027 * reynolds**0.805 * prandtl**(1/3)
    
    @staticmethod
    def calculate_heat_transfer_coefficient(params: ConvectionParameters, 
                                           surface_temp: float) -> float:
        """
        Berechnet Wärmeübergangskoeffizient h in W/(m²·K)
        
        Args:
            params: Konvektionsparameter
            surface_temp: Oberflächentemperatur in °C
            
        Returns:
            h: Wärmeübergangskoeffizient in W/(m²·K)
        """
        # Mittlere Filmtemperatur
        t_film = (surface_temp + params.air_temp) / 2
        
        # Temperaturdifferenz
        delta_t = abs(surface_temp - params.air_temp)
        
        if delta_t < 0.1:
            return 0.0
        
        # Grashof-Zahl (natürliche Konvektion)
        g = 9.81  # m/s²
        beta = 1 / (273.15 + t_film)  # Volumenausdehnungskoeffizient
        
        grashof = (g * beta * delta_t * params.characteristic_length**3) / \
                  (params.air_viscosity / params.air_density)**2
        
        # Reynolds-Zahl (erzwungene Konvektion)
        reynolds = (params.air_density * params.air_velocity * 
                   params.characteristic_length) / params.air_viscosity
        
        # Nusselt-Zahl auswählen
        if params.air_velocity < 0.1:
            # Natürliche Konvektion dominant
            nusselt = ConvectionModel.calculate_nusselt_natural(
                grashof, params.air_prandtl
            )
        else:
            # Erzwungene Konvektion
            nu_forced = ConvectionModel.calculate_nusselt_forced(
                reynolds, params.air_prandtl
            )
            nu_natural = ConvectionModel.calculate_nusselt_natural(
                grashof, params.air_prandtl
            )
            # Gemischte Konvektion
            nusselt = max(nu_forced, nu_natural)
        
        # Wärmeübergangskoeffizient
        h = nusselt * params.air_conductivity / params.characteristic_length
        
        return h


class RadiationModel:
    """Berechnung der Wärmestrahlung"""
    
    @staticmethod
    def calculate_radiation_heat_flux(params: RadiationParameters,
                                     surface_temp: float,
                                     surface_area: float) -> float:
        """
        Berechnet Strahlungswärmestrom nach Stefan-Boltzmann
        
        Q_rad = ε × σ × F × A × (T_s⁴ - T_surr⁴)
        
        Args:
            params: Strahlungsparameter
            surface_temp: Oberflächentemperatur in °C
            surface_area: Oberfläche in m²
            
        Returns:
            Q: Wärmestrom in W
        """
        # Temperaturen in Kelvin
        t_surface_k = surface_temp + 273.15
        t_surr_k = params.surrounding_temp + 273.15
        
        # Stefan-Boltzmann Gesetz
        q_rad = (params.emissivity * params.stefan_boltzmann * 
                params.view_factor * surface_area *
                (t_surface_k**4 - t_surr_k**4))
        
        return q_rad
    
    @staticmethod
    def calculate_radiation_coefficient(params: RadiationParameters,
                                       surface_temp: float) -> float:
        """
        Linearisierter Strahlungskoeffizient h_rad in W/(m²·K)
        
        h_rad ≈ 4 × ε × σ × T_m³
        """
        t_mean = ((surface_temp + params.surrounding_temp) / 2 + 273.15)
        
        h_rad = 4 * params.emissivity * params.stefan_boltzmann * t_mean**3
        
        return h_rad


class SkinEffectModel:
    """Skin-Effekt für AC-Leitungen"""
    
    @staticmethod
    def calculate_skin_depth(frequency: float, resistivity: float, 
                            mu_r: float = 1.0) -> float:
        """
        Berechnet Eindringtiefe δ in m
        
        δ = √(ρ / (π × f × μ₀ × μᵣ))
        
        Args:
            frequency: Frequenz in Hz (50 Hz für Europa)
            resistivity: Spezifischer Widerstand in Ω·m
            mu_r: Relative Permeabilität (1.0 für Kupfer/Aluminium)
            
        Returns:
            δ: Eindringtiefe in m
        """
        mu_0 = 4 * math.pi * 1e-7  # H/m
        
        if frequency < 0.1:
            return float('inf')  # DC
        
        delta = math.sqrt(resistivity / (math.pi * frequency * mu_0 * mu_r))
        
        return delta
    
    @staticmethod
    def calculate_ac_resistance(r_dc: float, conductor_radius: float,
                               frequency: float, resistivity: float) -> float:
        """
        Berechnet AC-Widerstand mit Skin-Effekt
        
        R_ac = R_dc × k_skin
        """
        delta = SkinEffectModel.calculate_skin_depth(frequency, resistivity)
        
        # Verhältnis Radius zu Eindringtiefe
        x = conductor_radius / delta
        
        if x < 1:
            # Geringer Skin-Effekt
            k_skin = 1 + x**4 / 48
        else:
            # Starker Skin-Effekt (Bessel-Funktionen-Näherung)
            k_skin = x / 2 * (1 + 0.25 / x)
        
        return r_dc * k_skin


class ProximityEffectModel:
    """Proximity-Effekt zwischen mehreren Leitern"""
    
    @staticmethod
    def calculate_proximity_factor(conductor_radius: float,
                                   axis_distance: float,
                                   num_conductors: int = 3) -> float:
        """
        Berechnet Proximity-Faktor k_p
        
        Args:
            conductor_radius: Leiterradius in m
            axis_distance: Achsabstand in m
            num_conductors: Anzahl Leiter (3 für Drehstrom)
            
        Returns:
            k_p: Proximity-Faktor (≥ 1.0)
        """
        if axis_distance < 2 * conductor_radius:
            axis_distance = 2 * conductor_radius
        
        # Verhältnis Abstand zu Radius
        s_d = axis_distance / (2 * conductor_radius)
        
        if num_conductors == 2:
            # Zwei parallele Leiter
            k_p = 1 + 1 / (4 * s_d**2)
        elif num_conductors == 3:
            # Drei Leiter (Dreieckformation oder flach)
            # Vereinfachte Formel nach IEC 60287-1-1
            k_p = 1 + 0.312 * (2 * conductor_radius / axis_distance)**2
        else:
            k_p = 1.0
        
        return k_p


class TransientThermalModel:
    """Transiente (zeitabhängige) Wärmeberechnung"""
    
    @staticmethod
    def calculate_thermal_capacitance(layers: List, length: float = 1.0) -> float:
        """
        Berechnet thermische Kapazität C in J/K
        
        C = Σ(ρᵢ × cᵢ × Vᵢ)
        """
        c_total = 0.0
        
        for layer in layers:
            volume = math.pi * (layer.outer_radius**2 - layer.inner_radius**2) * length
            if hasattr(layer, 'density') and hasattr(layer, 'specific_heat'):
                c_layer = layer.density * layer.specific_heat * volume
                c_total += c_layer
        
        return c_total
    
    @staticmethod
    def calculate_time_constant(thermal_resistance: float,
                               thermal_capacitance: float) -> float:
        """
        Berechnet thermische Zeitkonstante τ in s
        
        τ = R_th × C_th
        """
        return thermal_resistance * thermal_capacitance
    
    @staticmethod
    def calculate_transient_temperature(t_initial: float, t_final: float,
                                       time: float, time_constant: float) -> float:
        """
        Berechnet Temperatur zum Zeitpunkt t
        
        T(t) = T_final + (T_initial - T_final) × exp(-t/τ)
        """
        return t_final + (t_initial - t_final) * math.exp(-time / time_constant)
    
    @staticmethod
    def calculate_heating_curve(t_ambient: float, losses: float,
                               thermal_resistance: float,
                               thermal_capacitance: float,
                               time_steps: int = 100,
                               duration: float = 3600) -> Tuple[np.ndarray, np.ndarray]:
        """
        Berechnet Aufheizkurve über Zeit
        
        Returns:
            (times, temperatures): Arrays für Zeit und Temperatur
        """
        tau = thermal_resistance * thermal_capacitance
        t_final = t_ambient + losses * thermal_resistance
        
        times = np.linspace(0, duration, time_steps)
        temperatures = t_ambient + (t_final - t_ambient) * (1 - np.exp(-times / tau))
        
        return times, temperatures


class ShieldLossModel:
    """Schirm- und Mantelverluste"""
    
    @staticmethod
    def calculate_shield_losses(conductor_current: float,
                               shield_resistance: float,
                               mutual_inductance: float,
                               frequency: float = 50) -> float:
        """
        Berechnet Schirmverluste durch induzierte Ströme
        
        W_shield ≈ I²_conductor × (ω × M / R_shield)² × R_shield
        """
        omega = 2 * math.pi * frequency
        
        if shield_resistance < 1e-9:
            return 0.0
        
        # Induzierter Schirmstrom (vereinfacht)
        i_shield = conductor_current * (omega * mutual_inductance) / shield_resistance
        
        # Schirmverluste
        w_shield = i_shield**2 * shield_resistance
        
        return w_shield
    
    @staticmethod
    def calculate_mutual_inductance(conductor_radius: float,
                                   shield_radius: float,
                                   length: float = 1.0) -> float:
        """
        Berechnet Gegeninduktivität M in H/m
        
        M ≈ (μ₀ / 2π) × ln(r_shield / r_conductor)
        """
        mu_0 = 4 * math.pi * 1e-7
        
        if shield_radius <= conductor_radius:
            return 0.0
        
        m = (mu_0 / (2 * math.pi)) * math.log(shield_radius / conductor_radius)
        
        return m * length


class InstallationFactors:
    """Verlegefaktoren nach IEC 60287"""
    
    @staticmethod
    def get_grouping_factor(num_cables: int, spacing_ratio: float) -> float:
        """
        Gruppenfaktor für mehrere Kabel
        
        Args:
            num_cables: Anzahl Kabel
            spacing_ratio: Verhältnis Abstand zu Durchmesser
            
        Returns:
            Faktor < 1.0 (Derating)
        """
        if num_cables == 1:
            return 1.0
        
        # Vereinfachte Tabellenwerte
        if spacing_ratio < 0.25:
            factors = {2: 0.75, 3: 0.65, 4: 0.60, 6: 0.55}
        elif spacing_ratio < 0.5:
            factors = {2: 0.80, 3: 0.70, 4: 0.65, 6: 0.60}
        else:
            factors = {2: 0.85, 3: 0.75, 4: 0.70, 6: 0.65}
        
        return factors.get(num_cables, 0.5)
    
    @staticmethod
    def get_installation_method_factor(method: str) -> float:
        """
        Verlegeart-Faktor
        
        Args:
            method: 'direct_buried', 'in_duct', 'in_air', 'in_water'
        """
        factors = {
            'direct_buried': 1.0,
            'in_duct': 0.85,
            'in_air': 1.2,
            'in_water': 1.15,
            'in_tunnel': 0.90
        }
        
        return factors.get(method, 1.0)
    
    @staticmethod
    def get_soil_thermal_resistivity(soil_type: str, moisture: float = 0.1) -> float:
        """
        Thermischer Bodenwiderstand in K·m/W
        
        Args:
            soil_type: 'sand', 'clay', 'gravel', 'rock'
            moisture: Feuchtegehalt 0-1
        """
        # Trockene Werte
        base_values = {
            'sand': 1.2,
            'clay': 1.0,
            'gravel': 1.5,
            'rock': 2.5,
            'peat': 2.0
        }
        
        base = base_values.get(soil_type, 1.0)
        
        # Feuchtekorrektur (mehr Feuchte = besser)
        moisture_factor = 1 - 0.5 * moisture
        
        return base * moisture_factor


# Validierungsfunktion
def validate_advanced_models():
    """Validiert erweiterte Modelle mit Beispielrechnungen"""
    
    print("=== VALIDIERUNG ERWEITERTE PHYSIK ===\n")
    
    # Test 1: Konvektion
    print("Test 1: Konvektion")
    conv_params = ConvectionParameters(
        air_velocity=2.0,
        air_temp=20.0,
        characteristic_length=0.08
    )
    h = ConvectionModel.calculate_heat_transfer_coefficient(conv_params, 50.0)
    print(f"Wärmeübergangskoeffizient: {h:.2f} W/(m²·K)")
    print(f"Erwartung: 20-40 W/(m²·K) bei 2 m/s Luftstrom")
    print()
    
    # Test 2: Strahlung
    print("Test 2: Strahlung")
    rad_params = RadiationParameters(emissivity=0.9, surrounding_temp=20.0)
    q_rad = RadiationModel.calculate_radiation_heat_flux(
        rad_params, 50.0, 0.25  # 0.25 m² Oberfläche
    )
    print(f"Strahlungswärmestrom: {q_rad:.2f} W")
    print(f"Erwartung: 10-30 W bei 30K Differenz")
    print()
    
    # Test 3: Skin-Effekt
    print("Test 3: Skin-Effekt")
    delta = SkinEffectModel.calculate_skin_depth(50, 1.68e-8)  # Kupfer, 50 Hz
    print(f"Eindringtiefe bei 50 Hz: {delta*1000:.2f} mm")
    print(f"Erwartung: ~9 mm für Kupfer")
    
    r_ac = SkinEffectModel.calculate_ac_resistance(
        r_dc=0.0001, conductor_radius=0.01, frequency=50, resistivity=1.68e-8
    )
    print(f"AC/DC-Widerstandsverhältnis: {r_ac/0.0001:.4f}")
    print()
    
    # Test 4: Transient
    print("Test 4: Transiente Berechnung")
    tau = TransientThermalModel.calculate_time_constant(
        thermal_resistance=1.0, thermal_capacitance=10000
    )
    print(f"Zeitkonstante: {tau/60:.1f} Minuten")
    
    t_after_1h = TransientThermalModel.calculate_transient_temperature(
        t_initial=20, t_final=50, time=3600, time_constant=tau
    )
    print(f"Temperatur nach 1h: {t_after_1h:.1f}°C")
    print()
    
    print("=== VALIDIERUNG ABGESCHLOSSEN ===")


if __name__ == "__main__":
    validate_advanced_models()
