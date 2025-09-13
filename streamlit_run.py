# ---
# lambda-test: false  # auxiliary-file
# ---
# ## Demo Streamlit application.
#
# This application is the example from https://docs.streamlit.io/library/get-started/create-an-app.
#
# Streamlit is designed to run its apps as Python scripts, not functions, so we separate the Streamlit
# code into this module, away from the Modal application code.
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import modal
from typing import Union


def get_supabase_client() -> Client:
    load_dotenv()
    SUPABASE_URL, SUPABASE_API_KEY = os.getenv("SUPABASE_URL"), os.getenv(
        "SUPABASE_KEY"
    )
    return create_client(SUPABASE_URL, SUPABASE_API_KEY)


def select_rows_from_table(
    client: Client, table_name: str
) -> dict[str, Union[str, float]]:
    response = client.table(table_name).select("*").limit(50).execute()
    return response.data


def get_supabase_client() -> Client:
    import os
    from dotenv import load_dotenv

    load_dotenv()
    SUPABASE_URL, SUPABASE_API_KEY = os.getenv("SUPABASE_URL"), os.getenv(
        "SUPABASE_KEY"
    )
    return create_client(SUPABASE_URL, SUPABASE_API_KEY)


def select_rows_from_table(
    client: Client, table_name: str
) -> dict[str, Union[str, float]]:
    response = client.table(table_name).select("*").limit(50).execute()
    return response.data


def main():
    import numpy as np
    import pandas as pd
    import streamlit as st
    import plotly.express as px

    st.title("Uber pickups in NYC!")

    DATE_COLUMN = "date/time"
    DATA_URL = (
        "https://s3-us-west-2.amazonaws.com/"
        "streamlit-demo-data/uber-raw-data-sep14.csv.gz"
    )

    @st.cache_data
    def load_data(nrows):
        data = pd.read_csv(DATA_URL, nrows=nrows)

        def lowercase(x):
            return str(x).lower()

        data.rename(lowercase, axis="columns", inplace=True)
        data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
        return data

    data_load_state = st.text("Loading data...")
    data = load_data(10000)
    data_load_state.text("Done! (using st.cache_data)")

    if st.checkbox("Show raw data"):
        st.subheader("Raw data")
        st.write(data)

    st.subheader("Number of pickups by hour")
    hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0, 24))[0]
    st.bar_chart(hist_values)

    # Some number in the range 0-23
    hour_to_filter = st.slider("hour", 0, 23, 17)
    filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]

    st.subheader("Map of all pickups at %s:00" % hour_to_filter)
    st.map(filtered_data)

    # Interactivity: pick available plotly color palettes
    plotting_color = st.color_picker(label="Select Color of Charts", value="#83c9ff")

    # New chart / visualization one: Let's see how the number of pickups have changed through the days
    st.subheader("Number of pickups per day")
    pickups_grouped_by_day = (
        data.assign(date=data["date/time"].dt.date)
        .groupby("date", sort=True)
        .agg(pickup_count=("lat", "count"))
        .reset_index()
    )

    pickups_grouped_by_day["date"] = pd.to_datetime(
        pickups_grouped_by_day["date"]
    ).dt.strftime("%B %-d")

    pickups_per_day_fig = px.bar(
        data_frame=pickups_grouped_by_day,
        x="date",
        y="pickup_count",
        text="pickup_count",
    )
    pickups_per_day_fig.update_traces(
        textposition="outside", marker_color=plotting_color
    )

    st.plotly_chart(pickups_per_day_fig, config={"scrollZoom": False})

    # New chart two: Analyzing the 5 most popular pick-up destinations
    st.subheader("Top 5 most popular pickup destinations")

    # Latitude and longitude are very precise, and I don't need that. Only extract the top 3 decimals from both
    most_popular_pickup_locations = (
        data.assign(lat_trunc=data["lat"].round(3), lon_trunc=data["lon"].round(3))
        .groupby(by=["lat_trunc", "lon_trunc"])
        .size()
        .reset_index(name="pickup_count")
    )
    most_popular_pickup_locations = most_popular_pickup_locations.nlargest(
        n=5, columns="pickup_count"
    )

    # Manually found what these places are
    most_popular_pickup_locations = most_popular_pickup_locations.assign(
        location=[
            "John F. Kennedy International Airport, Terminal 4",
            "LaGuardia Airport",
            "Chelsea Market",
            "Newark Liberty International Airport",
            "John F. Kennedy International Airport, Terminal 5",
        ]
    )

    most_popular_pickup_locations_fig = px.bar(
        data_frame=most_popular_pickup_locations,
        x="location",
        y="pickup_count",
        text="pickup_count",
    )

    most_popular_pickup_locations_fig.update_traces(
        textposition="inside", marker_color=plotting_color
    )

    st.plotly_chart(most_popular_pickup_locations_fig, config={"scrollZoom": False})

    st.title("Supabase Integration")
    client = get_supabase_client()
    puffle_rows = (
        pd.DataFrame(select_rows_from_table(client, "puffles"))
        .set_index("id")
        .sort_index()
    )
    st.dataframe(puffle_rows)

    # Let's figure out the most popular color within our dataset
    puffles_grouped_by_colors = (
        puffle_rows.groupby(by="color")
        .agg(puffle_count=("name", "count"))
        .reset_index()
        .sort_values(by="puffle_count", ascending=False)
    )

    puffles_grouped_by_colors_fig = px.bar(
        data_frame=puffles_grouped_by_colors,
        x="color",
        y="puffle_count",
        color="color",
        color_discrete_map={
            x: x.lower() if x != "Rainbow" else "papayawhip"
            for x in puffles_grouped_by_colors["color"]
        },
        # color_discrete_sequence=px.colors.sequential.Rainbow
    )

    puffles_grouped_by_colors_fig.update_layout(
        showlegend=False, xaxis_title="Puffle Color", yaxis_title="Number of Puffles"
    )

    st.plotly_chart(puffles_grouped_by_colors_fig, config={"scrollZoom": False})


if __name__ == "__main__":
    main()
