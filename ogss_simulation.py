python
import numpy as np
import pandas as pd
import math

def run_photon_budget_analysis(distance_pc=10.0, aperture_diameter=6.0):
    """
    WORK PACKAGE 2: Calculates basic photon mechanics for a single satellite
    versus background noise sources at interstellar distances.
    """
    # Physical Constants
    pc_to_m = 3.086e16
    h = 6.626e-34
    c = 3.0e8
    wavelength = 550e-9  # Center of visible band (V-band)
    photon_energy = (h * c) / wavelength
    
    distance_m = distance_pc * pc_to_m
    solar_constant = 1361.0  # W/m^2 at 1 AU
    theta_sun = 0.0093      # Angular diameter of Solar twin from 1 AU (rad)
    
    # Beam divergence footprint area at telescope distance
    spot_radius = distance_m * (theta_sun / 2)
    spot_area = math.pi * (spot_radius ** 2)
    
    # Telescope Properties
    telescope_area = math.pi * (aperture_diameter / 2) ** 2
    throughput = 0.20  # 20% photon efficiency
    
    # Single Object Reflection Mechanics (10 m^2 mirror, 90% specular albedo)
    avg_mirror_area = 10.0
    albedo_specular = 0.9
    power_reflected_per_sat = solar_constant * avg_mirror_area * albedo_specular
    total_photons_reflected_per_sat = power_reflected_per_sat / photon_energy
    
    # Fraction of the diverged beam captured by the telescope
    fraction_captured = telescope_area / spot_area
    photons_per_sat_per_sec = total_photons_reflected_per_sat * fraction_captured * throughput
    
    print("=====================================================================")
    print("📌 WORK PACKAGE 2: PHOTON BUDGET ANALYSIS")
    print("=====================================================================")
    print(f"Target System Distance: {distance_pc} pc ({distance_m:.2e} meters)")
    print(f"Telescope Aperture: {aperture_diameter} meters")
    print(f"Reflected Beam Footprint Radius at Earth: {spot_radius:.2e} meters")
    print(f"Single Satellite Photons/sec collected: {photons_per_sat_per_sec:.2e}")
    print(f"Time required for 1 photon from a single satellite: {1/photons_per_sat_per_sec:.2e} seconds\n")


def generate_snr_sensitivity_surface(distance_pc=10.0, integration_time_hours=100.0):
    """
    WORK PACKAGE 2 (EXTENDED): Generates a sensitivity matrix mapping 
    Constellation Size vs. Telescope Aperture Size to find the statistical detection threshold.
    """
    pc_to_m = 3.086e16
    h = 6.626e-34; c = 3.0e8; wavelength = 550e-9
    photon_energy = (h * c) / wavelength
    
    distance_m = distance_pc * pc_to_m
    solar_constant = 1361.0
    theta_sun = 0.0093
    spot_area = math.pi * (distance_m * (theta_sun / 2)) ** 2
    
    # Background Star Flux (V-band solar twin at 10pc yields ~2.33e7 photons/sec/m2)
    star_flux_density_m2 = 2.33e7 
    raw_contrast = 1e-10  # Coronagraph leakage performance
    throughput = 0.20     
    
    apertures = np.linspace(2.0, 15.0, 6)       
    constellations = np.logspace(5, 9, 5)       # 100k to 1 Billion objects
    duty_cycle = 0.001                          # 0.1% actively flashing to observer
    integration_seconds = integration_time_hours * 3600.0
    
    print("=====================================================================")
    print(f"📌 WORK PACKAGE 2: SENSITIVITY SURFACE (AGGREGATE SNR OVER {integration_time_hours} HRS)")
    print("=====================================================================")
    print(f"Assumed Coronagraph Star Leakage Contrast: {raw_contrast:.1e}\n")
    
    header = f"{'Constellation Size':<20}" + "".join([f"{f'{ap}m':>12}" for ap in apertures])
    print(header)
    print("-" * len(header))
    
    for N in constellations:
        row_str = f"{int(N):<20,}"
        for D in apertures:
            tel_area = math.pi * (D / 2)**2
            
            # Background Shot Noise from star leakage
            star_photons_sec = star_flux_density_m2 * tel_area * throughput
            leakage_photons_sec = star_photons_sec * raw_contrast
            total_bg_noise_photons = leakage_photons_sec * integration_seconds
            shot_noise = math.sqrt(total_bg_noise_photons)
            
            # Signal accumulation
            power_per_sat = solar_constant * 10.0 * 0.9  
            photons_sec_per_sat = (power_per_sat / photon_energy) * (tel_area / spot_area) * throughput
            active_sats = N * duty_cycle
            aggregate_signal_photons = (photons_sec_per_sat * active_sats) * integration_seconds
            
            snr = aggregate_signal_photons / shot_noise if shot_noise > 0 else 0
            row_str += f"{snr:>12.2f}"
        print(row_str)
    print("\n")


def generate_earth_forward_model(duration_hours=48.0, cadence_minutes=1.0):
    """
    WORK PACKAGE 3: Simulates the dynamic, disk-integrated light curve of natural Earth
    including continental rotation, cloud variations, and ocean glint confounders.
    """
    total_steps = int((duration_hours * 60) / cadence_minutes)
    times_hours = np.linspace(0, duration_hours, total_steps)
    
    t_rot = 24.0
    rotation_phase = (times_hours % t_rot) / t_rot * 2 * np.pi
    base_flux = 1.0 
    
    # 1. Rotational Land/Ocean Modulation
    land_albedo_mod = 0.15 * np.sin(rotation_phase) + 0.05 * np.cos(2 * rotation_phase)
    
    # 2. Stochastic Weather / Clouds
    np.random.seed(42)
    slow_weather = 0.08 * np.sin(rotation_phase / 3) 
    fast_clouds = np.random.normal(0, 0.03, total_steps)
    cloud_noise = slow_weather + fast_clouds
    
    # 3. Natural Ocean Glint Spikes (The primary tracking confounder)
    ocean_glint = np.zeros(total_steps)
    glint_peak_1 = 0.25 * np.pi  
    glint_peak_2 = 1.25 * np.pi  
    glint_width_rad = 0.15 
    
    for i, phase in enumerate(rotation_phase):
        diff_1 = np.arctan2(np.sin(phase - glint_peak_1), np.cos(phase - glint_peak_1))
        diff_2 = np.arctan2(np.sin(phase - glint_peak_2), np.cos(phase - glint_peak_2))
        spike_1 = 0.40 * np.exp(-(diff_1**2) / (2 * glint_width_rad**2))
        spike_2 = 0.40 * np.exp(-(diff_2**2) / (2 * glint_width_rad**2))
        ocean_glint[i] = spike_1 + spike_2

    f_nat = base_flux + land_albedo_mod + cloud_noise + ocean_glint
    
    light_curve = pd.DataFrame({
        'Time_Hours': times_hours,
        'Rotational_Modulation': land_albedo_mod,
        'Cloud_Noise': cloud_noise,
        'Ocean_Glint_Flux': ocean_glint,
        'Total_Natural_Flux': f_nat
    })
    
    print("=====================================================================")
    print("📌 WORK PACKAGE 3: NATURAL EARTH DYNAMIC LIGHT CURVE SAMPLE")
    print("=====================================================================")
    print(light_curve[['Time_Hours', 'Ocean_Glint_Flux', 'Total_Natural_Flux']].head(10))
    print(f"...\nSuccessfully generated {len(light_curve)} high-cadence data points.")
    return light_curve


if __name__ == "__main__":
    # Execute the technical validation baseline
    run_photon_budget_analysis(distance_pc=10.0, aperture_diameter=6.0)
    generate_snr_sensitivity_surface(distance_pc=10.0, integration_time_hours=100.0)
    earth_df = generate_earth_forward_model(duration_hours=48.0, cadence_minutes=1.0)
