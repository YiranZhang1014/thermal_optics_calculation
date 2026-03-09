import streamlit as st


def calculate(isolar_path, r_path, lower=300, upper=2400, separator="\t"):
    import pandas as pd
    import numpy as np

    # Read the data files
    isolar = pd.read_csv(
        isolar_path, sep=separator, header=None, names=["wavelength_nm", "I_solar"]
    )
    r = pd.read_csv(r_path, sep=separator, header=None, names=["wavelength_nm", "R"])

    # Ensure data is numeric and drop any rows with text/missing values (e.g., headers)
    isolar["wavelength_nm"] = pd.to_numeric(isolar["wavelength_nm"], errors='coerce')
    isolar["I_solar"] = pd.to_numeric(isolar["I_solar"], errors='coerce')
    r["wavelength_nm"] = pd.to_numeric(r["wavelength_nm"], errors='coerce')
    r["R"] = pd.to_numeric(r["R"], errors='coerce')

    isolar = isolar.dropna().sort_values("wavelength_nm")
    r = r.dropna().sort_values("wavelength_nm")

    # Determine the valid overlapping range between the two datasets and the user bounds
    overlap_min = max(isolar["wavelength_nm"].min(), r["wavelength_nm"].min(), lower)
    overlap_max = min(isolar["wavelength_nm"].max(), r["wavelength_nm"].max(), upper)

    # Filter the solar spectrum to this common range
    isolar_valid = isolar[
        (isolar["wavelength_nm"] >= overlap_min) & (isolar["wavelength_nm"] <= overlap_max)
    ].copy()

    # Convert wavelengths from nm to um to standardise units
    isolar_valid["wavelength_um"] = isolar_valid["wavelength_nm"] / 1000
    wl_common_um = isolar_valid["wavelength_um"].values
    I_solar_common = isolar_valid["I_solar"].values

    r_wl_um = r["wavelength_nm"].values / 1000
    r_val = r["R"].values / 100.0  # Convert reflectance from percentage to a fraction (0 to 1)

    # Interpolate the reflectance data onto the solar spectrum's wavelength grid
    # This is the scientific approach to harmonise mismatched data points
    R_interp = np.interp(wl_common_um, r_wl_um, r_val)

    # Clip the interpolated reflectance to physical limits to prevent anomalies
    R_interp = np.clip(R_interp, 0.0, 1.0)

    # Calculate the weighted reflectance using trapezoidal integration
    numerator_trapz = np.trapezoid(I_solar_common * R_interp, x=wl_common_um)
    denominator_trapz = np.trapezoid(I_solar_common, x=wl_common_um)

    R_solar_trapz = numerator_trapz / denominator_trapz
    R_solar_trapz = round(R_solar_trapz, 6)

    # The final calculated value
    return float(R_solar_trapz)


st.title("Solar Reflectivity Calculator")

# 上传文件
isolar_file = st.file_uploader("Upload isolar file", type=["txt", "csv"])
r_file = st.file_uploader("Upload r file", type=["txt", "csv"])

# 参数输入
lower = st.number_input("Lower limit (> 300)", value=300)
upper = st.number_input("Upper limit (< 2500)", value=2500)
separator = st.text_input("Separator", value="\\t")  # 默认tab

# 只在文件和参数齐全时启用按钮
if isolar_file and r_file:
    if st.button("Calculate"):
        # 存储上传的文件为临时文件
        isolar_temp = "temp_isolar.txt"
        r_temp = "temp_r.txt"

        with open(isolar_temp, "wb") as f:
            f.write(isolar_file.getbuffer())
        with open(r_temp, "wb") as f:
            f.write(r_file.getbuffer())

        try:
            result = calculate(
                isolar_temp,
                r_temp,
                lower,
                upper,
                separator.encode().decode("unicode_escape"),
            )
            st.success(f"Calculation result: {result}")
        except Exception as e:
            st.error(f"Error during calculation: {e}")

else:
    st.info("Please upload both files and set the parameters.")
