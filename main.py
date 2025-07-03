
import flask
from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import io
import base64
import os
from typing import Dict, List, Any

app = Flask(__name__)

class AirlineDataScraper:
    """Handles data collection from various sources"""
    
    def __init__(self):
        self.base_urls = {
            'aviation_stack': 'http://api.aviationstack.com/v1/flights',
            'opensky': 'https://opensky-network.org/api/states/all'
        }
    
    def get_sample_airline_data(self) -> List[Dict]:
        """Generate sample airline booking data for demonstration"""
        # Australian cities only
        cities = ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide', 'Canberra', 'Hobart', 'Darwin']
        airlines = ['Qantas', 'Virgin Australia', 'Rex Airlines', 'Tigerair']
        
        # Generate comprehensive routes between all Australian cities
        routes = []
        for i, origin in enumerate(cities):
            for destination in cities[i+1:]:
                routes.append((origin, destination))
                routes.append((destination, origin))  # Add reverse route
        
        data = []
        # Generate data ensuring each route has flights from multiple airlines
        for route in routes:
            for airline in airlines:
                for j in range(2):  # 2 flights per route per airline
                    base_price = 150 + (len(data) % 300)
                    demand_factor = 0.7 + (len(data) % 60) / 100
                    
                    data.append({
                        'route': f"{route[0]} -> {route[1]}",
                        'origin': route[0],
                        'destination': route[1],
                        'airline': airline,
                        'price': int(base_price * demand_factor),
                        'demand_score': round(demand_factor * 100, 1),
                        'bookings': 50 + (len(data) % 150),
                        'date': (datetime.now() - timedelta(days=len(data) % 30)).strftime('%Y-%m-%d')
                    })
        
        return data
    
    def get_flight_data_opensky(self) -> List[Dict]:
        """Fetch real flight data from OpenSky API"""
        try:
            response = requests.get(self.base_urls['opensky'], timeout=10)
            if response.status_code == 200:
                data = response.json()
                flights = []
                
                if 'states' in data and data['states']:
                    for state in data['states'][:50]:  # Limit to 50 flights
                        if state[1]:  # callsign exists
                            flights.append({
                                'callsign': state[1].strip() if state[1] else 'Unknown',
                                'origin_country': state[2] if state[2] else 'Unknown',
                                'longitude': state[5] if state[5] else 0,
                                'latitude': state[6] if state[6] else 0,
                                'altitude': state[7] if state[7] else 0,
                                'velocity': state[9] if state[9] else 0
                            })
                
                return flights
        except Exception as e:
            print(f"Error fetching OpenSky data: {e}")
        
        return []

class DataProcessor:
    """Processes and analyzes airline data"""
    
    def __init__(self):
        pass
    
    def analyze_demand_trends(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze demand trends from airline data"""
        df = pd.DataFrame(data)
        
        # Convert numpy types to native Python types for JSON serialization
        popular_routes = df.groupby('route')['bookings'].sum().sort_values(ascending=False).head(5)
        average_prices = df.groupby('route')['price'].mean().sort_values(ascending=False).head(5)
        airline_market_share = df.groupby('airline')['bookings'].sum()
        demand_by_origin = df.groupby('origin')['demand_score'].mean().sort_values(ascending=False)
        
        analysis = {
            'popular_routes': {str(k): int(v) for k, v in popular_routes.items()},
            'average_prices': {str(k): float(v) for k, v in average_prices.items()},
            'airline_market_share': {str(k): int(v) for k, v in airline_market_share.items()},
            'demand_by_origin': {str(k): float(v) for k, v in demand_by_origin.items()},
            'total_bookings': int(df['bookings'].sum()),
            'average_price': float(round(df['price'].mean(), 2)),
            'highest_demand_route': str(df.loc[df['demand_score'].idxmax()]['route'])
        }
        
        return analysis
    
    def generate_insights_with_ai(self, analysis: Dict) -> str:
        """Generate insights using a simple rule-based system (simulating AI analysis)"""
        insights = []
        
        popular_routes = list(analysis['popular_routes'].keys())
        if popular_routes:
            insights.append(f"The most popular route is {popular_routes[0]} with {analysis['popular_routes'][popular_routes[0]]} bookings.")
        
        if analysis['average_price'] > 200:
            insights.append("Average flight prices are relatively high, indicating strong demand or premium routes.")
        else:
            insights.append("Average flight prices are moderate, suggesting competitive pricing in the market.")
        
        airline_leader = max(analysis['airline_market_share'].items(), key=lambda x: x[1])
        insights.append(f"{airline_leader[0]} leads the market with {airline_leader[1]} total bookings.")
        
        insights.append(f"The route with highest demand score is: {analysis['highest_demand_route']}")
        
        return " ".join(insights)

def create_visualization(data: List[Dict]) -> str:
    """Create data visualizations and return as base64 encoded image"""
    df = pd.DataFrame(data)
    
    # Create a figure with multiple subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Popular routes
    route_bookings = df.groupby('route')['bookings'].sum().sort_values(ascending=False).head(8)
    ax1.bar(range(len(route_bookings)), route_bookings.values)
    ax1.set_title('Popular Routes by Bookings')
    ax1.set_xlabel('Routes')
    ax1.set_ylabel('Total Bookings')
    ax1.set_xticks(range(len(route_bookings)))
    ax1.set_xticklabels(route_bookings.index, rotation=45, ha='right')
    
    # Price distribution
    ax2.hist(df['price'], bins=20, alpha=0.7, color='skyblue')
    ax2.set_title('Price Distribution')
    ax2.set_xlabel('Price ($)')
    ax2.set_ylabel('Frequency')
    
    # Airline market share
    airline_bookings = df.groupby('airline')['bookings'].sum()
    ax3.pie(airline_bookings.values, labels=airline_bookings.index, autopct='%1.1f%%')
    ax3.set_title('Airline Market Share')
    
    # Demand trends by date
    daily_demand = df.groupby('date')['demand_score'].mean()
    ax4.plot(daily_demand.index, daily_demand.values, marker='o')
    ax4.set_title('Average Demand Score Over Time')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Average Demand Score')
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Convert plot to base64 string
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return img_base64

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """API endpoint to fetch and analyze airline data"""
    try:
        scraper = AirlineDataScraper()
        processor = DataProcessor()
        
        # Get sample data (in production, this would fetch real data)
        airline_data = scraper.get_sample_airline_data()
        
        # Get real flight data for additional context
        flight_data = scraper.get_flight_data_opensky()
        
        # Analyze the data
        analysis = processor.analyze_demand_trends(airline_data)
        
        # Generate AI insights
        insights = processor.generate_insights_with_ai(analysis)
        
        # Create visualizations
        chart_image = create_visualization(airline_data)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'insights': insights,
            'chart': chart_image,
            'live_flights': len(flight_data),
            'data_points': len(airline_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/filter')
def filter_data():
    """API endpoint to filter data based on user inputs"""
    try:
        origin = request.args.get('origin', '')
        destination = request.args.get('destination', '')
        airline = request.args.get('airline', '')
        
        scraper = AirlineDataScraper()
        processor = DataProcessor()
        
        # Get data
        data = scraper.get_sample_airline_data()
        
        # Apply filters
        if origin:
            data = [d for d in data if origin.lower() in d['origin'].lower()]
        if destination:
            data = [d for d in data if destination.lower() in d['destination'].lower()]
        if airline:
            data = [d for d in data if airline.lower() in d['airline'].lower()]
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data found matching the filters'
            })
        
        # Analyze filtered data
        analysis = processor.analyze_demand_trends(data)
        insights = processor.generate_insights_with_ai(analysis)
        chart_image = create_visualization(data)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'insights': insights,
            'chart': chart_image,
            'filtered_count': len(data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
