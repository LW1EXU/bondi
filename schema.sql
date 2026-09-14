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

-- Paradas oficiales del Gran La Plata con georreferenciación PostGIS
INSERT INTO stops(id, name, location, street_side) VALUES
  ('stop_plaza_moreno', 'Plaza Moreno', ST_SetSRID(ST_MakePoint(-57.9545, -34.9214), 4326)::geography, 'Calle 12 y 51'),
  ('stop_plaza_san_martin', 'Plaza San Martín', ST_SetSRID(ST_MakePoint(-57.9498, -34.9142), 4326)::geography, 'Calle 7 y 50'),
  ('stop_plaza_italia', 'Plaza Italia', ST_SetSRID(ST_MakePoint(-57.9576, -34.9082), 4326)::geography, 'Calle 7 y 44'),
  ('stop_estacion_tren', 'Estación La Plata (Línea Roca)', ST_SetSRID(ST_MakePoint(-57.9463, -34.9048), 4326)::geography, 'Calle 1 y 44'),
  ('stop_terminal_bus', 'Terminal de Ómnibus', ST_SetSRID(ST_MakePoint(-57.9507, -34.9031), 4326)::geography, 'Calle 4 y 42'),
  ('stop_plaza_rocha', 'Plaza Rocha', ST_SetSRID(ST_MakePoint(-57.9419, -34.9248), 4326)::geography, 'Calle 7 y 60'),
  ('stop_plaza_paso', 'Plaza Paso', ST_SetSRID(ST_MakePoint(-57.9652, -34.9155), 4326)::geography, 'Calle 13 y 44'),
  ('stop_hosp_ninos', 'Hospital de Niños', ST_SetSRID(ST_MakePoint(-57.9462, -34.9351), 4326)::geography, 'Calle 14 y 66'),
  ('stop_hosp_san_martin', 'Hospital Policlínico San Martín', ST_SetSRID(ST_MakePoint(-57.9254, -34.9221), 4326)::geography, 'Calle 1 y 70'),
  ('stop_hosp_san_juan', 'Hospital San Juan de Dios', ST_SetSRID(ST_MakePoint(-57.949, -34.9427), 4326)::geography, 'Calle 27 y 70'),
  ('stop_hosp_espanol', 'Hospital Español', ST_SetSRID(ST_MakePoint(-57.962, -34.9002), 4326)::geography, 'Calle 9 y 36'),
  ('stop_estadio_unico', 'Estadio Diego Armando Maradona', ST_SetSRID(ST_MakePoint(-57.9892, -34.9001), 4326)::geography, 'Av. 25 y 32'),
  ('stop_cementerio', 'Cementerio La Plata', ST_SetSRID(ST_MakePoint(-57.9622, -34.9526), 4326)::geography, 'Calle 31 y 72'),
  ('stop_los_hornos_60', 'Los Hornos (Centro)', ST_SetSRID(ST_MakePoint(-57.9942, -34.9548), 4326)::geography, 'Av. 60 y 137'),
  ('stop_los_hornos_66', 'Los Hornos (Sur)', ST_SetSRID(ST_MakePoint(-58.0062, -34.9691), 4326)::geography, 'Av. 66 y 143'),
  ('stop_san_carlos', 'San Carlos', ST_SetSRID(ST_MakePoint(-58.0142, -34.9282), 4326)::geography, 'Av. 32 y 137'),
  ('stop_melchor_romero', 'Melchor Romero', ST_SetSRID(ST_MakePoint(-58.064, -34.9452), 4326)::geography, 'Av. 520 y 173'),
  ('stop_tolosa', 'Tolosa', ST_SetSRID(ST_MakePoint(-57.9732, -34.8872), 4326)::geography, 'Calle 7 y 528'),
  ('stop_rep_ninos', 'República de los Niños', ST_SetSRID(ST_MakePoint(-57.9982, -34.8835), 4326)::geography, 'Cno. General Belgrano y 500'),
  ('stop_gonnet', 'Estación Gonnet', ST_SetSRID(ST_MakePoint(-57.9904, -34.8802), 4326)::geography, 'Cno. Centenario y 502'),
  ('stop_city_bell', 'Estación City Bell', ST_SetSRID(ST_MakePoint(-58.0163, -34.8621), 4326)::geography, 'Cno. Centenario y Cantilo (461)'),
  ('stop_villa_elisa', 'Villa Elisa (Centro)', ST_SetSRID(ST_MakePoint(-58.0381, -34.8482), 4326)::geography, 'Cno. Centenario y Arana (419)'),
  ('stop_berisso_puente_roma', 'Berisso - Puente Roma', ST_SetSRID(ST_MakePoint(-57.8862, -34.8722), 4326)::geography, 'Av. Génova y 158'),
  ('stop_berisso_centro', 'Berisso Centro', ST_SetSRID(ST_MakePoint(-57.8761, -34.8785), 4326)::geography, 'Av. Montevideo y 11'),
  ('stop_berisso_los_talas', 'Berisso - Los Talas', ST_SetSRID(ST_MakePoint(-57.848, -34.8992), 4326)::geography, 'Av. Montevideo y 30'),
  ('stop_ensenada_centro', 'Ensenada - Plaza Belgrano', ST_SetSRID(ST_MakePoint(-57.9102, -34.8601), 4326)::geography, 'Don Bosco y La Merced'),
  ('stop_ensenada_astillero', 'Ensenada - Astillero', ST_SetSRID(ST_MakePoint(-57.9021, -34.8512), 4326)::geography, 'Av. Horacio Cestino y Río Santiago'),
  ('stop_villa_elvira', 'Villa Elvira', ST_SetSRID(ST_MakePoint(-57.9281, -34.9392), 4326)::geography, 'Calle 7 y 80'),
  ('stop_sicardi', 'Parque Sicardi', ST_SetSRID(ST_MakePoint(-57.8862, -34.9921), 4326)::geography, 'Calle 659 y 22'),
  ('stop_unlp_bosque', 'UNLP - Facultades Bosque Central', ST_SetSRID(ST_MakePoint(-57.9412, -34.9082), 4326)::geography, 'Av. 1 y 50'),
  ('stop_unlp_informatica', 'UNLP - Informática / Naturales', ST_SetSRID(ST_MakePoint(-57.9302, -34.9061), 4326)::geography, 'Calle 120 y 52'),
  ('stop_unlp_medicina', 'UNLP - Medicina / Periodismo', ST_SetSRID(ST_MakePoint(-57.9242, -34.9123), 4326)::geography, 'Calle 60 y 120'),
  ('stop_rotonda_autopista', 'Rotonda Autopista La Plata-BsAs', ST_SetSRID(ST_MakePoint(-57.9442, -34.8912), 4326)::geography, 'Av. 120 y 32');

-- Ramales principales para cada una de las 19 líneas
INSERT INTO branches(id, line_id, name, direction, variant, color) VALUES
  ('506_ida', '506', 'Los Hornos ↔ Ensenada por Plaza Moreno', 0, 'regular', '18382B'),
  ('518_ida', '518', 'Aeropuerto ↔ Rep. de los Niños por Pza. Italia', 0, 'regular', '2E7D32'),
  ('520_ida', '520', 'Parque Sicardi ↔ Estación por Los Hornos', 0, 'regular', '388E3C'),
  ('561_ida', '561', 'San Carlos ↔ Estación por Estadio Único', 0, 'regular', '43A047'),
  ('este_ida', 'este', 'Villa Elvira ↔ Plaza Italia por Policlínico', 0, 'regular', '1B5E20'),
  ('oeste_ida', 'oeste', 'Melchor Romero ↔ Estación por Hosp. Español', 0, 'regular', '00796B'),
  ('norte_ida', 'norte', 'City Bell ↔ Plaza Moreno por Gonnet', 0, 'regular', '004D40'),
  ('sur_ida', 'sur', 'Los Hornos ↔ Plaza Italia por Hospitales', 0, 'regular', '00897B'),
  ('273_ida', '273', 'Villa Elisa ↔ Cementerio por City Bell', 0, 'regular', '1565C0'),
  ('275_ida', '275', 'Astillero Río Santiago ↔ Plaza San Martín', 0, 'regular', '0D47A1'),
  ('214_ida', '214', 'Berisso Los Talas ↔ Hospital San Juan de Dios', 0, 'regular', '1976D2'),
  ('307_ida', '307', 'Río Santiago ↔ Cementerio por Estación', 0, 'regular', '0277BD'),
  ('202_ida', '202', 'Berisso Centro ↔ Estación La Plata', 0, 'regular', '0288D1'),
  ('215_ida', '215', 'Tolosa ↔ Melchor Romero por San Carlos', 0, 'regular', '039BE5'),
  ('418_ida', '418', 'Berazategui ↔ Terminal La Plata por Cno. Centenario', 0, 'regular', '00838F'),
  ('414_ida', '414', 'Florencio Varela ↔ Terminal La Plata', 0, 'regular', '29B6F6'),
  ('129_ida', '129', 'CABA Retiro ↔ La Plata por Autopista', 0, 'regular', 'D84315'),
  ('195_ida', '195', 'CABA Retiro ↔ Terminal y Plaza San Martín', 0, 'regular', 'C2185B'),
  ('unlp_ida', 'unlp', 'Circuito Facultades del Bosque UNLP', 0, 'regular', 'E65100');

-- Secuencia de paradas por ramal
INSERT INTO branch_stops(branch_id, stop_id, sequence) VALUES
  ('506_ida', 'stop_los_hornos_60', 0),
  ('506_ida', 'stop_cementerio', 1),
  ('506_ida', 'stop_plaza_moreno', 2),
  ('506_ida', 'stop_plaza_san_martin', 3),
  ('506_ida', 'stop_estacion_tren', 4),
  ('506_ida', 'stop_ensenada_centro', 5),
  ('518_ida', 'stop_plaza_rocha', 0),
  ('518_ida', 'stop_plaza_italia', 1),
  ('518_ida', 'stop_tolosa', 2),
  ('518_ida', 'stop_rep_ninos', 3),
  ('520_ida', 'stop_sicardi', 0),
  ('520_ida', 'stop_villa_elvira', 1),
  ('520_ida', 'stop_los_hornos_60', 2),
  ('520_ida', 'stop_plaza_rocha', 3),
  ('520_ida', 'stop_plaza_san_martin', 4),
  ('520_ida', 'stop_estacion_tren', 5),
  ('561_ida', 'stop_san_carlos', 0),
  ('561_ida', 'stop_estadio_unico', 1),
  ('561_ida', 'stop_plaza_paso', 2),
  ('561_ida', 'stop_plaza_moreno', 3),
  ('561_ida', 'stop_estacion_tren', 4),
  ('este_ida', 'stop_villa_elvira', 0),
  ('este_ida', 'stop_hosp_san_martin', 1),
  ('este_ida', 'stop_unlp_bosque', 2),
  ('este_ida', 'stop_plaza_san_martin', 3),
  ('este_ida', 'stop_plaza_italia', 4),
  ('oeste_ida', 'stop_melchor_romero', 0),
  ('oeste_ida', 'stop_san_carlos', 1),
  ('oeste_ida', 'stop_hosp_espanol', 2),
  ('oeste_ida', 'stop_plaza_italia', 3),
  ('oeste_ida', 'stop_estacion_tren', 4),
  ('norte_ida', 'stop_city_bell', 0),
  ('norte_ida', 'stop_gonnet', 1),
  ('norte_ida', 'stop_rep_ninos', 2),
  ('norte_ida', 'stop_tolosa', 3),
  ('norte_ida', 'stop_plaza_italia', 4),
  ('norte_ida', 'stop_plaza_moreno', 5),
  ('sur_ida', 'stop_los_hornos_66', 0),
  ('sur_ida', 'stop_hosp_san_juan', 1),
  ('sur_ida', 'stop_hosp_ninos', 2),
  ('sur_ida', 'stop_plaza_moreno', 3),
  ('sur_ida', 'stop_plaza_italia', 4),
  ('273_ida', 'stop_villa_elisa', 0),
  ('273_ida', 'stop_city_bell', 1),
  ('273_ida', 'stop_gonnet', 2),
  ('273_ida', 'stop_plaza_italia', 3),
  ('273_ida', 'stop_plaza_moreno', 4),
  ('273_ida', 'stop_cementerio', 5),
  ('275_ida', 'stop_ensenada_astillero', 0),
  ('275_ida', 'stop_ensenada_centro', 1),
  ('275_ida', 'stop_estacion_tren', 2),
  ('275_ida', 'stop_plaza_san_martin', 3),
  ('214_ida', 'stop_berisso_los_talas', 0),
  ('214_ida', 'stop_berisso_centro', 1),
  ('214_ida', 'stop_berisso_puente_roma', 2),
  ('214_ida', 'stop_plaza_san_martin', 3),
  ('214_ida', 'stop_hosp_ninos', 4),
  ('214_ida', 'stop_hosp_san_juan', 5),
  ('307_ida', 'stop_ensenada_astillero', 0),
  ('307_ida', 'stop_ensenada_centro', 1),
  ('307_ida', 'stop_estacion_tren', 2),
  ('307_ida', 'stop_plaza_moreno', 3),
  ('307_ida', 'stop_cementerio', 4),
  ('202_ida', 'stop_berisso_centro', 0),
  ('202_ida', 'stop_berisso_puente_roma', 1),
  ('202_ida', 'stop_unlp_medicina', 2),
  ('202_ida', 'stop_estacion_tren', 3),
  ('215_ida', 'stop_tolosa', 0),
  ('215_ida', 'stop_estacion_tren', 1),
  ('215_ida', 'stop_plaza_san_martin', 2),
  ('215_ida', 'stop_san_carlos', 3),
  ('215_ida', 'stop_melchor_romero', 4),
  ('418_ida', 'stop_villa_elisa', 0),
  ('418_ida', 'stop_city_bell', 1),
  ('418_ida', 'stop_gonnet', 2),
  ('418_ida', 'stop_terminal_bus', 3),
  ('414_ida', 'stop_estacion_tren', 0),
  ('414_ida', 'stop_terminal_bus', 1),
  ('129_ida', 'stop_rotonda_autopista', 0),
  ('129_ida', 'stop_terminal_bus', 1),
  ('129_ida', 'stop_plaza_italia', 2),
  ('195_ida', 'stop_rotonda_autopista', 0),
  ('195_ida', 'stop_terminal_bus', 1),
  ('195_ida', 'stop_plaza_san_martin', 2),
  ('unlp_ida', 'stop_plaza_rocha', 0),
  ('unlp_ida', 'stop_plaza_san_martin', 1),
  ('unlp_ida', 'stop_unlp_bosque', 2),
  ('unlp_ida', 'stop_unlp_informatica', 3),
  ('unlp_ida', 'stop_unlp_medicina', 4);

COMMIT;
