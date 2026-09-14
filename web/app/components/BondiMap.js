'use client';

import React, { useState, useEffect, useRef } from 'react';
import { STOPS, LINES, calculateArrivals } from '../data/transport';
import 'leaflet/dist/leaflet.css';

export default function BondiMap() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({});
  const polylineRef = useRef(null);

  const [selectedLineId, setSelectedLineId] = useState('all');
  const [selectedStopId, setSelectedStopId] = useState('stop_plaza_moreno');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());

  // Live timer tick every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Initialize Leaflet map
  useEffect(() => {
    let isMounted = true;
    let L = null;

    async function initMap() {
      if (!mapContainerRef.current || mapInstanceRef.current) return;
      L = (await import('leaflet')).default;

      if (!isMounted || !mapContainerRef.current) return;

      const map = L.map(mapContainerRef.current, {
        center: [-34.9214, -57.9545],
        zoom: 13,
        zoomControl: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
      }).addTo(map);

      mapInstanceRef.current = map;

      // Add markers for all stops
      STOPS.forEach((stop) => {
        const customIcon = L.divIcon({
          className: 'bondi-marker',
          html: `<div class="marker-pin" id="pin-${stop.id}"><span class="pin-icon">🚏</span></div>`,
          iconSize: [32, 32],
          iconAnchor: [16, 32],
          popupAnchor: [0, -32],
        });

        const marker = L.marker([stop.lat, stop.lon], { icon: customIcon }).addTo(map);
        marker.on('click', () => {
          setSelectedStopId(stop.id);
          map.panTo([stop.lat, stop.lon], { animate: true, duration: 0.6 });
        });

        markersRef.current[stop.id] = marker;
      });
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update line route and active stops when selectedLineId changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    import('leaflet').then((module) => {
      const L = module.default;
      const map = mapInstanceRef.current;
      if (!map) return;

      // Remove existing polyline if any
      if (polylineRef.current) {
        map.removeLayer(polylineRef.current);
        polylineRef.current = null;
      }

      const activeLine = LINES.find((l) => l.id === selectedLineId);

      // Update markers visibility / styling
      STOPS.forEach((stop) => {
        const marker = markersRef.current[stop.id];
        if (!marker) return;

        const isIncluded = !activeLine || stop.lines.includes(selectedLineId);
        const isSelected = stop.id === selectedStopId;

        const pinClass = isSelected
          ? 'marker-pin selected'
          : isIncluded
          ? 'marker-pin'
          : 'marker-pin dimmed';

        const customIcon = L.divIcon({
          className: 'bondi-marker',
          html: `<div class="${pinClass}"><span class="pin-icon">${isSelected ? '⭐' : '🚏'}</span></div>`,
          iconSize: isSelected ? [40, 40] : [30, 30],
          iconAnchor: isSelected ? [20, 40] : [15, 30],
        });
        marker.setIcon(customIcon);
        marker.setZIndexOffset(isSelected ? 1000 : isIncluded ? 100 : 0);
      });

      // Draw polyline if specific line selected
      if (activeLine) {
        const lineCoords = activeLine.stops
          .map((sid) => STOPS.find((s) => s.id === sid))
          .filter(Boolean)
          .map((s) => [s.lat, s.lon]);

        if (lineCoords.length > 1) {
          const polyline = L.polyline(lineCoords, {
            color: activeLine.color || '#18382B',
            weight: 5,
            opacity: 0.85,
            dashArray: '8, 8',
          }).addTo(map);
          polylineRef.current = polyline;
          map.fitBounds(polyline.getBounds(), { padding: [40, 40] });
        }
      }
    });
  }, [selectedLineId, selectedStopId]);

  // Center on selected stop when changed
  useEffect(() => {
    if (!mapInstanceRef.current || !selectedStopId) return;
    const stop = STOPS.find((s) => s.id === selectedStopId);
    if (stop) {
      mapInstanceRef.current.panTo([stop.lat, stop.lon], { animate: true, duration: 0.5 });
    }
  }, [selectedStopId]);

  const selectedStop = STOPS.find((s) => s.id === selectedStopId) || STOPS[0];
  const arrivals = selectedStop ? calculateArrivals(selectedStop.id, currentTime) : [];
  const nextBus = arrivals[0];

  // Search filtered stops
  const filteredStops = STOPS.filter((stop) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      stop.name.toLowerCase().includes(q) ||
      stop.address.toLowerCase().includes(q) ||
      stop.landmark.toLowerCase().includes(q) ||
      stop.lines.some((l) => l.toLowerCase().includes(q))
    );
  });

  // Format seconds to mm:ss
  const formatCountdown = (totalSec) => {
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  return (
    <div className="map-wrapper">
      {/* Map Control Toolbar */}
      <div className="map-toolbar">
        <div className="filter-group">
          <label htmlFor="line-select">Línea de micro:</label>
          <select
            id="line-select"
            value={selectedLineId}
            onChange={(e) => setSelectedLineId(e.target.value)}
            className="select-input"
          >
            <option value="all">Todas las líneas ({LINES.length})</option>
            {LINES.map((line) => (
              <option key={line.id} value={line.id}>
                Línea {line.name} ({line.type})
              </option>
            ))}
          </select>
        </div>

        <div className="search-group">
          <input
            type="text"
            placeholder="🔍 Buscar parada, calle o lugar..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="clock-display">
          <span className="live-dot">●</span>
          <span>Hora actual: {currentTime.toLocaleTimeString('es-AR')}</span>
        </div>
      </div>

      <div className="map-content-layout">
        {/* Leaflet Map Canvas */}
        <div className="map-canvas-container" ref={mapContainerRef}>
          {/* Fallback while map loads */}
          <noscript>Por favor, habilita JavaScript para ver el mapa interactivo.</noscript>
        </div>

        {/* Selected Stop Details & Real-Time Countdown Panel */}
        <aside className="stop-detail-panel">
          {selectedStop ? (
            <div className="panel-inner">
              <div className="stop-header">
                <div>
                  <span className="eyebrow">PARADA SELECCIONADA</span>
                  <h3>{selectedStop.name}</h3>
                  <p className="stop-address">📍 {selectedStop.address}</p>
                  <p className="stop-landmark">ℹ️ {selectedStop.landmark}</p>
                </div>
              </div>

              {/* PRIMARY PROMINENT COUNTDOWN TIMER */}
              {nextBus ? (
                <div className="countdown-card">
                  <div className="countdown-badge-row">
                    <span
                      className="line-tag"
                      style={{ backgroundColor: nextBus.line_color || '#18382B' }}
                    >
                      Línea {nextBus.line_name}
                    </span>
                    <span className="status-badge">
                      <span className="pulse-icon">●</span> EN CAMINO
                    </span>
                  </div>

                  <p className="headsign-title">{nextBus.headsign}</p>

                  <div className="timer-box">
                    <span className="timer-label">TIEMPO ESTIMADO DE LLEGADA</span>
                    <div className="timer-digits">
                      {nextBus.eta_seconds <= 45 ? (
                        <span className="arriving-now">¡LLEGANDO!</span>
                      ) : (
                        <>
                          <span className="digits">{formatCountdown(nextBus.eta_seconds)}</span>
                          <span className="unit">min:seg</span>
                        </>
                      )}
                    </div>
                    <div className="clock-time">
                      Horario programado: <strong>{nextBus.scheduled_time} hs</strong>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="no-arrivals">
                  No hay micros previstos en los próximos minutos para esta parada.
                </div>
              )}

              {/* UPCOMING BUSES LIST */}
              <div className="upcoming-section">
                <h4>Próximos arribos a esta parada ({arrivals.length})</h4>
                <div className="arrivals-list">
                  {arrivals.map((arr, idx) => (
                    <div key={`${arr.line_id}-${idx}`} className="arrival-item">
                      <div className="arr-line-info">
                        <span
                          className="mini-line-tag"
                          style={{ backgroundColor: arr.line_color || '#18382B' }}
                        >
                          {arr.line_name}
                        </span>
                        <div className="arr-text">
                          <span className="arr-headsign">{arr.headsign}</span>
                          <span className="arr-clock">Previsto a las {arr.scheduled_time} hs</span>
                        </div>
                      </div>

                      <div className="arr-countdown">
                        <span className="arr-time">
                          {arr.eta_seconds <= 45 ? 'Llegando' : formatCountdown(arr.eta_seconds)}
                        </span>
                        <span className="arr-eta-min">{arr.eta_minutes} min</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Stop lines summary */}
              <div className="stop-lines-footer">
                <span className="footer-title">Líneas con parada aquí:</span>
                <div className="chip-row">
                  {selectedStop.lines.map((lid) => {
                    const lObj = LINES.find((l) => l.id === lid);
                    return (
                      <button
                        key={lid}
                        className={`line-chip ${selectedLineId === lid ? 'active' : ''}`}
                        onClick={() => setSelectedLineId(selectedLineId === lid ? 'all' : lid)}
                        title={`Ver recorrido de línea ${lObj ? lObj.name : lid}`}
                      >
                        {lObj ? lObj.name : lid}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-selection">
              <p>Seleccioná cualquier parada en el mapa para ver sus próximos micros y la cuenta regresiva en vivo.</p>
            </div>
          )}

          {/* Quick stop selector list if searched */}
          {searchQuery && (
            <div className="search-results-overlay">
              <h5>Resultados de búsqueda ({filteredStops.length})</h5>
              <ul>
                {filteredStops.map((stop) => (
                  <li
                    key={stop.id}
                    onClick={() => {
                      setSelectedStopId(stop.id);
                      setSearchQuery('');
                    }}
                  >
                    <strong>{stop.name}</strong>
                    <span>{stop.address}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
