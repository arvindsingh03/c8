# Arctic Protection System 2.0

## Overview
This project implements an advanced Arctic Protection System designed to provide full-body protection in extreme cold conditions. It is ISO 11079:2007 compliant and integrates real-life physiological and environmental factors to recommend optimal clothing configurations using the ECWCS Gen III layers. The system dynamically calculates the required insulation (IREQ) and selects layers based on various constraints and conditions.

## Features
1. **Advanced IREQ Calculation:**
   - Uses ISO 11079 standards to calculate insulation requirements.
   - Incorporates factors such as wind chill, humidity, body fat percentage, and activity level.
   - Dynamic adjustments for extreme cold conditions and high humidity.

2. **Layer Optimization:**
   - Recommends ECWCS Gen III layers to meet or exceed calculated insulation requirements.
   - Optimizes for minimal weight and cost while ensuring maximum protection.
   - Supports constraints like activity level and weather conditions.

3. **Interactive Visualization:**
   - Provides an intuitive interface using Streamlit.
   - Visualizes layer contribution to overall insulation with Plotly.

4. **Customizable User Profiles:**
   - Users can input their physical attributes and preferences.
   - The system adapts recommendations to personal physiological factors.

## Installation
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/<arvind singh>/c8.git
   cd c8.py
   ```

2. **Install Dependencies:**
   - Use `pip` to install required Python packages:
     ```bash
     pip install -r requirements.txt
     ```

3. **Prepare Data:**
   - Ensure the `crt.csv` file is placed in the project directory. This file contains user profiles.

4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```

## Usage
1. Open the application in your browser (Streamlit provides a local URL).
2. Select a user profile from the sidebar.
3. Adjust environmental parameters (temperature, wind speed, humidity, activity level).
4. Click **Calculate Protection** to get recommendations.
5. View:
   - Recommended layers and their details.
   - Interactive visualization of layer contributions.

## Configuration File: `crt.csv`
The `crt.csv` file should contain the following columns:
- `Person_ID`
- `Name`
- `Weight_kg`
- `Height_cm`
- `Body_Fat_Percent`
- `Skin_Temperature_C`
- `VO2_Max_mL_kg_min`

## Key Classes and Functions
### **ArcticIREQCalculator**
- **Purpose:** Calculates the insulation required (IREQ) based on ISO 11079.
- **Key Methods:**
  - `calculate_bsa(weight_kg, height_cm)`
  - `calculate_wind_chill(temp_c, wind_speed)`
  - `calculate_ireq(air_temp, wind_speed, humidity, personal_data)`

### **ArcticLayerOptimizer**
- **Purpose:** Selects optimal clothing layers based on the calculated IREQ.
- **Key Methods:**
  - `recommend_layers(target_clu, wind_speed, humidity, activity_level, air_temp)`

## Future Improvements
1. **Dynamic Real-Life Integration:**
   - Real-time weather API integration.
   - Integration with wearable sensors to dynamically monitor user conditions.

2. **Custom Layer Configurations:**
   - Allow users to upload their clothing database.

3. **Multi-User Support:**
   - Enable multi-user sessions and save configurations.

4. **Enhanced Visualization:**
   - Add more interactive charts to compare various configurations.

## Contributing
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Added new feature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Create a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.



---

Enjoy using Arctic Protection System 2.0! Stay warm and safe in extreme conditions.

