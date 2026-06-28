import xarray as xr
import pandas as pd
import numpy as np

def concat_models_along_time(dfs_models):
    """
    Concatenate the temporal chunks of each model along the 'time' dimension.

    Parameters
    ----------
    dfs_models : dict
        A dictionary where each key represents a model name and each value 
        contains multiple xarray.Dataset objects corresponding to different 
        time chunks.

    Returns
    -------
    dict
        A dictionary mapping each model name to a single xarray.Dataset
        obtained by concatenating all its time chunks along the 'time' dimension.
    """
    dfs_models_concat = {}                             # Main dictionary

    for model, chunks in dfs_models.items():           # Loop over each model
        keys_sorted = sorted(chunks.keys())            # Ensure chronological order
        ds_list = [chunks[k] for k in keys_sorted]     # Extract datasets in order
        ds_concat = xr.concat(ds_list, dim="time")     # Concatenate along time
        dfs_models_concat[model] = ds_concat           # Fill the main dictionary
    return dfs_models_concat

def compute_yearly_ext(dfs_models):
    """
    Compute yearly extreme values (maximum or minimum) for each model.

    For every model dataset:
    - If 'tasmax', 'pr', and ' are present, compute the yearly maximum.
    - If 'tasmin' is present, compute the yearly minimum.

    The function resamples the data along the 'time' dimension using a
    yearly frequency ('1YE') and stores the resulting extremes in a new
    dictionary, one entry per model.
    """
    
    dfs_yearly_ext = {}                                       # Main dictionary with yearly extreme values (max or min)
    for model, ds in dfs_models.items():                      # Loop over each model
        if "tasmax" in ds:                                    # Compute yearly maximum of tasmax
            ds_yearly_ext = ds.resample(time="1YE").max()
            dfs_yearly_ext[model] = ds_yearly_ext
        if "pr" in ds:                                        # Compute yearly maximum of precipitation
            ds_yearly_ext = ds.resample(time="1YE").max()
            dfs_yearly_ext[model] = ds_yearly_ext
        if "tasmin" in ds:                                    # Compute yearly minimum of tasmin
            ds_yearly_ext = ds.resample(time="1YE").min()
            dfs_yearly_ext[model] = ds_yearly_ext
        if "sfcWind" in ds:
            ds_yearly_ext = ds.resample(time="1YE").max()     # Compute yearly maximum of wind speed
            dfs_yearly_ext[model] = ds_yearly_ext
    return dfs_yearly_ext


def split_time_windows(dfs_yearly_ext, window_length=40, shift=10):
    """
    Split yearly data into sliding time windows for each model.

    For every model dataset:
    - Extract the available years from the 'time' coordinate.
    - Generate time windows of length `window_length` years, moving forward
      by `shift` years between consecutive windows.
    - For each window, select the subset of data whose years fall within
      the window range (start_year --> end_year).
    - Store each windowed dataset in a dictionary indexed by (start_year, end_year).

    The function returns a dictionary where each model is associated with
    multiple time-window datasets, useful for analyzing long-term climate
    extremes over overlapping periods.
    """
    dfs_window = {}                                             # Main dictionary with data divided by time windows

    for model, ds in dfs_yearly_ext.items():                    # Loop over each model
        years = ds["time"].dt.year.values
        min_year, max_year = int(years.min()), int(years.max())
        windows = [
            (start, start + window_length - 1)                  # For each start (year), it generates a time window "window_length - 1" long.
            for start in range(min_year, max_year + 1, shift)
            if start + window_length - 1 <= max_year            # Exclude time windows that end beyond max_year.
        ]
        windowed_data = {}                                      # Fill the dictionary with only time windows (?)

        for start, end in windows:
            mask = (ds["time"].dt.year >= start) & (ds["time"].dt.year <= end)
            ds_window = ds.sel(time=mask)
            windowed_data[(start, end)] = ds_window
            print(f"model: {model}, window: {start}/{end}, shape: {dict(ds_window.sizes)}")
        dfs_window[model] = windowed_data

    return dfs_window

def new_ev1_param(data, T_r=50, method='LSM', value='positive'):
    original_data = data
    data = np.asarray(data).astype(float)
    p = 1 / T_r
    yp = -np.log(-np.log(1 - p))
    N = data.shape[0]
    pp = np.arange(N, 0, -1) / (N + 1)
    loglog_pp = np.log(-np.log(pp)).reshape(N, 1, 1)

    if value == 'positive':
        data_sorted = np.sort(data, axis=0)[::-1]

        if method == 'LSM':
            parmhat_2 = (
                (np.sum(data_sorted, axis=0)**2 - N * np.sum(data_sorted**2, axis=0)) /
                (N * np.sum(data_sorted * loglog_pp, axis=0)
                 - np.sum(data_sorted, axis=0) * np.sum(loglog_pp, axis=0)))
            parmhat_1 = (np.mean(data_sorted, axis=0)
                + np.sum(loglog_pp * parmhat_2, axis=0) / N)

        elif method == 'MOM':
            mean_val = np.mean(data_sorted, axis=0)
            std_val = np.std(data_sorted, ddof=1, axis=0)
            parmhat_2 = np.sqrt(6) / np.pi * std_val
            parmhat_1 = mean_val - 0.5772157 * parmhat_2


    elif value == 'negative':

        if method == 'MOM':
            data_sorted = np.sort(data, axis=0)[::-1]
            mean_val = np.mean(data_sorted, axis=0)
            std_val = np.std(data_sorted, ddof=1, axis=0)
            parmhat_2 = -np.sqrt(6) / np.pi * std_val
            parmhat_1 = mean_val - 0.5772157 * (-parmhat_2)

        elif method == 'LSM':
            data_sorted = np.sort(data, axis=0)
            parmhat_2 = ((np.sum(data_sorted, axis=0)**2 - N * np.sum(data_sorted**2, axis=0)) /
                (N * np.sum(data_sorted * loglog_pp, axis=0)
                 - np.sum(data_sorted, axis=0) * np.sum(loglog_pp, axis=0)))
            parmhat_1 = (np.mean(data_sorted, axis=0) + np.sum(loglog_pp * parmhat_2, axis=0) / N)

    R_value = parmhat_1 + parmhat_2 * yp

    new_dict = {'lat': original_data['lat'],'lon': original_data['lon'],'rlat': original_data['rlat'],'rlon': original_data['rlon']}
    new_data = xr.DataArray(data=R_value,dims=['rlat', 'rlon'],coords=new_dict)
    return new_data

def compute_window_results(dfs_window, T_r=50, variable="tasmax", method='MOM'):
    """
    Compute the temporal mean for each model and
    each defined time window.
    """
    dfs_window_means = {}
    dfs_window_cov = {}
    dfs_window_charact = {}

    positive_vars = {"tasmax", "pr", "sfcWind"}

    for model, windows in dfs_window.items():

        window_means = {}
        window_cov = {}
        window_charact = {}

        for (start, end), ds_window in windows.items():
            
            # Estrai la variabile specifica
            da_window = ds_window[variable]

            # Mean value
            window_means[(start, end)] = da_window.mean(dim="time")
            
            # COV
            window_cov[(start, end)] = (
                da_window.std(dim="time") / da_window.mean(dim="time")
            )

            # Characteristic value (EV1)
            if variable in positive_vars:
                value_type = "positive"
            elif variable == "tasmin":
                    value_type = "negative"

            window_charact[(start, end)] = new_ev1_param(
                da_window,
                T_r=T_r,
                method=method,
                value=value_type
            )

        dfs_window_means[model] = window_means
        dfs_window_cov[model] = window_cov
        dfs_window_charact[model] = window_charact

    return dfs_window_means, dfs_window_cov, dfs_window_charact


def compute_fc_from_charact(dfs_charact, variable):
    """
    Compute the factor of change (fc) from dfs_charact.

    For:
    - tasmax, tasmin: fc = difference with respect to the first time window
    - pr, sfcWind:   fc = ratio with respect to the first time window

    Parameters
    ----------
    dfs_charact : dict
        Dictionary structured as dfs_charact[model][(start, end)] = xr.DataArray
    variable: str
        Climate variable name ('tasmax', 'tasmin', 'pr', 'sfcWind')

    Returns
    -------
    dfs_fc : dict
        Dictionary with the same structure as dfs_charact containing fc values
    """

    if variable not in ["tasmax", "tasmin", "pr", "sfcWind"]:
        raise ValueError(f"Variable '{variable}' not supported for fc computation")

    dfs_fc = {}

    for model, windows in dfs_charact.items():

        sorted_windows = sorted(windows.keys(), key=lambda x: x[0])

        ref_window = sorted_windows[0]
        ref_data = windows[ref_window]

        model_fc = {}

        for window in sorted_windows:
            current_data = windows[window]

            if variable in ["tasmax", "tasmin"]:
                # difference
                fc = current_data - ref_data

            elif variable in ["pr", "sfcWind"]:
                # division
                fc = current_data / ref_data

            model_fc[window] = fc

        dfs_fc[model] = model_fc

    return dfs_fc

def extract_results(dfs_results, lat, lon):
    """
    Finds the closest (rlat,rlon) values to the given (lat, lon) for each model 
    and each available time window (period) in dfs_results. The function first converts 
    the input geographic coordinates into the corresponding model grid coordinates,
    and only after that extracts the matching dataframes.
    """
    
    coords = {}
    result_dfs = {}

    for key in dfs_results:
        coords[key] = {}
        result_dfs[key] = {}

        for period in dfs_results[key].keys():
            dfs = dfs_results[key][period]

            dist = (dfs.lat - lat)**2 + (dfs.lon - lon)**2
            idx = dist.argmin(dim=("rlat", "rlon"))

            rlat_idx = idx["rlat"]
            rlon_idx = idx["rlon"]

            rlat_value = dfs.rlat.isel(rlat=rlat_idx).item()
            rlon_value = dfs.rlon.isel(rlon=rlon_idx).item()

            coords[key] = (rlat_value, rlon_value)

            result_dfs[key][period] = dfs.sel(
                rlat=rlat_value,
                rlon=rlon_value,
                method="nearest"
            )


    return coords, result_dfs

def export_csv(dfs, label, out_filename):
    """
    Save all the data in a .csv file, and export it.
    """

    all_models = []

    for model, windows in dfs.items():
        print("Processing model:", model)

        df_model = None

        for (start, end), da in windows.items():
            da = da.compute()

            lat2d  = da["lat"].values
            lon2d  = da["lon"].values
            rlat1d = da["rlat"].values
            rlon1d = da["rlon"].values
            vals   = da.values

            nlat, nlon = vals.shape
            records = []

            for i in range(nlat):
                for j in range(nlon):
                    v = vals[i, j]
                    if np.isnan(v):
                        continue

                    records.append({
                        "lat":  float(lat2d[i, j]),
                        "lon":  float(lon2d[i, j]),
                        "rlat": float(rlat1d[i]),
                        "rlon": float(rlon1d[j]),
                        f"{label}_{start}_{end}": float(v)
                    })

            df_window = pd.DataFrame.from_records(records)

            if df_model is None:
                df_model = df_window
            else:
                df_model = df_model.merge(
                    df_window,
                    on=["lat","lon","rlat","rlon"],
                    how="outer"
                )

        df_model.insert(0, "model", model)

        all_models.append(df_model)

    final_df = pd.concat(all_models, ignore_index=True)
    final_df.to_csv(
        out_filename,
        index=False,
        sep=";",
        decimal=",",
        float_format="%.6f"
    )

    print("CSV saved:", len(final_df), "rows ->", out_filename)