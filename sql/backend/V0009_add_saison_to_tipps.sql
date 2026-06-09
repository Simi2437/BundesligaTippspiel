-- Migration: saison-Spalte zu tipps-Tabelle hinzufügen
-- Backfill der bestehenden Einträge erfolgt via Python (cross-DB Join) in migrator_backend.py
ALTER TABLE tipps ADD COLUMN saison TEXT;

