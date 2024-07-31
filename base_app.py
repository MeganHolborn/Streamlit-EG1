"""
    A Streamlit webserver application for generating user ratings based on historical preferences.
"""

# Import dependencies
import os
import re
import string
import time

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from recommenders.models.surprise.surprise_utils import predict

# Load data
anime_data = pd.read_csv(r"data/anime.csv")
train_data = pd.read_csv(r"data/train.csv")

# Load pickled models
collab_svd_tuned = pd.read_pickle(r"pickles/collab_svd_tuned.pkl")


# Function to clean anime titles
def clean_titles(name):
    return re.sub("[^a-zA-Z0-9 ]", " ", name)


# Function to generate rating predictions using a collaborative recommender
def generate_predictions(user_ids: list, anime_ids: list, model):
    # Generate predictions
    data = pd.DataFrame()
    data["anime_id"] = anime_ids
    data["user_id"] = user_ids
    start_time = time.time()
    svd_predictions = predict(
        collab_svd_tuned, data, usercol="user_id", itemcol="anime_id"
    )
    pred_time = time.time() - start_time

    # Format the data
    svd_predictions["ID"] = (
        svd_predictions["user_id"].astype(str)
        + "_"
        + svd_predictions["anime_id"].astype(str)
    )
    svd_predictions["rating"] = round(svd_predictions["prediction"], 2)
    svd_predictions = svd_predictions[["ID", "rating"]]

    return svd_predictions, pred_time


# Function to generate n recommendations using a collaborative recommender
def get_recommendations(user_id: int, model, n):
    # Get a list of all items
    all_items = list(
        train_data[~(train_data["user_id"] == user_id)]["anime_id"].unique()
    )

    # Predict ratings for all items for the given user
    test_data = pd.DataFrame(columns=["user_id", "anime_id"])
    test_data["anime_id"] = all_items
    test_data["user_id"] = user_id
    predictions = predict(model, test_data, usercol="user_id", itemcol="anime_id")

    # Sort predictions by estimated rating
    recommendations = predictions.sort_values(by="prediction", ascending=False).iloc[
        :n, :
    ]
    return recommendations


# The main function where we will build the actual app
def main():
    """Anime Recommender System"""

    # Creating sidebar with logo and navigation
    image = Image.open("Animex.png")
    st.sidebar.image(image)

    options = [
        "About",
        "Predict Your Ratings",
        "Your Recommendations",
        "Behind the Scenes",
    ]

    selection = st.sidebar.radio("Navigate To", options)

    # Building out the "About" page
    if selection == "About":

        # Create a banner

        # Add a title and banner
        st.image(
            "https://blog.playstation.com/tachyon/2016/10/unnamed-file-6.jpg",
            use_column_width=True,
        )

        st.title("Personalized Anime Recommender")
        st.divider()

        # Add information divided by subsections
        st.subheader(":grey[Introduction]")
        st.markdown("Some information here")

        st.subheader(":grey[App Features]")
        st.markdown("Some information here")

        st.subheader(":grey[How to Use the App]")
        st.markdown("Some information here")

        st.subheader(":grey[Meet the Team]")
        st.markdown("Some information here")

        # Add footer with contact information
        footer_html = """<div style='text-align: center;'>
        <p>Developed by Kawaii Consulting | Contact us at: info@kawaiiconsulting.com</p>
        </div>"""
        st.markdown("#")
        st.divider()
        st.markdown(footer_html, unsafe_allow_html=True)

    # Building out the "Get Recommendations" page
    if selection == "Your Recommendations":

        # Add a title and divider
        st.title("Your Recommendations")
        st.divider()

        # Add an information box
        st.info(
            "Get personalised recommendations based on your favourite shows and genres."
        )

        # Creating a box for User ID input
        user_id = st.number_input(
            "Enter a valid User ID",
            value=None,
            placeholder="User ID",
            step=1,
        )

        try:
            # Check if the user_id exists in the training data
            if user_id in train_data["user_id"].values:
                pass
            else:
                # Raise a ValueError if the user_id is not found
                raise ValueError("User ID not found")
        except ValueError as e:
            # Display an error message in Streamlit
            st.error(str(e))

        # Select number of recommendations
        n_recommendations = st.slider(
            "Number of Recommendations",
            1,
            30,
        )

        # Generate recommendations
        if st.button("Get Recommendations"):

            recommended_anime = get_recommendations(
                user_id, collab_svd_tuned, n_recommendations
            )

            recommended_anime = pd.merge(
                recommended_anime[["anime_id", "prediction"]],
                anime_data[["anime_id", "name"]],
            )

            recommended_anime = recommended_anime[["name", "prediction"]].rename(
                columns={"name": "Anime Title", "prediction": "Predicted Rating"}
            )

            recommended_anime.reset_index(drop=True, inplace=True)

            # When model has successfully run, will print prediction
            st.text("Your Recommended Anime:")
            st.table(recommended_anime)

        # Add footer with contact information
        footer_html = """<div style='text-align: center;'>
        <p>Developed by Kawaii Consulting | Contact us at: info@kawaiiconsulting.com</p>
        </div>"""
        st.markdown("#")
        st.divider()
        st.markdown(footer_html, unsafe_allow_html=True)

    # Building out the "Predicted Ratings" page
    if selection == "Predict Your Ratings":

        # Add a title and divider
        st.title("Predict Your Ratings")
        st.divider()

        # Add an information box
        st.info(
            "Predict what rating you would give an anime you haven't watched before."
        )

        # Creating a box for User ID input
        user_id = st.number_input(
            "Enter a valid User ID",
            value=None,
            placeholder="User ID",
            step=1,
        )

        try:
            # Check if the user_id exists in the training data
            if user_id in train_data["user_id"].values:
                # Get a list of items that the user has not rated before
                unrated_anime = list(
                    train_data[train_data["user_id"] != user_id]["anime_id"].unique()
                )

                unrated_anime_titles = anime_data[
                    anime_data["anime_id"].isin(unrated_anime)
                ]["name"].unique()

                # Create an anime title selection box
                selected_anime = st.selectbox("Select an Anime", unrated_anime_titles)
            else:
                # Raise a ValueError if the user_id is not found
                raise ValueError("User ID not found")
        except ValueError as e:
            # Display an error message in Streamlit
            st.error(str(e))

        # Get the user's predicted rating for the selected anime
        if st.button("Predict Your Ratings"):

            selected_anime_id = anime_data[anime_data["name"] == str(selected_anime)][
                "anime_id"
            ].values[0]

            prediction, prediction_time = generate_predictions(
                [user_id], [selected_anime_id], collab_svd_tuned
            )

            prediction = prediction["rating"].values[0]

            st.write("Predicted Rating:", prediction)

        # Add footer with contact information
        footer_html = """<div style='text-align: center;'>
        <p>Developed by Kawaii Consulting | Contact us at: info@kawaiiconsulting.com</p>
        </div>"""
        st.markdown("#")
        st.divider()
        st.markdown(footer_html, unsafe_allow_html=True)

    # Building out the "Behind the Scenes" page
    if selection == "Behind the Scenes":

        # Add a title
        st.title("Behind the Scenes")
        st.divider()

        # Add information divided by subsections
        st.subheader(":grey[Project Methods]")
        st.markdown("Some information here")

        st.subheader(":grey[Future Work]")
        st.markdown("Some information here")

        # Add footer with contact information
        footer_html = """<div style='text-align: center;'>
        <p>Developed by Kawaii Consulting | Contact us at: info@kawaiiconsulting.com</p>
        </div>"""
        st.markdown("#")
        st.divider()
        st.markdown(footer_html, unsafe_allow_html=True)


# Required to let Streamlit instantiate our web app.
if __name__ == "__main__":
    main()
