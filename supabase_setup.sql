-- GlobeTrotter Database Schema for Supabase
-- Run this SQL in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- USERS TABLE
-- =====================================================
-- Note: Supabase Auth handles the core authentication
-- This table extends the auth.users table with profile data
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    language_preference TEXT DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users can only view and update their own profile
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON public.users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- =====================================================
-- TRIPS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    photo_url TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    share_token TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_dates CHECK (end_date >= start_date)
);

-- Enable Row Level Security
ALTER TABLE public.trips ENABLE ROW LEVEL SECURITY;

-- Users can view their own trips
CREATE POLICY "Users can view own trips"
    ON public.trips FOR SELECT
    USING (auth.uid() = user_id);

-- Anyone can view public trips via share token
CREATE POLICY "Anyone can view public trips"
    ON public.trips FOR SELECT
    USING (is_public = TRUE);

-- Users can create their own trips
CREATE POLICY "Users can create own trips"
    ON public.trips FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own trips
CREATE POLICY "Users can update own trips"
    ON public.trips FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own trips
CREATE POLICY "Users can delete own trips"
    ON public.trips FOR DELETE
    USING (auth.uid() = user_id);

-- Create index for faster queries
CREATE INDEX idx_trips_user_id ON public.trips(user_id);
CREATE INDEX idx_trips_share_token ON public.trips(share_token);

-- =====================================================
-- DESTINATIONS/CITIES CATALOG TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.destinations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    region TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    cost_index INTEGER DEFAULT 50, -- 0-100 scale (low to high)
    popularity_score INTEGER DEFAULT 0,
    description TEXT,
    photo_url TEXT,
    average_temperature DECIMAL(4, 1), -- in Celsius
    best_time_to_visit TEXT,
    timezone TEXT,
    currency_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Public read access for destinations catalog
ALTER TABLE public.destinations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view destinations"
    ON public.destinations FOR SELECT
    TO public
    USING (true);

CREATE INDEX idx_destinations_country ON public.destinations(country);
CREATE INDEX idx_destinations_name ON public.destinations(name);

-- =====================================================
-- ACTIVITY CATALOG TABLE (Pre-populated activities)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.activity_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    destination_id UUID REFERENCES public.destinations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- 'sightseeing', 'food', 'adventure', 'culture', 'nightlife', 'shopping'
    subcategory TEXT,
    average_cost DECIMAL(10, 2),
    currency TEXT DEFAULT 'USD',
    duration_minutes INTEGER,
    photo_url TEXT,
    rating DECIMAL(2, 1), -- 0.0 - 5.0
    review_count INTEGER DEFAULT 0,
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    foursquare_id TEXT,
    popularity_score INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Public read access for activity catalog
ALTER TABLE public.activity_catalog ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view activity catalog"
    ON public.activity_catalog FOR SELECT
    TO public
    USING (true);

CREATE INDEX idx_activity_catalog_destination ON public.activity_catalog(destination_id);
CREATE INDEX idx_activity_catalog_category ON public.activity_catalog(category);

-- =====================================================
-- SAVED DESTINATIONS (User favorites)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.saved_destinations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    destination_id UUID NOT NULL REFERENCES public.destinations(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, destination_id)
);

ALTER TABLE public.saved_destinations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own saved destinations"
    ON public.saved_destinations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own saved destinations"
    ON public.saved_destinations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own saved destinations"
    ON public.saved_destinations FOR DELETE
    USING (auth.uid() = user_id);

CREATE INDEX idx_saved_destinations_user ON public.saved_destinations(user_id);

-- =====================================================
-- STOPS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.stops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
    destination_id UUID REFERENCES public.destinations(id), -- Link to destinations catalog
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    arrival_date DATE,
    departure_date DATE,
    "order" INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.stops ENABLE ROW LEVEL SECURITY;

-- Users can view stops for their own trips
CREATE POLICY "Users can view own trip stops"
    ON public.stops FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = stops.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Anyone can view stops for public trips
CREATE POLICY "Anyone can view public trip stops"
    ON public.stops FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = stops.trip_id
            AND trips.is_public = TRUE
        )
    );

-- Users can manage stops for their own trips
CREATE POLICY "Users can insert own trip stops"
    ON public.stops FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = stops.trip_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own trip stops"
    ON public.stops FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = stops.trip_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own trip stops"
    ON public.stops FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = stops.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- Create index for faster queries
CREATE INDEX idx_stops_trip_id ON public.stops(trip_id);

-- =====================================================
-- ACTIVITIES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stop_id UUID NOT NULL REFERENCES public.stops(id) ON DELETE CASCADE,
    catalog_activity_id UUID REFERENCES public.activity_catalog(id), -- Link to catalog if selected from it
    name TEXT NOT NULL,
    description TEXT,
    activity_type TEXT NOT NULL,
    scheduled_date DATE,
    scheduled_time TIME,
    duration_minutes INTEGER,
    cost DECIMAL(10, 2),
    currency TEXT DEFAULT 'USD',
    location TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    foursquare_id TEXT,
    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.activities ENABLE ROW LEVEL SECURITY;

-- Users can view activities for their own trips
CREATE POLICY "Users can view own trip activities"
    ON public.activities FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = activities.stop_id
            AND trips.user_id = auth.uid()
        )
    );

-- Anyone can view activities for public trips
CREATE POLICY "Anyone can view public trip activities"
    ON public.activities FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = activities.stop_id
            AND trips.is_public = TRUE
        )
    );

-- Users can manage activities for their own trips
CREATE POLICY "Users can insert own trip activities"
    ON public.activities FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = activities.stop_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own trip activities"
    ON public.activities FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = activities.stop_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own trip activities"
    ON public.activities FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = activities.stop_id
            AND trips.user_id = auth.uid()
        )
    );

-- Create index for faster queries
CREATE INDEX idx_activities_stop_id ON public.activities(stop_id);

-- =====================================================
-- ACCOMMODATIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.accommodations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stop_id UUID NOT NULL REFERENCES public.stops(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT, -- 'hotel', 'hostel', 'airbnb', 'resort', etc.
    address TEXT,
    check_in_date DATE,
    check_out_date DATE,
    cost_per_night DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    currency TEXT DEFAULT 'USD',
    rating DECIMAL(2, 1),
    photo_url TEXT,
    booking_url TEXT,
    confirmation_number TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.accommodations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view accommodations for own trips"
    ON public.accommodations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = accommodations.stop_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE POLICY "Anyone can view accommodations for public trips"
    ON public.accommodations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = accommodations.stop_id
            AND trips.is_public = TRUE
        )
    );

CREATE POLICY "Users can manage accommodations for own trips"
    ON public.accommodations FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = accommodations.stop_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE INDEX idx_accommodations_stop_id ON public.accommodations(stop_id);

-- =====================================================
-- TRANSPORTATION TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.transportation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
    from_stop_id UUID REFERENCES public.stops(id) ON DELETE SET NULL,
    to_stop_id UUID REFERENCES public.stops(id) ON DELETE SET NULL,
    type TEXT NOT NULL, -- 'flight', 'train', 'bus', 'car', 'ferry', etc.
    provider TEXT, -- airline, bus company, etc.
    departure_location TEXT,
    arrival_location TEXT,
    departure_time TIMESTAMP WITH TIME ZONE,
    arrival_time TIMESTAMP WITH TIME ZONE,
    cost DECIMAL(10, 2),
    currency TEXT DEFAULT 'USD',
    booking_reference TEXT,
    seat_number TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.transportation ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view transportation for own trips"
    ON public.transportation FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = transportation.trip_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE POLICY "Anyone can view transportation for public trips"
    ON public.transportation FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = transportation.trip_id
            AND trips.is_public = TRUE
        )
    );

CREATE POLICY "Users can manage transportation for own trips"
    ON public.transportation FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = transportation.trip_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE INDEX idx_transportation_trip_id ON public.transportation(trip_id);

-- =====================================================
-- MEALS/DINING TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.meals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stop_id UUID NOT NULL REFERENCES public.stops(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    meal_type TEXT, -- 'breakfast', 'lunch', 'dinner', 'snack'
    restaurant_name TEXT,
    cuisine_type TEXT,
    scheduled_date DATE,
    scheduled_time TIME,
    cost DECIMAL(10, 2),
    currency TEXT DEFAULT 'USD',
    location TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    rating DECIMAL(2, 1),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.meals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view meals for own trips"
    ON public.meals FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = meals.stop_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE POLICY "Anyone can view meals for public trips"
    ON public.meals FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = meals.stop_id
            AND trips.is_public = TRUE
        )
    );

CREATE POLICY "Users can manage meals for own trips"
    ON public.meals FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.stops
            JOIN public.trips ON trips.id = stops.trip_id
            WHERE stops.id = meals.stop_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE INDEX idx_meals_stop_id ON public.meals(stop_id);

-- =====================================================
-- TRIP BUDGET SUMMARY (Materialized view or table)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.trip_budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL UNIQUE REFERENCES public.trips(id) ON DELETE CASCADE,
    total_accommodation_cost DECIMAL(10, 2) DEFAULT 0,
    total_transportation_cost DECIMAL(10, 2) DEFAULT 0,
    total_activities_cost DECIMAL(10, 2) DEFAULT 0,
    total_meals_cost DECIMAL(10, 2) DEFAULT 0,
    total_other_cost DECIMAL(10, 2) DEFAULT 0,
    total_cost DECIMAL(10, 2) DEFAULT 0,
    currency TEXT DEFAULT 'USD',
    budget_limit DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.trip_budgets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view budget for own trips"
    ON public.trip_budgets FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = trip_budgets.trip_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE POLICY "Anyone can view budget for public trips"
    ON public.trip_budgets FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = trip_budgets.trip_id
            AND trips.is_public = TRUE
        )
    );

CREATE POLICY "Users can manage budget for own trips"
    ON public.trip_budgets FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = trip_budgets.trip_id
            AND trips.user_id = auth.uid()
        )
    );

CREATE INDEX idx_trip_budgets_trip_id ON public.trip_budgets(trip_id);

-- =====================================================
-- ANALYTICS/METRICS TABLE (for Admin Dashboard)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.platform_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_users INTEGER DEFAULT 0,
    new_users_today INTEGER DEFAULT 0,
    total_trips INTEGER DEFAULT 0,
    new_trips_today INTEGER DEFAULT 0,
    total_public_trips INTEGER DEFAULT 0,
    total_activities INTEGER DEFAULT 0,
    popular_destinations JSONB, -- [{destination_id, count}, ...]
    popular_activities JSONB, -- [{activity_type, count}, ...]
    average_trip_duration DECIMAL(10, 2),
    average_stops_per_trip DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(metric_date)
);

-- Only admins can access metrics (you'll need to add admin role logic)
ALTER TABLE public.platform_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Only service role can access metrics"
    ON public.platform_metrics FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trips_updated_at
    BEFORE UPDATE ON public.trips
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stops_updated_at
    BEFORE UPDATE ON public.stops
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_activities_updated_at
    BEFORE UPDATE ON public.activities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_destinations_updated_at
    BEFORE UPDATE ON public.destinations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_activity_catalog_updated_at
    BEFORE UPDATE ON public.activity_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accommodations_updated_at
    BEFORE UPDATE ON public.accommodations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transportation_updated_at
    BEFORE UPDATE ON public.transportation
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meals_updated_at
    BEFORE UPDATE ON public.meals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trip_budgets_updated_at
    BEFORE UPDATE ON public.trip_budgets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, created_at, updated_at)
    VALUES (NEW.id, NEW.email, NOW(), NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to automatically create profile on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Function to calculate trip budget totals
CREATE OR REPLACE FUNCTION public.calculate_trip_budget(p_trip_id UUID)
RETURNS void AS $$
DECLARE
    v_accommodation_total DECIMAL(10, 2);
    v_transportation_total DECIMAL(10, 2);
    v_activities_total DECIMAL(10, 2);
    v_meals_total DECIMAL(10, 2);
    v_grand_total DECIMAL(10, 2);
BEGIN
    -- Calculate accommodation costs
    SELECT COALESCE(SUM(total_cost), 0) INTO v_accommodation_total
    FROM public.accommodations
    WHERE stop_id IN (
        SELECT id FROM public.stops WHERE trip_id = p_trip_id
    );
    
    -- Calculate transportation costs
    SELECT COALESCE(SUM(cost), 0) INTO v_transportation_total
    FROM public.transportation
    WHERE trip_id = p_trip_id;
    
    -- Calculate activities costs
    SELECT COALESCE(SUM(cost), 0) INTO v_activities_total
    FROM public.activities
    WHERE stop_id IN (
        SELECT id FROM public.stops WHERE trip_id = p_trip_id
    );
    
    -- Calculate meals costs
    SELECT COALESCE(SUM(cost), 0) INTO v_meals_total
    FROM public.meals
    WHERE stop_id IN (
        SELECT id FROM public.stops WHERE trip_id = p_trip_id
    );
    
    v_grand_total := v_accommodation_total + v_transportation_total + 
                     v_activities_total + v_meals_total;
    
    -- Upsert budget record
    INSERT INTO public.trip_budgets (
        trip_id, 
        total_accommodation_cost, 
        total_transportation_cost,
        total_activities_cost,
        total_meals_cost,
        total_cost,
        updated_at
    )
    VALUES (
        p_trip_id,
        v_accommodation_total,
        v_transportation_total,
        v_activities_total,
        v_meals_total,
        v_grand_total,
        NOW()
    )
    ON CONFLICT (trip_id) DO UPDATE SET
        total_accommodation_cost = v_accommodation_total,
        total_transportation_cost = v_transportation_total,
        total_activities_cost = v_activities_total,
        total_meals_cost = v_meals_total,
        total_cost = v_grand_total,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- GRANT PERMISSIONS
-- =====================================================

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION public.calculate_trip_budget(UUID) TO authenticated;
