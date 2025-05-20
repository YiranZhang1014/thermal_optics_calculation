import streamlit as st


def calculate(isolar_path, r_path, lower=300, upper=2400, separator="\t"):
    import pandas as pd

    # 读取数据
    isolar = pd.read_csv(
        isolar_path, sep=separator, header=None, names=["wavelength_nm", "I_solar"]
    )
    r = pd.read_csv(r_path, sep=separator, header=None, names=["wavelength_nm", "R"])

    # 过滤掉小数点后有数字的行
    isolar_int = isolar[isolar["wavelength_nm"] % 1 == 0]
    r_int = r[r["wavelength_nm"] % 1 == 0]

    isolar_filtered_int = isolar_int[
        (isolar_int["wavelength_nm"] >= lower) & (isolar_int["wavelength_nm"] <= upper)
    ]
    r_filtered_int = r_int[
        (r_int["wavelength_nm"] >= lower) & (r_int["wavelength_nm"] <= upper)
    ]

    # 明确创建副本
    isolar_filtered_int = isolar_int[
        (isolar_int["wavelength_nm"] >= lower) & (isolar_int["wavelength_nm"] <= upper)
    ].copy()
    r_filtered_int = r_int[
        (r_int["wavelength_nm"] >= lower) & (r_int["wavelength_nm"] <= upper)
    ].copy()

    isolar_filtered_int["wavelength_um"] = isolar_filtered_int["wavelength_nm"] / 1000
    r_filtered_int["wavelength_um"] = r_filtered_int["wavelength_nm"] / 1000

    # Restrict to common range
    isolar_range = isolar_filtered_int[
        (isolar_filtered_int["wavelength_um"] >= 0.5)
        & (isolar_filtered_int["wavelength_um"] <= 2.4)
    ]
    r_range = r_filtered_int[
        (r_filtered_int["wavelength_um"] >= 0.5)
        & (r_filtered_int["wavelength_um"] <= 2.4)
    ]

    # Merge on common wavelength values
    merged = pd.merge(
        isolar_range[["wavelength_um", "I_solar"]],
        r_range[["wavelength_um", "R"]],
        on="wavelength_um",
    )

    # ------------------- Handle the missing value -------------------
    merged = merged.dropna()
    merged["I_solar"] = merged["I_solar"].astype(float)
    merged["R"] = merged["R"].astype(float)
    merged["wavelength_um"] = merged["wavelength_um"].astype(float)
    # --------------------Handle the missing value end-------------------

    # Convert R from percent to 0-1
    merged["R"] /= 100

    # Assume uniform delta_lambda = 0.001 μm
    delta_lambda = 0.001

    # Compute weighted reflectance
    numerator = (merged["I_solar"] * merged["R"]).sum() * delta_lambda
    denominator = merged["I_solar"].sum() * delta_lambda
    R_solar_discrete = numerator / denominator

    # 保留4位小数
    R_solar_discrete = round(R_solar_discrete, 6)

    return float(R_solar_discrete)


st.title("Solar Reflectivity Calculator")

# 上传文件
isolar_file = st.file_uploader("Upload isolar file", type=["txt", "csv"])
r_file = st.file_uploader("Upload r file", type=["txt", "csv"])

# 参数输入
lower = st.number_input("Lower limit", value=300)
upper = st.number_input("Upper limit", value=2400)
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
