-- Migration: Punkte-Spalte zu tipps-Tabelle hinzufügen
ALTER TABLE tipps ADD COLUMN punkte INTEGER DEFAULT NULL;
