import earthkit.data
import os
import json



def download_dfs(requests, dictionay_name):
    """
    Function to "download" as a temporary file with Earthkit and add the orography/variables of several climate models to the dictionary (dfs_orography or dfs_models).
    :param requests: the parameters of the request (those indicated in the Copernicus dataset: names RCM, GCM, resolution, etc.).
    Example of a request
    irnet_orography = {
    "domain": "europe",
    "experiment": "historical",
    "horizontal_resolution": "0_11_degree_x_0_11_degree",
    "temporal_resolution": "fixed",
    "variable": ["orography"],
    "gcm_model": "ichec_ec_earth",
    "rcm_model": "knmi_racmo22e",
    "ensemble_member": "r1i1p1"
    }
    :param dictionary_name: the name of the dictionary to save the dataset in.
    """
    for key_name, request in requests:
        try:
            # "Download" the dataset and convert it into a xarray then convert the dataset into a dataframe
            ds = earthkit.data.from_source("cds", "projections-cordex-domains-single-levels", request)
            df = ds.to_xarray(xarray_open_mfdataset_kwargs=dict(decode_cf=True, decode_times=True))
            # df = ds.to_xarray(xarray_open_mfdataset_kwargs=dict(decode_cf=True, decode_times=True)).to_dataframe().reset_index()
            
            # Add to dictionary
            dictionay_name[key_name] = df
            print(f"Dataset '{key_name}' downloaded and added to dictionary")

            # Convert tasmax from Kelvin to Celsius
            if "tasmax" in df:
                df["tasmax"] = df["tasmax"] - 273.15
                df["tasmax"].attrs["units"] = "°C"
            # Convert tasmin from Kelvin to Celsius
            if "tasmin" in df:
                df["tasmin"] = df["tasmin"] - 273.15
                df["tasmin"].attrs["units"] = "°C"
            # Convert pr from kg*m-2*s-1 to mm
            if "pr" in df:
                df["pr"] = df["pr"] * 100000
                df["pr"].attrs["units"] = "mm"
            # Convertion not needed for wind speed (already in m*s-1)
    
        except Exception as e:
            print(f"Error with the dataset '{key_name}': {e}")

def run_all_models(file_json,variable):
    """
    Load climate model configurations from a JSON file, download the corresponding
    datasets for each model and time interval, and return all results in a structured
    dictionary.

    This function reads a JSON file containing multiple climate model specifications
    (GCM, RCM, ensemble member, and temporal ranges). For each model, it iterates
    through the defined start/end year pairs, builds the request parameters, and
    downloads the associated datasets using `download_dfs()`. All downloaded data
    are organized into a nested dictionary structure.

    Parameters:
        file_json (str):
            Path or filename of the JSON file containing model configurations (e.g., "tasmax.json").
        variable (str):
            Name of the climate variable to download (e.g., "maximum_2m_temperature_in_the_last_24_hours"
                                                            "minimum_2m_temperature_in_the_last_24_hours"
                                                            "mean_precipitation_flux"
                                                            "10m_wind_speed").
    Returns:
        dict:
            A dictionary where each key corresponds to a model name, and each value
            contains another dictionary mapping each temporal chunk (start_year–end_year)
            to the downloaded dataset.
    """

    dfs_models = {}                                                  # Main dictionary
    base_dir = os.getcwd()                                           # base_dir = os.getcwd() obtain current folder
    with open(os.path.join(base_dir, file_json)) as f:
        models = json.load(f)                                        # Read models from json file
    for model in models:                                             # Iterate through the models and download the data
        gcm = models[model]["gcm"]
        rcm = models[model]["rcm"]
        # ensemble_orography = models[model]["ensemble_orography"]
        ensemble_model = models[model]["ensemble_model"]
        start_years = models[model]["start_years"]
        end_years = models[model]["end_years"]
        dfs_chunks = {}                                              # Dictionary to store temporal chunks. Chunks can be: 1950-1950,1951-1955,...,1971-1975

        for sy, ey in zip(start_years, end_years):                   # Loop over each temporal chunk

            request_models = [
                (
                    f"{model}_{sy}_{ey}",
                    {
                        "domain": "europe",                                         # fixed
                        "experiment": ["historical", "rcp_4_5"],                    # change with rcp_8_5
                        "horizontal_resolution": "0_11_degree_x_0_11_degree",       # fixed
                        "temporal_resolution": "daily_mean",                        # fixed
                        "variable": variable,                                       # Argument of the function
                        "gcm_model": gcm,                                           # fixed
                        "rcm_model": rcm,                                           # fixed
                        "ensemble_member": ensemble_model,                          # fixed
                        "start_year": sy,                                           # Single start year
                        "end_year": ey,                                             # Single end year
                    },
                ),
            ]
            
            download_dfs(request_models, dfs_chunks)                  # Download of the dictionary
        dfs_models[model] = dfs_chunks                                # Fill the main dictionary
    return dfs_models
