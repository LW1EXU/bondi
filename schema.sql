BEGIN;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE agencies (
 id text PRIMARY KEY, name text NOT NULL, url text,
 timezone text NOT NULL DEFAULT 'America/Argentina/Buenos_Aires'
);
CREATE TABLE data_versions (
 version text PRIMARY KEY CHECK (version ~ '^\d+\.\d+\.\d+$'),
 created_at timestamptz NOT NULL DEFAULT now(),
 status text NOT NULL CHECK (status IN ('candidate','published','rejected')),
 manifest jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE sources (
 id text PRIMARY KEY, url text NOT NULL, fetched_at timestamptz,
 sha256 text, license text, metadata jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE lines (
 id text PRIMARY KEY, name text NOT NULL,
 type text NOT NULL CHECK (type IN ('comunal','provincial','especial')),
 agency_id text REFERENCES agencies(id),
 verified boolean NOT NULL DEFAULT false,
 source_id text REFERENCES sources(id), version text REFERENCES data_versions(version)
);
CREATE TABLE branches (
 id text PRIMARY KEY, line_id text NOT NULL REFERENCES lines(id),
 name text NOT NULL, direction smallint NOT NULL CHECK (direction IN (0,1)),
 variant text NOT NULL DEFAULT 'regular', color text CHECK (color ~ '^[0-9A-Fa-f]{6}$'),
 shape geometry(LineString,4326), source_id text REFERENCES sources(id),
 UNIQUE(line_id,name,direction,variant)
);
CREATE INDEX branches_shape_idx ON branches USING gist(shape);
CREATE TABLE stops (
 id text PRIMARY KEY, name text NOT NULL, location geography(Point,4326) NOT NULL,
 street_side text, wheelchair_boarding smallint NOT NULL DEFAULT 0 CHECK (wheelchair_boarding BETWEEN 0 AND 2),
 source_id text REFERENCES sources(id)
);
CREATE INDEX stops_location_idx ON stops USING gist(location);
CREATE TABLE branch_stops (
 branch_id text REFERENCES branches(id) ON DELETE CASCADE,
 stop_id text NOT NULL REFERENCES stops(id), sequence integer CHECK (sequence >= 0),
 PRIMARY KEY(branch_id,sequence)
);
CREATE INDEX branch_stops_stop_idx ON branch_stops(stop_id);
CREATE TABLE services (
 id text PRIMARY KEY, start_date date NOT NULL, end_date date NOT NULL,
 weekdays boolean[] NOT NULL CHECK (array_length(weekdays,1)=7),
 CHECK(end_date >= start_date)
);
CREATE TABLE service_exceptions (
 service_id text REFERENCES services(id), date date NOT NULL,
 exception_type smallint NOT NULL CHECK(exception_type IN (1,2)), PRIMARY KEY(service_id,date)
);
CREATE TABLE trips (
 id text PRIMARY KEY, branch_id text NOT NULL REFERENCES branches(id),
 service_id text NOT NULL REFERENCES services(id), headsign text
);
CREATE INDEX trips_branch_idx ON trips(branch_id);
-- Seconds since service-day midnight support GTFS 25:30:00 and overnight runs.
CREATE TABLE stop_times (
 trip_id text REFERENCES trips(id) ON DELETE CASCADE, stop_id text NOT NULL REFERENCES stops(id),
 sequence integer CHECK(sequence >= 0), arrival_seconds integer NOT NULL CHECK(arrival_seconds >= 0),
 departure_seconds integer NOT NULL CHECK(departure_seconds >= arrival_seconds), PRIMARY KEY(trip_id,sequence)
);
CREATE TABLE frequencies (
 trip_id text REFERENCES trips(id), start_seconds integer CHECK(start_seconds >= 0),
 end_seconds integer NOT NULL, headway_seconds integer NOT NULL CHECK(headway_seconds > 0),
 exact_times boolean NOT NULL DEFAULT false, PRIMARY KEY(trip_id,start_seconds), CHECK(end_seconds > start_seconds)
);
CREATE TABLE alerts (
 id text PRIMARY KEY, line_id text REFERENCES lines(id), branch_id text REFERENCES branches(id),
 title text NOT NULL, description text NOT NULL, starts_at timestamptz NOT NULL,
 ends_at timestamptz, source_id text REFERENCES sources(id),
 kind text NOT NULL CHECK(kind IN ('official','community')),
 moderation_status text NOT NULL DEFAULT 'pending' CHECK(moderation_status IN ('pending','approved','rejected')),
 CHECK(ends_at IS NULL OR ends_at > starts_at)
);
CREATE INDEX alerts_active_idx ON alerts(starts_at,ends_at) WHERE moderation_status='approved';
CREATE TABLE sync_changes (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 version text NOT NULL REFERENCES data_versions(version), entity text NOT NULL,
 entity_id text NOT NULL, operation text NOT NULL CHECK(operation IN ('upsert','delete')), payload jsonb
);
CREATE INDEX sync_version_idx ON sync_changes(version,id);
-- Requested scope only: does not assert current operation, jurisdiction or operator.
INSERT INTO lines(id,name,type) VALUES
('506','506','comunal'),('518','518','comunal'),('520','520','comunal'),('561','561','comunal'),
('este','Este','comunal'),('oeste','Oeste','comunal'),('norte','Norte','comunal'),('sur','Sur','comunal'),
('273','273','provincial'),('275','275','provincial'),('214','214','provincial'),('307','307','provincial'),
('202','202','provincial'),('215','215','provincial'),('418','418','provincial'),('414','414','provincial'),
('129','129','provincial'),('195','195','provincial'),('unlp','Rondín Universitario UNLP','especial');
COMMIT;
