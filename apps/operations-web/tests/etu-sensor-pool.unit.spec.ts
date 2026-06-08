import { expect, test } from '@playwright/test'

import {
  SENSOR_CAP,
  buildSensorPool,
  summarizeSensorTerminal,
  type SensorTerminalInput,
} from '../lib/etu-sensor-pool'
import type { CascadeResponse, EtuBridgeSensorsResponse } from '../lib/breaker-resources'

// ── fixtures ──────────────────────────────────────────────────────────────────
// Mirrors the live WavePro SST bridge (breaker_id 18, PCB): two frames at 800 A,
// each carrying the native Power+/WavePro trip (251) AND the new EntelliGuard TU
// alt-trip (1073) seeded by migration 017.
function bridgeSensor(
  styleId: number,
  frame: string,
  tripType: string,
  tripStyle: string,
  tripStyleId: number,
  sensorId: number,
  rating: number,
): EtuBridgeSensorsResponse['sensors'][number] {
  return {
    breaker_class: 'pcb',
    breaker_id: 18,
    breaker_style_id: styleId,
    breaker_style_frame: frame,
    breaker_model_display: frame,
    tmt_sst_mfr: 'GE',
    tmt_sst_type: tripType,
    tmt_sst_style: tripStyle,
    trip_style_id: tripStyleId,
    sensor_id: sensorId,
    sensor_rating: rating,
    sensor_description: `${rating} A`,
  }
}

const waveproBreakerGrain: EtuBridgeSensorsResponse = {
  breaker_style_id: null,
  breaker_id: 18,
  bridge_match_status: 'matched',
  count: 4,
  sensors: [
    bridgeSensor(1026, 'WPS-08', 'Power+', 'WavePro', 251, 5001, 800),
    bridgeSensor(1026, 'WPS-08', 'Entelliguard TU', 'WavePro', 1073, 7001, 800),
    bridgeSensor(1028, 'WPX-08', 'Power+', 'WavePro', 251, 5002, 800),
    bridgeSensor(1028, 'WPX-08', 'Entelliguard TU', 'WavePro', 1073, 7002, 800),
  ],
}

const waveproFrameGrain: EtuBridgeSensorsResponse = {
  breaker_style_id: 1026,
  breaker_id: 18,
  bridge_match_status: 'matched',
  count: 2,
  sensors: [
    bridgeSensor(1026, 'WPS-08', 'Power+', 'WavePro', 251, 5001, 800),
    bridgeSensor(1026, 'WPS-08', 'Entelliguard TU', 'WavePro', 1073, 7001, 800),
  ],
}

function cascadeWithSensors(count: number): CascadeResponse {
  return {
    level: 'sensors',
    count,
    manufacturers: [],
    trip_types: [],
    trip_styles: [],
    sensors: Array.from({ length: count }, (_, i) => ({
      sensor_id: 9000 + i,
      sensor_rating: 800,
      sensor_desc: '800 A',
      trip_style_id: 536,
      trip_style_name: 'Std',
      trip_type_id: 390,
      trip_type_name: 'Std',
      manufacturer_id: 9,
      manufacturer_name: 'GE',
      has_ltpu: true,
      has_stpu: true,
      has_inst: true,
      has_gfpu: true,
    })),
    plug_values: [],
  }
}

const cascadeCountOnly: CascadeResponse = { ...cascadeWithSensors(0), count: 8 }

const EMPTY: SensorTerminalInput = {
  tStyle: '',
  tCascade: null,
  bStyle: '',
  bId: '',
  bridge: null,
}

// ── the bug: picking a breaker (no frame) must populate the pool ───────────────
test('breaker-grain: picking a breaker (bId, no frame) populates the sensor pool', () => {
  const pool = buildSensorPool({ ...EMPTY, bId: '18', bridge: waveproBreakerGrain })
  expect(pool.length).toBe(4)
})

test('breaker-grain pool surfaces the EntelliGuard TU alt-trip as a compatible device', () => {
  const pool = buildSensorPool({ ...EMPTY, bId: '18', bridge: waveproBreakerGrain })
  expect(pool.some((p) => p.tripType === 'Entelliguard TU')).toBe(true)
})

test('breaker-grain labels include the frame so same-rating frames stay distinct', () => {
  const pool = buildSensorPool({ ...EMPTY, bId: '18', bridge: waveproBreakerGrain })
  // Four rows: two frames (WPS-08, WPX-08) x two trips, all at 800 A. Without the
  // frame in the label the WPS/WPX rows would collide into duplicate text.
  expect(new Set(pool.map((p) => p.label)).size).toBe(4)
  expect(pool.every((p) => /^WP[SX]-08 /.test(p.label))).toBe(true)
})

test('breaker-grain pool carries frame + styleId so the nameplate stays complete', () => {
  const pool = buildSensorPool({ ...EMPTY, bId: '18', bridge: waveproBreakerGrain })
  const row = pool.find((p) => p.sensor_id === 5001)!
  expect(row.frame).toBe('WPS-08')
  expect(row.styleId).toBe(1026)
})

// ── the count must match the dropdown (no more "8 but empty") ──────────────────
test('summary count equals pool size when the breaker-grain terminal is ready', () => {
  const pool = buildSensorPool({ ...EMPTY, bId: '18', bridge: waveproBreakerGrain })
  const summary = summarizeSensorTerminal(
    { ...EMPTY, bId: '18', bridge: waveproBreakerGrain },
    pool,
    true,
  )
  expect(summary.state).toBe('ready')
  expect(summary.count).toBe(pool.length)
  expect(summary.count).toBe(4)
})

// ── regression: existing frame-grain and trip-style terminals still work ───────
test('frame-grain: picking a frame (bStyle) yields its sensors, label without frame prefix', () => {
  const pool = buildSensorPool({ ...EMPTY, bStyle: '1026', bId: '18', bridge: waveproFrameGrain })
  expect(pool.length).toBe(2)
  // At frame grain the frame is already chosen upstream, so it is not re-prefixed.
  expect(pool.every((p) => p.label.startsWith('GE '))).toBe(true)
})

test('trip-style terminal still sources the pool from the trip cascade', () => {
  const pool = buildSensorPool({ ...EMPTY, tStyle: '536', tCascade: cascadeWithSensors(3) })
  expect(pool.length).toBe(3)
  expect(pool.every((p) => p.frame === null)).toBe(true)
})

test('a chosen trip-style leaf wins over the breaker bridge (precise intersection)', () => {
  const pool = buildSensorPool({
    tStyle: '536',
    tCascade: cascadeWithSensors(1),
    bStyle: '1026',
    bId: '18',
    bridge: waveproBreakerGrain,
  })
  expect(pool.length).toBe(1)
  expect(pool[0].sensor_id).toBe(9000)
})

// ── status states drive honest messaging ──────────────────────────────────────
test('idle: nothing selected -> idle, count 0, empty pool', () => {
  const pool = buildSensorPool(EMPTY)
  expect(pool.length).toBe(0)
  expect(summarizeSensorTerminal(EMPTY, pool, false).state).toBe('idle')
})

test('narrow: only a coarse axis picked -> narrow with the reachable universe count', () => {
  const input: SensorTerminalInput = { ...EMPTY, tCascade: cascadeCountOnly }
  const pool = buildSensorPool(input)
  const summary = summarizeSensorTerminal(input, pool, true)
  expect(pool.length).toBe(0)
  expect(summary.state).toBe('narrow')
  expect(summary.count).toBe(8)
})

test('empty: a reached breaker terminal with no bridge match -> empty, count 0', () => {
  const unmatched: EtuBridgeSensorsResponse = {
    breaker_style_id: null,
    breaker_id: 18,
    bridge_match_status: 'unmatched',
    count: 0,
    sensors: [],
  }
  const input: SensorTerminalInput = { ...EMPTY, bId: '18', bridge: unmatched }
  const pool = buildSensorPool(input)
  const summary = summarizeSensorTerminal(input, pool, true)
  expect(pool.length).toBe(0)
  expect(summary.state).toBe('empty')
  expect(summary.count).toBe(0)
})

// ── #1/#2: de-dup the stuttered model + tag retrofit · protection-class ────────
// Mirrors the merged GE EntelliGuard TU: trip type "Entelliguard TU" + model display
// "Entelliguard" (1073 LSIG / 1566 LIG both display "Entelliguard"). The trip axis
// carries has_* flags; the alt-trip map carries the retrofit relation + protection class.
function egtuCascade(): CascadeResponse {
  const mk = (sensorId: number, tripStyleId: number, rating: number) => ({
    sensor_id: sensorId,
    sensor_rating: rating,
    sensor_desc: `${rating} A`,
    trip_style_id: tripStyleId,
    trip_style_name: tripStyleId === 1566 ? 'Wavepro LI' : 'WavePro',
    trip_model_display: 'Entelliguard',
    trip_type_id: 700,
    trip_type_name: 'Entelliguard TU',
    manufacturer_id: 9,
    manufacturer_name: 'GE',
    has_ltpu: true,
    has_stpu: tripStyleId !== 1566,
    has_inst: true,
    has_gfpu: true,
  })
  return {
    level: 'sensors',
    count: 2,
    manufacturers: [],
    trip_types: [],
    trip_styles: [],
    sensors: [mk(7001, 1073, 4000), mk(7002, 1566, 4000)],
    plug_values: [],
  }
}

const EGTU_ALT = {
  1073: { relation: 'retrofit', protectionClass: 'LSIG' },
  1566: { relation: 'retrofit', protectionClass: 'LIG' },
}

test('trip-axis retrofit: de-dups the stuttered model and tags retrofit + class', () => {
  const pool = buildSensorPool({ ...EMPTY, tStyle: '1073', tCascade: egtuCascade(), altTrips: EGTU_ALT })
  const lsig = pool.find((p) => p.tripStyleId === 1073)!
  expect(lsig.tripLabel).toBe('GE Entelliguard TU (retrofit · LSIG)')
  expect(lsig.label).not.toContain('Entelliguard TU Entelliguard')
  expect(lsig.label.startsWith('GE Entelliguard TU (retrofit · LSIG) — ')).toBe(true)
})

test('the protection-class tag distinguishes the merged Entelliguard variants (LSIG vs LIG)', () => {
  const pool = buildSensorPool({ ...EMPTY, tStyle: '1073', tCascade: egtuCascade(), altTrips: EGTU_ALT })
  expect(pool.find((p) => p.tripStyleId === 1566)!.tripLabel).toBe('GE Entelliguard TU (retrofit · LIG)')
})

test('pool items carry trip_style_id for the alt-trip lookup', () => {
  const pool = buildSensorPool({ ...EMPTY, tStyle: '1073', tCascade: egtuCascade() })
  expect(pool.every((p) => p.tripStyleId != null)).toBe(true)
})

test('non-retrofit trips get no tag (and a duplicate model is still de-duped)', () => {
  const pool = buildSensorPool({ ...EMPTY, tStyle: '536', tCascade: cascadeWithSensors(1) })
  expect(pool[0].label).not.toContain('retrofit')
  expect(pool[0].tripLabel).toBe('GE Std') // "Std Std" collapses to "Std"
})

test('breaker-grain retrofit: frame prefix + de-dup + retrofit·class tag', () => {
  const bridge: EtuBridgeSensorsResponse = {
    breaker_style_id: null,
    breaker_id: 18,
    bridge_match_status: 'matched',
    count: 1,
    sensors: [bridgeSensor(1026, 'WPS-08', 'Entelliguard TU', 'WavePro', 1073, 7001, 800)],
  }
  const pool = buildSensorPool({ ...EMPTY, bId: '18', bridge, altTrips: { 1073: { relation: 'retrofit', protectionClass: 'LSIG' } } })
  expect(pool[0].label).toBe('WPS-08 GE Entelliguard TU (retrofit · LSIG) — 800 A (800A)')
})

test('SENSOR_CAP bounds the breaker-grain pool', () => {
  const many: EtuBridgeSensorsResponse = {
    breaker_style_id: null,
    breaker_id: 99,
    bridge_match_status: 'matched',
    count: SENSOR_CAP + 50,
    sensors: Array.from({ length: SENSOR_CAP + 50 }, (_, i) =>
      bridgeSensor(2000 + i, `FR-${i}`, 'Power+', 'X', 251, 40000 + i, 800),
    ),
  }
  const pool = buildSensorPool({ ...EMPTY, bId: '99', bridge: many })
  expect(pool.length).toBe(SENSOR_CAP)
})
