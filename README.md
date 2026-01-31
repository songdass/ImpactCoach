# Daily Action-to-Impact Coach 🌱

A minimal MVP for tracking daily environmental impact and receiving personalized recommendations to reduce your carbon footprint.

## Features

- **📝 Action Logging**: Record daily actions across three categories:
  - 🚗 **Mobility**: Transportation (taxi, bus, subway, car, bicycle, etc.)
  - 🛒 **Purchase**: Consumption (food, fashion, electronics, etc.)
  - 🏠 **Home Energy**: Energy use (electricity, gas, heating)

- **📊 Impact Calculation**: Automatic calculation of:
  - CO₂e emissions (kg)
  - Water footprint (L)

- **🎯 Smart Recommendations**: Personalized suggestions based on your daily actions with estimated savings

- **📈 Weekly Trends**: Track your progress over time with charts and insights

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Streamlit UI   │────▶│  FastAPI Backend │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Impact   │ │ Recommend│ │ SQLite   │
              │ Engine   │ │ Engine   │ │ Database │
              └──────────┘ └──────────┘ └──────────┘
```

## Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Backend API

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 4. Start the Streamlit Frontend

Open a new terminal:

```bash
streamlit run app_streamlit.py
```

The app will open at http://localhost:8501

## Project Structure

```
ImpactCoach/
├── app_streamlit.py           # Streamlit frontend
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── db.py                  # SQLite database operations
│   ├── models.py              # Pydantic schemas
│   ├── services/
│   │   ├── impact_engine.py   # Impact calculation engine
│   │   └── recommendation.py  # Recommendation engine
│   └── data/
│       ├── emission_factors.json   # Mobility & energy factors
│       └── product_factors.json    # Purchase factors
├── tests/
│   └── test_impact_engine.py  # Unit tests
├── requirements.txt
└── README.md
```

## API Endpoints

### Actions
- `POST /actions` - Log a new action
- `GET /actions` - Get actions for a date
- `DELETE /actions/{id}` - Delete an action

### Impact
- `GET /impact/daily` - Get daily impact summary
- `GET /impact/weekly` - Get weekly trend data

### Coaching
- `GET /coach/daily` - Get daily coaching response with recommendations
- `GET /coach/insight` - Get weekly insight message

### Reference
- `GET /factors` - List all available factors
- `GET /factors/{category}` - List factors by category

## Sample Actions

### Mobility
```json
{
  "category": "mobility",
  "item": "taxi_ice",
  "amount": 5
}
```

### Purchase
```json
{
  "category": "purchase",
  "item": "beef_meal",
  "amount": 1
}
```

### Home Energy
```json
{
  "category": "home_energy",
  "item": "electricity_kwh",
  "amount": 10,
  "time_of_day": "peak"
}
```

## Available Factors

### Mobility (distance in km)
| Item | CO₂e (kg/km) | Description |
|------|--------------|-------------|
| taxi_ice | 0.21 | Gasoline taxi |
| taxi_ev | 0.05 | Electric taxi |
| bus | 0.089 | City bus |
| subway | 0.035 | Metro/subway |
| bicycle | 0.0 | Bicycle |
| walking | 0.0 | Walking |

### Food (per meal/unit)
| Item | CO₂e (kg) | Water (L) |
|------|-----------|-----------|
| beef_meal | 6.5 | 1850 |
| chicken_meal | 1.1 | 430 |
| vegetarian_meal | 0.4 | 180 |
| coffee | 0.21 | 140 |

### Fashion (per item)
| Item | CO₂e (kg) | Water (L) |
|------|-----------|-----------|
| tshirt_fastfashion | 5.5 | 2700 |
| tshirt_secondhand | 0.5 | 50 |
| jeans_fastfashion | 33.0 | 7500 |

### Home Energy
| Item | CO₂e (kg/unit) | Unit |
|------|----------------|------|
| electricity_kwh | 0.459 | kWh |
| natural_gas_m3 | 2.23 | m³ |

## Running Tests

```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ -v --cov=backend
```

## Export Data

The Streamlit app supports CSV export for weekly data. Navigate to the Weekly Trend page and click "Download Weekly Data as CSV".

## Future Enhancements

- [ ] User authentication
- [ ] Multi-agent system (MAS) architecture
- [ ] Real-time grid carbon intensity data
- [ ] Location-based recommendations
- [ ] Social features (compare with friends)
- [ ] Mobile app

## Data Sources

The emission factors in this MVP are placeholder values based on:
- Korea Environment Corporation guidelines
- IPCC emission factor database
- Various Life Cycle Assessment (LCA) studies

For production use, these should be updated with verified, region-specific data.

## License

MIT License

---

Built with ❤️ for a sustainable future
