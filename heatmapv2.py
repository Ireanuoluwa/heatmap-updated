import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from collections import defaultdict
import datetime
import os

st.title("WOW LIVE ACTIVITY DASHBOARD")

PASSWORD = st.secrets.get("admin_password", "changeme")  

manual_name_map = {
    "Funmi": "Gloria",
    "Anu": "Moyin",
    "Faithy": "Faith",
    "Oyinade Priscilla": "Oyinade",
    "Dora": "Dorathy",
    "Barisuka Goodluck": "Barisuka",
    "Bee❤️": "Bisoye",
    "joy387115": "Joy",
    "Princess Esther Etang": "Esther Etang",
    "~MJ": "Reme",
    "El👑": "El",
    "~ M&J Wears": "Baridule"
    
}

dashboard_names = [
    "Adeola", "Baridule", "Barisuka", "Bisoye", "Christabel", "Dorathy",
    "Esther Chioma", "Esther Etang", "El", "Faith", "Gloria", "Joy",
    "Moyin", "Oyinkan", "Peace", "Reme", "Shirley", "Tiaraoluwa",
    "Tolani", "Oyinade"
]

HEATMAP_FILE = "latest_heatmap.csv"
DATE_FILE = "latest_dates.csv"

# ---------- 1. Show the latest heatmap on page load (if exists) ----------
def display_heatmap_from_csv():
    if os.path.exists(HEATMAP_FILE) and os.path.exists(DATE_FILE):
        df = pd.read_csv(HEATMAP_FILE, index_col=0)
        with open(DATE_FILE, "r") as f:
            selected_dates = f.read().strip().split(",")
        cmap = sns.color_palette(["indianred", "yellow", "lightseagreen"])
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            df,
            annot=False,
            cmap=cmap,
            cbar=True,
            ax=ax,
            cbar_kws={
                "ticks": [0, 0.5, 1],
                "format": plt.FuncFormatter(
                    lambda x, _: (
                        "Non-active" if x == 0 else
                        "Unavailable (Took Permission)" if x == 0.5 else
                        "Active"
                    )
                )
            }
        )
        ax.set_title("Latest Activity Heatmap", pad=12)
        ax.set_xlabel("Dates")
        ax.set_ylabel("Names")
        st.pyplot(fig)
        st.caption(f"Heatmap last updated for dates: {', '.join(selected_dates)}")

st.subheader("Latest Heatmap (Auto-Refreshed)")
display_heatmap_from_csv()

uploaded_file = st.file_uploader("Upload your WhatsApp text file", type=['txt'])

if uploaded_file is not None:
    lines = uploaded_file.read().decode("utf-8").splitlines()
    date_pattern = re.compile(r'^\[(\d+/\d+/\d+),')
    unique_dates = set()
    for line in lines:
        match = date_pattern.match(line)
        if match:
            unique_dates.add(match.group(1))
    sorted_dates = sorted(unique_dates, key=lambda x: datetime.datetime.strptime(x, "%m/%d/%y"))
    # By default, pick last 5 dates (or all if < 5)
    selected_dates = st.multiselect(
        "Select dates to display (MM/DD/YY):",
        options=sorted_dates,
        default=sorted_dates[-5:] if len(sorted_dates) >= 5 else sorted_dates
    )

    if selected_dates:
        st.markdown("### Mark Unavailable Users")
        unavailable_by_date = {}
        for date in selected_dates:
            unavailable_by_date[date] = st.multiselect(
                f"Who was unavailable on {date}?",
                options=dashboard_names,
                key=f"unavailable_{date}"
            )
        # Password input
        password = st.text_input("Enter password to refresh heatmap:", type="password")
        if st.button("Refresh Heatmap"):
            # ------------- AUTH -------------
            if password != PASSWORD:  # Replace with your chosen password
                st.error("Incorrect password. Please try again.")
            else:
                # ------------ DATA PROCESSING -------------
                message_pattern = re.compile(r'^\[(\d+/\d+/\d+),.*?\] (.*?):')
                sender_date_counts = defaultdict(lambda: {date: 0 for date in selected_dates})
                for line in lines:
                    match = message_pattern.match(line)
                    if match:
                        date, sender = match.groups()
                        if date in selected_dates:
                            sender_date_counts[sender.strip()][date] += 1

                def normalize_name(name):
                    name = name.strip()
                    name = re.sub(r'[^A-Za-z ]', '', name)
                    return name

                name_mapping = {}
                for raw_name in sender_date_counts.keys():
                    mapped_name = manual_name_map.get(raw_name)
                    if mapped_name:
                        name_mapping[raw_name] = mapped_name
                    else:
                        raw_norm = normalize_name(raw_name).lower()
                        for dash_name in dashboard_names:
                            if raw_norm in dash_name.lower() or dash_name.lower() in raw_norm:
                                name_mapping[raw_name] = dash_name
                                break
                        else:
                            name_mapping[raw_name] = raw_name

                heatmap_data = []
                for name in dashboard_names:
                    counts = sender_date_counts.get(name, {date: 0 for date in selected_dates})
                    for raw, mapped in name_mapping.items():
                        if mapped == name:
                            counts = sender_date_counts[raw]
                            break
                    row = []
                    for date in selected_dates:
                        if name in unavailable_by_date[date]:
                            row.append(0.5)  # Unavailable
                        elif counts[date] > 0:
                            row.append(1)    # Active
                        else:
                            row.append(0)    # Non-active
                    heatmap_data.append(row)

                df = pd.DataFrame(heatmap_data, index=dashboard_names, columns=selected_dates)
                # Save heatmap as csv so it persists
                df.to_csv(HEATMAP_FILE)
                # Save selected_dates for reference
                with open(DATE_FILE, "w") as f:
                    f.write(",".join(selected_dates))

                cmap = sns.color_palette(["indianred", "yellow", "lightseagreen"])
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(
                    df,
                    annot=False,
                    cmap=cmap,
                    cbar=True,
                    ax=ax,
                    cbar_kws={
                        "ticks": [0, 0.5, 1],
                        "format": plt.FuncFormatter(
                            lambda x, _: (
                                "Non-active" if x == 0 else
                                "Unavailable (Took Permission)" if x == 0.5 else
                                "Active"
                            )
                        )
                    }
                )
                ax.set_title("Activity Heatmap", pad=12)
                ax.set_xlabel("Dates")
                ax.set_ylabel("Names")
                st.pyplot(fig)
                st.success("Heatmap updated! All users will see the latest version.")

else:
    st.write("Please upload a WhatsApp .txt file to get started.")

