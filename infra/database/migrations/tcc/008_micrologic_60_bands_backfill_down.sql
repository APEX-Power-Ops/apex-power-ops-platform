-- 008_micrologic_60_bands_backfill_down.sql
-- Reverse 008: remove the backfilled STD/GFD bands for the band-less Micrologic 6.0
-- styles. These styles are genuinely band-less in EasyPower's source (STATE §138),
-- so deleting all their band rows restores the faithful (band-less) state.
BEGIN;
DELETE FROM tcc.etu_std_bands b
USING tcc.etu_sensors s
WHERE b.sensor_id = s.id
  AND s.trip_style_id IN (238, 1919, 1920, 1921, 1922, 2173);
DELETE FROM tcc.etu_gfd_bands g
USING tcc.etu_sensors s
WHERE g.sensor_id = s.id
  AND s.trip_style_id IN (238, 1919, 1920, 1921, 1922, 2173);
COMMIT;
