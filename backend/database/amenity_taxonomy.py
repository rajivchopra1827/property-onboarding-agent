"""
Canonical amenity taxonomy for normalization.

This file defines the standard, canonical names for amenities that all
raw amenity names should be mapped to. The AI normalization service
will use this taxonomy to map variations (e.g., "gym", "24-Hour Fitness Center")
to canonical names (e.g., "Fitness Center").
"""

CANONICAL_AMENITIES = {
    'building': [
        # Fitness & Recreation
        'Fitness Center',
        'Swimming Pool',
        'Hot Tub',
        'Sauna',
        'Steam Room',
        'Basketball Court',
        'Tennis Court',
        'Volleyball Court',
        'Racquetball Court',
        'Yoga Studio',
        'Cycling Studio',
        'Running Track',
        
        # Business & Work
        'Business Center',
        'Conference Room',
        'Coworking Space',
        'Wi-Fi',
        'High-Speed Internet',
        
        # Parking & Transportation
        'Parking',
        'Garage Parking',
        'Covered Parking',
        'Reserved Parking',
        'EV Charging Stations',
        'Bike Storage',
        'Bike Racks',
        
        # Pet Amenities
        'Pet-Friendly',
        'Dog Park',
        'Pet Spa',
        'Pet Washing Station',
        
        # Community Spaces
        'Clubhouse',
        'Community Room',
        'Game Room',
        'Media Room',
        'Theater Room',
        'Party Room',
        'Rooftop Deck',
        'Outdoor Space',
        'Courtyard',
        'Patio',
        'BBQ Area',
        'Fire Pit',
        'Outdoor Kitchen',
        
        # Services
        'Concierge',
        'Package Receiving',
        'Package Lockers',
        'On-Site Management',
        '24-Hour Maintenance',
        'Valet Trash Service',
        'Dry Cleaning Service',
        
        # Laundry
        'Laundry Facilities',
        'Laundry Room',
        'On-Site Laundry',
        
        # Security
        'Controlled Access',
        'Gated Community',
        'Security System',
        'Video Surveillance',
        'Keyless Entry',
        
        # Other
        'Elevator',
        'Storage Units',
        'Climate Control',
        'Green Building',
        'LEED Certified',
    ],
    'apartment': [
        # Kitchen Appliances
        'Dishwasher',
        'Disposal',
        'Microwave',
        'Refrigerator',
        'Stainless Steel Appliances',
        'Gas Range',
        'Electric Range',
        'Oven',
        'Island',
        'Pantry',
        'Wine Cooler',
        
        # Laundry
        'Washer/Dryer',
        'Washer/Dryer Hookups',
        'In-Unit Laundry',
        
        # Climate Control
        'Air Conditioning',
        'Central Air',
        'Heating',
        'Ceiling Fans',
        'Programmable Thermostat',
        
        # Flooring
        'Hardwood Floors',
        'Carpet',
        'Tile Floors',
        'Vinyl Plank Flooring',
        'Luxury Vinyl',
        
        # Storage
        'Walk-in Closet',
        'Extra Storage',
        'Built-in Storage',
        
        # Outdoor Spaces
        'Balcony',
        'Patio',
        'Private Balcony',
        'Private Patio',
        'Private Yard',
        
        # Windows & Light
        'Large Windows',
        'Natural Light',
        'Bay Windows',
        'Window Coverings',
        
        # Technology
        'High-Speed Internet',
        'Cable Ready',
        'Smart Home Features',
        'Smart Thermostat',
        'Smart Locks',
        
        # Bathroom
        'Garden Tub',
        'Soaking Tub',
        'Double Vanity',
        'Separate Shower',
        'Walk-in Shower',
        
        # Other Features
        'Fireplace',
        'Vaulted Ceilings',
        'Crown Molding',
        'Granite Countertops',
        'Quartz Countertops',
        'Stainless Steel Sink',
        'Updated Kitchen',
        'Updated Bathroom',
        'Renovated',
        'New Construction',
    ]
}

def get_canonical_amenities(category: str) -> list:
    """Get canonical amenities for a given category."""
    return CANONICAL_AMENITIES.get(category, [])

def is_canonical(name: str, category: str) -> bool:
    """Check if a name is already a canonical amenity name."""
    return name in CANONICAL_AMENITIES.get(category, [])
