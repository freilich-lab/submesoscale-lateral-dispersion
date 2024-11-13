import numpy as np 
import pickle 
import os

# Constants
SECONDS_PER_DAY = 86400  # 24 hours * 60 minutes * 60 seconds
meters_per_degree = 111320
AVG_LATITUDE = 35  # Picking a latitude for the conversion of the turbulent velocity fluctuations into the correct units (should not matter that much because it itself is an average)
R = 6371000 # Radius of earth in meters (approximately)


def get_velocities(longitudes, latitudes, time_diff):
    """
    Returns the list of velocities in m/s given a trajectory in lon/lat coordinates. 
    """
    lat_rad = np.radians(latitudes) #convert from degrees to radians 
    lon_rad = np.radians(longitudes)
    dlat = np.diff(lat_rad) #calculate differences 
    dlon = np.diff(lon_rad)
    # Calculate displacements in meters
    displacement_ns = dlat * R #meridional 
    displacement_ew = dlon * R * np.cos(lat_rad[:-1]) #zonal, accounting for lat 
    # Calculate velocities in m/s
    v_velocities = displacement_ns / time_diff  # Meridional velocity
    u_velocities = displacement_ew / time_diff  # Zonal velocity
    return u_velocities, v_velocities


def update_position(lat, lon, u, v, dt):
    """
    Calculates the updated particle position.
    Input:
    - lat, lon: current lat/lon, in degrees
    - u, v: velocity components in m/s
    - dt: time step in s
    Returns:
    - Updated latitude and longitude in degrees.
    """
    delta_lat = (v / R) * (180 / np.pi) * dt
    delta_lon = (u / (R * np.cos(np.radians(lat)))) * (180 / np.pi) * dt
    new_lat = lat + delta_lat
    new_lon = lon + delta_lon
    return new_lat, new_lon


def clean_dict(input_dict):
    """
    Removes any entries that have nan values (like if a trajectory left the domain, there could then be nan values) from a dictionary.
    Input:
    - input_dict: Expected to have (lon, lat) tuples as keys and numpy arrays or lists as values.
    Returns:
    - A new dictionary with the same structure as input_dict but without any entries that had nans. 
    """
    cleaned_dict = {}
    for key, value in input_dict.items():
        if isinstance(value, (np.ndarray, list)):
            if not np.isnan(value).any():
                cleaned_dict[key] = value
        else:
            if not np.isnan(value): 
                cleaned_dict[key] = value
    return cleaned_dict


def calculate_acceleration(times, x):
    """
    Compute acceleration using a central difference approximation.
    """ 
    dt = np.diff(times) 
    acceleration = np.zeros_like(x, dtype=float)
    acceleration[1:-1, :, :] = (x[2:, :, :] - x[:-2, :, :]) / (dt[1:] + dt[:-1])[:, np.newaxis, np.newaxis]
    # Handle the first and last points using forward and backward differences, respectively
    acceleration[0, :, :] = (x[1, :, :] - x[0, :, :]) / dt[0]
    acceleration[-1, :, :] = (x[-1, :, :] - x[-2, :, :]) / dt[-1]
    return acceleration


def convert_velocity(velocity_m_s, latitude):
    """
    Convert to degrees/day.
    """
    adjusted_factor = np.cos(np.radians(latitude)) 
    u = (velocity_m_s[0] / (meters_per_degree * adjusted_factor)) * SECONDS_PER_DAY 
    v = (velocity_m_s[1] / meters_per_degree) * SECONDS_PER_DAY
    return (u,v)