-- Migration: is_finished-Spalte zu spiele-Tabelle hinzufügen
ALTER TABLE spiele ADD COLUMN is_finished BOOLEAN DEFAULT 0;
