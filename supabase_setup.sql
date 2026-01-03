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
-- STOPS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.stops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
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
    name TEXT NOT NULL,
    description TEXT,
    activity_type TEXT NOT NULL,
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

-- =====================================================
-- GRANT PERMISSIONS
-- =====================================================

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
