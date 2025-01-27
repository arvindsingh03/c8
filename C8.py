import pandas as pd
from ortools.sat.python import cp_model
import streamlit as st
import plotly.express as px
import base64

# Set background image
def set_background_image(image_path):
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{base64_image}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background_image("C:/Users/PC/Downloads/Telegram Desktop/113.png")

# Improved IREQ Algorithm
class ArcticIREQCalculator:
    def __init__(self):
        self.STEFAN_BOLTZMANN = 5.67e-8
        self.EMISSIVITY = 0.97

    def calculate_bsa(self, weight_kg, height_cm):
        """Calculate body surface area using Du Bois formula."""
        return 0.007184 * (weight_kg**0.425) * (height_cm**0.725)

    def calculate_wind_chill(self, temp_c, wind_speed):
        """Calculate wind chill using ISO 11079 formula."""
        if wind_speed < 4.8:  # Wind speed less than 4.8 km/h has negligible impact
            return temp_c
        wind_chill = 13.12 + 0.6215 * temp_c - 11.37 * wind_speed**0.16 + 0.3965 * temp_c * wind_speed**0.16
        return round(wind_chill, 2)

    def calculate_ireq(self, air_temp, wind_speed, humidity, personal_data):
        """Calculate IREQ with physiological and environmental factors."""
        try:
            weight = max(personal_data.get('weight_kg', 70), 40)
            height = max(personal_data.get('height_cm', 170), 120)
            skin_temp = personal_data.get('skin_temp', 33)
            vo2_max = max(personal_data.get('vo2_max', 10), 10)
            body_fat_percent = personal_data.get('body_fat_percent', 20)
            brown_fat_level = personal_data.get('brown_fat_level', 1)  # 1 = low, 2 = medium, 3 = high

            t_skin = skin_temp + 273.15
            t_air = air_temp + 273.15
            va = max(wind_speed, 0.1)

            # Body surface area and heat generation
            bsa = self.calculate_bsa(weight, height)
            metabolic_heat = max(vo2_max * bsa * 58.2, 50)  # Minimum contribution of 50W

            # Adjust metabolic heat based on brown fat level
            brown_fat_factor = 1 + (brown_fat_level - 1) * 0.2  # Increase heat generation by 20% per level
            metabolic_heat *= brown_fat_factor

            # Limit the effect of wind speed (realistic cap)
            va = min(va, 40)  # Cap wind speed at 40 m/s (extreme conditions)
            
            ireq = 100  # Start with 1.0 clo (scaled by 100)
            for iteration in range(5):
                hr = 4 * self.EMISSIVITY * self.STEFAN_BOLTZMANN * ((t_skin + t_air) / 2)**3
                hc = 10.4 * (va**0.6)
                q_total = (t_skin - t_air) / ((ireq / 100) + 1 / (hr + hc))
                q_total -= metabolic_heat / bsa  # Subtract metabolic contribution

                # Ensure q_total is positive and prevent negative heat loss
                if q_total <= 0:
                    return max(ireq, 0)  # Avoid unrealistic results
                
                new_ireq = ((t_skin - t_air) / q_total - 1 / (hr + hc)) * 100
                if abs(new_ireq - ireq) < 1:
                    break
                ireq = new_ireq

            # Adjust IREQ based on body fat percentage
            body_fat_factor = 1 - (body_fat_percent / 100)  # Normalize to 0-1
            adjusted_ireq = ireq * body_fat_factor

            # Adjust IREQ based on humidity
            if humidity > 70:  # High humidity reduces insulation effectiveness
                adjusted_ireq *= 1.2  # Increase IREQ by 20%

            # Adjust IREQ for extreme cold (exponential scaling)
            adjusted_ireq *= max(1 + abs(air_temp) / 30, 1.5)  # Scale exponentially for extreme cold

            # If calculated IREQ is still below a reasonable threshold, force a safe value
            if adjusted_ireq < 100:
                return 100  # Set a minimum value for IREQ
            return int(adjusted_ireq)
        except Exception as e:
            st.error(f"IREQ calculation error: {e}")
            return 9999  # Fallback to max layers in case of error

# Layer Selection Logic
class ArcticLayerOptimizer:
    def __init__(self, layers_db):
        self.layers = sorted(layers_db, key=lambda x: x['order'])
        self.clu_map = {l['layer_id']: l['clu'] for l in self.layers}
        self.weight_map = {l['layer_id']: l['weight'] for l in self.layers}
        self.cost_map = {l['layer_id']: l['cost'] for l in self.layers}

    def recommend_layers(self, target_clu, wind_speed, humidity, activity_level, air_temp):
        """target_clu: integer value (scaled by 100)"""
        model = cp_model.CpModel()
        layer_vars = {l['layer_id']: model.NewBoolVar(f"layer_{l['layer_id']}") 
                     for l in self.layers}

        # Create a linear expression for total_clu
        total_clu_expr = sum(self.clu_map[l['layer_id']] * layer_vars[l['layer_id']] 
                             for l in self.layers)

        # Ensure target_clu is an integer
        target_clu_int = int(target_clu)

        # Constraints: only select layers with total CLU >= target_clu
        model.Add(total_clu_expr >= target_clu_int)

        # Additional constraints for realistic layering
        # 1. Always include the Base Layer (Layer 1)
        model.Add(layer_vars[1] == 1)

        # 2. Only include Wind Jacket (Layer 4) if wind speed > 5 m/s
        if wind_speed <= 5:
            model.Add(layer_vars[4] == 0)

        # 3. Only include Hard-Shell (Layer 6) if humidity > 70% or precipitation
        if humidity <= 70:
            model.Add(layer_vars[6] == 0)

        # 4. Adjust layers based on activity level
        if activity_level == 'high':
            # Reduce insulation for high activity
            model.Add(sum(layer_vars.values()) <= 3)
        elif activity_level == 'low':
            # Add more insulation for low activity
            model.Add(sum(layer_vars.values()) >= 4)

        # 5. Add insulation layers for extreme cold
        if air_temp < -40:
            model.Add(layer_vars[3] == 1)  # Always include High-Loft Fleece
            model.Add(layer_vars[7] == 1)  # Always include Extreme Cold Parka

        # 6. Add additional constraints for sub-zero temperatures
        if air_temp < 0:
            model.Add(sum(layer_vars.values()) >= 4)  # At least 4 layers for sub-zero

        # Multi-Objective Optimization: Minimize weight and cost
        total_weight_expr = sum(self.weight_map[l['layer_id']] * layer_vars[l['layer_id']] 
                                for l in self.layers)
        total_cost_expr = sum(self.cost_map[l['layer_id']] * layer_vars[l['layer_id']] 
                              for l in self.layers)
        model.Minimize(total_weight_expr + total_cost_expr)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL:
            selected_layers = sorted([l for l in self.layers 
                                     if solver.Value(layer_vars[l['layer_id']])],
                                     key=lambda x: x['order'])
            return selected_layers
        return []  # Return an empty list if no layers are selected

# Streamlit Interface
st.title("❄️ Arctic Protection System 2.0")
st.subheader("ISO 11079:2007 Compliant Full-Body Protection")

# Load CSV data
@st.cache_data
def load_data(csv_path):
    return pd.read_csv(csv_path)

data = load_data(r"C:\Users\PC\Downloads\crt.csv")

# Sidebar for Person ID selection
with st.sidebar:
    st.header("Personal Profile")
    person_id = st.selectbox("Select Person ID", data['Person_ID'].unique(), key="person_id_selectbox")
    
    # Fetch data for the selected person
    person_data = data[data['Person_ID'] == person_id].iloc[0]

    st.write(f"Name: {person_data['Name']}")
    st.write(f"Weight: {person_data['Weight_kg']} kg")
    st.write(f"Height: {person_data['Height_cm']} cm")
    st.write(f"Body Fat Percentage: {person_data['Body_Fat_Percent']}%")
    st.write(f"Skin Temperature: {person_data['Skin_Temperature_C']} °C")
    st.write(f"VO2 Max: {person_data['VO2_Max_mL_kg_min']} mL/kg/min")

    st.header("Environmental Parameters")
    air_temp = st.slider("Temperature (°C)", -60, 10, -40, key="air_temp_slider")
    wind_speed = st.slider("Wind Speed (m/s)", 0, 40, 25, key="wind_speed_slider")
    humidity = st.slider("Humidity (%)", 0, 100, 50, key="humidity_slider")
    activity_level = st.selectbox("Activity Level", ['low', 'moderate', 'high'], key="activity_level_selectbox")

# ECWCS Gen III Layers with CLO Values (scaled by 100)
LAYERS_DB = [
    {'layer_id': 1, 'clu': 30, 'order': 1, 'type': 'base', 'name': 'Lightweight Base Layer', 'weight': 0.2, 'cost': 50},
    {'layer_id': 2, 'clu': 70, 'order': 2, 'type': 'mid', 'name': 'Midweight Fleece', 'weight': 0.5, 'cost': 80},
    {'layer_id': 3, 'clu': 90, 'order': 3, 'type': 'insulation', 'name': 'High-Loft Fleece Jacket', 'weight': 0.7, 'cost': 120},
    {'layer_id': 4, 'clu': 40, 'order': 4, 'type': 'wind', 'name': 'Wind Jacket', 'weight': 0.4, 'cost': 100},
    {'layer_id': 5, 'clu': 60, 'order': 5, 'type': 'softshell', 'name': 'Soft-Shell Jacket', 'weight': 0.6, 'cost': 150},
    {'layer_id': 6, 'clu': 80, 'order': 6, 'type': 'hardshell', 'name': 'Waterproof Hard-Shell', 'weight': 0.8, 'cost': 200},
    {'layer_id': 7, 'clu': 250, 'order': 7, 'type': 'parka', 'name': 'Extreme Cold Parka', 'weight': 1.5, 'cost': 300},
]

if st.button("Calculate Protection", key="calculate_button"):
    calculator = ArcticIREQCalculator()
    optimizer = ArcticLayerOptimizer(LAYERS_DB)
    
    # Calculate base IREQ (already scaled by 100)
    base_ireq = calculator.calculate_ireq(
        air_temp=air_temp,
        wind_speed=wind_speed,
        humidity=humidity,
        personal_data={
            'skin_temp': person_data['Skin_Temperature_C'],
            'weight_kg': person_data['Weight_kg'],
            'height_cm': person_data['Height_cm'],
            'vo2_max': person_data['VO2_Max_mL_kg_min'],
            'body_fat_percent': person_data['Body_Fat_Percent'],
            'brown_fat_level': 2  # Default to medium brown fat level
        }
    )
    
    if base_ireq == 9999:
        st.error("🚨 Extreme conditions detected! Recommending all available layers.")
        recommended = LAYERS_DB  # This fallback shouldn't happen often.
    else:
        # Apply wind chill adjustment more effectively
        adjusted_ireq = base_ireq * (1 + 0.1 * wind_speed)  # Adjust more dynamically
        final_ireq = min(adjusted_ireq, 400)  # Cap max IREQ for safety
        
        # Get recommended layers based on adjusted IREQ
        recommended = optimizer.recommend_layers(final_ireq, wind_speed, humidity, activity_level, air_temp)
        
        if not recommended:
            st.error("🚨 Insufficient layers available for protection!")
            recommended = LAYERS_DB  # Fallback to all layers

        # Display results
        st.subheader("Analysis Results")
        col1, col2 = st.columns(2)
        col1.metric("Base IREQ", f"{base_ireq/100:.1f} clo")
        col2.metric("Adjusted IREQ", f"{final_ireq/100:.1f} clo", delta="+25% safety")
        
        total_clu = sum(l['clu'] for l in recommended)
        coverage = min(total_clu / final_ireq, 1.0)
        
        st.progress(coverage, text=f"Protection Coverage: {coverage*100:.1f}%")
        
        st.success("Optimal Layer Configuration:")
        for layer in recommended:
            st.markdown(f"""
            <div style="padding:15px; margin:10px; background:#0b2b40; border-radius:8px; color:white">
                <b>Layer {layer['order']}:</b> {layer['name']}<br>
                <small>CLU: {layer['clu']/100:.1f} | Type: {layer['type'].title()}</small>
            </div>
            """, unsafe_allow_html=True)

        # Interactive Visualization
        layer_names = [l['name'] for l in recommended]
        layer_clu = [l['clu']/100 for l in recommended]
        fig = px.bar(x=layer_names, y=layer_clu, labels={'x': 'Layer', 'y': 'CLU Value'}, title="Layer Contribution to Insulation")
        st.plotly_chart(fig)