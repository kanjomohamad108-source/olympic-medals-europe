# olympic-medals-europe
Interactive Streamlit app for visualizing Olympic Summer Games medals of European countries from 1996 to 2024.

## Project overview

This project visualizes the most successful European countries in the Olympic Summer Games between 1996 and 2024.  
The application uses an interactive choropleth map of Europe and allows users to explore medal counts by year or across the full period.

Russia and Turkey are treated as European countries in this project.

## Features

- Interactive choropleth map of Europe
- Selection between single Olympic years and the full period 1996–2024
- Top 3 countries display
- Detailed medal statistics for a selected country
- Germany preselected by default
- Tooltip support for countries with medals
- Gold-medal-based color scale

## Technologies

- Python
- Streamlit
- Plotly Express
- pandas
- requests

## Files

- `olympic_medals_app.py` – main Streamlit application
- `olympic_medals_europe.csv` – medal dataset
- `Belegarbeit-Datenvisualisierung.pdf` – project documentation

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/DEIN-USERNAME/olympic-medals-europe.git
