import streamlit as st
import pickle
import pandas as pd
import plotly.express as px

# Constants
MATERIAL_RATES = {
    'Residential': {'cement': 0.5, 'blocks': 10, 'steel': 0.025, 'sand': 0.05, 'granite': 0.03},
    'Commercial': {'cement': 0.7, 'blocks': 15, 'steel': 0.04, 'sand': 0.07, 'granite': 0.05},
    'Industrial': {'cement': 1.0, 'blocks': 20, 'steel': 0.06, 'sand': 0.10, 'granite': 0.08}
}

SHAPE_COMPLEXITY = {
    'Rectangular': 1.0,
    'Square': 1.05,
    'L-Shaped': 1.15,
    'U-Shaped': 1.2,
    'Circular': 1.25
}

PLANT_RATES = {
    'Residential': 0.08,
    'Commercial': 0.12,
    'Industrial': 0.18
}

# Labor productivity rates (hours/m²)
LABOR_PRODUCTIVITY_RATES = {
    'Residential': {
        'foundation': 1.2,
        'structural': 2.0,
        'finishing': 1.5
    },
    'Commercial': {
        'foundation': 1.5,
        'structural': 2.5,
        'finishing': 2.0
    },
    'Industrial': {
        'foundation': 2.0,
        'structural': 3.0,
        'finishing': 2.5
    }
}

# Labor efficiency factors
EFFICIENCY_FACTORS = {
    'crew_size': {
        'Small': 0.9,    # Less than 15 workers
        'Medium': 1.0,   # 15-30 workers
        'Large': 1.1     # More than 30 workers
    },
    'weather': {
        'Good': 1.0,
        'Average': 0.9,
        'Poor': 0.8
    }
}

RISK_FACTORS = {'prelim': 0.05, 'cont': 0.075, 'design': 0.02}
CIRCULATION_SPACE = 0.20
STANDARD_WORK_HOURS = 8
OVERHEAD_PROFIT = 0.15

# Load artifacts
model = pickle.load(open('cost_only_model.pkl', 'rb'))
preprocessor = pickle.load(open('preprocessor_cost.pkl', 'rb'))
metrics = pickle.load(open('metrics_cost.pkl', 'rb'))

# Page configuration
st.set_page_config(
    page_title="Estimate.ai",
    page_icon="🏗️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .header { color: #2E86C1; font-weight: 700; }
    .metric-box { padding: 20px; border-radius: 10px; background: #F4F6F6; margin: 10px 0; }
    .highlight { color: #2E86C1; font-weight: 700; }
    .sub-metric { padding: 10px; background: #EBF5FB; border-radius: 5px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("<h1 class='header'>🏗️ AI Construction Estimator</h1>", unsafe_allow_html=True)
st.markdown("### Construction Cost & Productivity Prediction App")

def calculate_gfa(length, breadth, storeys, shape):
    base_area = length * breadth * storeys
    shape_multiplier = SHAPE_COMPLEXITY[shape]
    return base_area * shape_multiplier

def calculate_site_difficulty(soil, access):
    soil_map = {'Rocky': 1.5, 'Sandy': 1.2, 'Clay': 1.0}
    access_map = {'Poor': 1.4, 'Average': 1.1, 'Good': 1.0}
    return soil_map[soil] * access_map[access]

def calculate_labor_hours(gfa, building_type, crew_size, weather_condition):
    base_hours = sum([
        LABOR_PRODUCTIVITY_RATES[building_type]['foundation'],
        LABOR_PRODUCTIVITY_RATES[building_type]['structural'],
        LABOR_PRODUCTIVITY_RATES[building_type]['finishing']
    ]) * gfa
    
    crew_efficiency = EFFICIENCY_FACTORS['crew_size']['Medium' if 15 <= crew_size <= 30 
                                                     else 'Large' if crew_size > 30 
                                                     else 'Small']
    weather_efficiency = EFFICIENCY_FACTORS['weather'][weather_condition]
    
    return base_hours / (crew_efficiency * weather_efficiency)

# Building dimensions section
st.markdown("### 📐 Building Dimensions")
col_dim1, col_dim2 = st.columns(2)

with col_dim1:
    length = st.number_input("Length (meters)", 10, 100, 20, key="length_input")
    breadth = st.number_input("Breadth (meters)", 10, 100, 15, key="breadth_input")
    
with col_dim2:
    storeys = st.slider("Number of Floors", 1, 10, 2, key="storeys_input")
    shape = st.selectbox("Building Shape", list(SHAPE_COMPLEXITY.keys()), key="shape_input")

# Calculate and display GFA instantly
current_gfa = calculate_gfa(length, breadth, storeys, shape)
st.markdown(f"""
<div class='metric-box'>
    <h3>Gross Floor Area (GFA)</h3>
    <h2 class='highlight'>{current_gfa:.2f} m²</h2>
</div>
""", unsafe_allow_html=True)

# Main form for other inputs
with st.form("project_input"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌍 Site Conditions")
        building_type = st.selectbox("Building Type", list(MATERIAL_RATES.keys()))
        location = st.selectbox("Location Type", ["Urban", "Suburban", "Rural"])
        soil = st.selectbox("Soil Type", ["Rocky", "Sandy", "Clay"])
        access = st.selectbox("Site Accessibility", ["Good", "Average", "Poor"])
        weather = st.selectbox("Weather Conditions", ["Good", "Average", "Poor"])
    
    st.markdown("### 💰 Pricing Inputs")
    col3, col4 = st.columns(2)
    with col3:
        cement = st.number_input("Cement Price (₦/bag)", 9500, 10500, 9800)
        blocks = st.number_input("Block Price (₦/unit)", 500, 750, 600)
        steel = st.number_input("Steel Price (₦/ton)", 700000, 1250000, 850000)
    with col4:
        sand = st.number_input("Sand Price (₦/ton)", 30000, 50000, 35000)
        granite = st.number_input("Granite Price (₦/ton)", 19000, 40000, 19500)
        labor_rate = st.number_input("Labor Rate (₦/hour)", 500, 3000, 1000)
    
    st.markdown("### 👷 Workforce & Permits")
    workers = st.number_input("Number of Workers", 10, 100, 20)
    permit = st.number_input("Permit Duration (months)", 1, 24, 3)
    
    submit_button = st.form_submit_button("🚀 Generate Estimate")
    
    if submit_button:
        # Calculate labor hours and productivity
        labor_hours = calculate_labor_hours(current_gfa, building_type, workers, weather)
        labor_productivity = current_gfa / (labor_hours * workers)
        project_duration = labor_hours / (workers * STANDARD_WORK_HOURS)
        
        # Calculate labor cost including overhead
        labor_cost = labor_hours * labor_rate * (1 + OVERHEAD_PROFIT)
        
        # Feature calculations
        site_difficulty = calculate_site_difficulty(soil, access)
        shape_complexity = SHAPE_COMPLEXITY[shape]
        vertical_complexity = storeys * 0.25
        
        # Create input data with ALL required columns
        input_data = pd.DataFrame([{
            'Length': length,
            'Breadth': breadth,
            'Storeys': storeys,
            'Shape': shape,
            'Type': building_type,
            'Location': location,
            'Soil': soil,
            'Access': access,
            'Weather': weather,
            'Cement_Price': cement,
            'Block_Price': blocks,
            'Steel_Price': steel,
            'Sand_Price': sand,
            'Granite_Price': granite,
            'Labor_Rate': labor_rate,  # User-provided hourly rate
            'Labor_Cost': labor_cost,  # Calculated total labor cost
            'Workers': workers,
            'Permit_Months': permit,
            'Site_Difficulty': site_difficulty,
            'Shape_Complexity': shape_complexity,
            'Vertical_Complexity': vertical_complexity
        }])
        
        # Make prediction
        processed = preprocessor.transform(input_data)
        total_cost = model.predict(processed)[0]
        
        # Display results
        st.success("## 📊 Estimation Results")
        
        # Cost Results
        st.markdown(f"""
        <div class='metric-box'>
            <h3>Total Construction Cost</h3>
            <h2 class='highlight'>₦{total_cost:,.0f}</h2>
            <p>Professional estimate accounting for material, labor, plant, and risk factors</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Productivity Results
        #st.markdown(f"""
        #<div class='metric-box'>
         #   <h3>Labor Productivity Metrics</h3>
          #  <div class='sub-metric'>
           #     <p>Total Labor Hours: <span class='highlight'>{labor_hours:,.0f} hours</span></p>
            #    <p>Productivity Rate: <span class='highlight'>{labor_productivity:.2f} m²/worker-hour</span></p>
             #   <p>Estimated Duration: <span class='highlight'>{project_duration:.1f} days</span></p>
              #  <p>Labor Cost (with overhead): <span class='highlight'>₦{labor_cost:,.0f}</span></p>
            #</div>
        #</div>
        #""", unsafe_allow_html=True)
        
        # Cost breakdown
        material_cost = sum([
            cement * MATERIAL_RATES[building_type]['cement'] * current_gfa,
            blocks * MATERIAL_RATES[building_type]['blocks'] * current_gfa,
            steel * MATERIAL_RATES[building_type]['steel'] * current_gfa,
            sand * MATERIAL_RATES[building_type]['sand'] * current_gfa,
            granite * MATERIAL_RATES[building_type]['granite'] * current_gfa
        ])
        
        plant_cost = (material_cost + labor_cost) * PLANT_RATES[building_type]
        base_cost = material_cost + labor_cost + plant_cost
        
        # Risk calculations
        risk_components = {
            'Contingencies': base_cost * RISK_FACTORS['cont'],
            'Preliminaries': base_cost * RISK_FACTORS['prelim'],
            'Design Risk': base_cost * RISK_FACTORS['design']
        }
        
        # Visualizations
        col_viz1, col_viz2 = st.columns(2)
        with col_viz1:
            fig_main = px.pie(
                names=['Materials', 'Labor', 'Plant', 'Risks'],
                values=[material_cost, labor_cost, plant_cost, sum(risk_components.values())],
                title="Cost Distribution",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_main, use_container_width=True)
            
        with col_viz2:
            fig_risk = px.pie(
                names=list(risk_components.keys()),
                values=list(risk_components.values()),
                title="Risk Factors Breakdown",
                color_discrete_sequence=px.colors.qualitative.Pastel1
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Productivity visualization
        fig_productivity = px.bar(
            x=['Foundation', 'Structural', 'Finishing'],
            y=[
                LABOR_PRODUCTIVITY_RATES[building_type]['foundation'] * current_gfa,
                LABOR_PRODUCTIVITY_RATES[building_type]['structural'] * current_gfa,
                LABOR_PRODUCTIVITY_RATES[building_type]['finishing'] * current_gfa
            ],
            title="Labor Hours by Construction Phase",
            labels={'x': 'Phase', 'y': 'Hours Required'}
        )
        st.plotly_chart(fig_productivity, use_container_width=True)
       
        # Model metrics
        st.markdown("### 🧠 Model Performance")
        col_met1, col_met2 = st.columns(2)
        with col_met1:
            st.markdown(f"""
            <div class='metric-box'>
                <h4>Training Performance</h4>
                <p>R²: <span class='highlight'>{metrics['train_r2']:.3f}</span></p>
            </div>
            """, unsafe_allow_html=True)
        with col_met2:
            st.markdown(f"""
            <div class='metric-box'>
                <h4>Validation Performance</h4>
                <p>R²: <span class='highlight'>{metrics['test_r2']:.3f}</span></p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    pass