-- vw_sensor_calc_context (current state after MAINT mode migrations)
--
-- Applied via Supabase migrations:
--   create_vw_sensor_calc_context
--   add_maint_columns_to_sensor_calc_context
--   restore_maint_available_add_maint_capable
--
-- Key MAINT columns:
--   maint_available  — runtime toggle (original Access DB value, always false until explicitly enabled)
--   maint_capable    — derived: true when INST or GFPU maint config data exists
--                      COALESCE(mt.maint_inst_calc, -1) != -1 OR COALESCE(mt.maint_gfpu_calc, -1) != -1

CREATE OR REPLACE VIEW vw_sensor_calc_context AS
SELECT
    s.id AS sensor_id,
    s.trip_style_id,
    s.rating,
    s.description AS sensor_desc,
    s.sensor_idx,
    m.name  AS manufacturer_name,
    tt.name AS trip_type_name,
    ts.name AS trip_style_name,

    -- LTPU
    s.ltpu_name, s.ltpu_calc, s.ltpu_func,
    s.ltpu_tol_hi, s.ltpu_tol_lo, s.ltpu_step,
    s.ltpu_mul_name, s.ltpu_c_name,

    -- LTD
    s.ltd_name, s.ltd_func, s.ltd_setting_method, s.ltd_setting_type,
    s.ltd_setting_val, s.ltd_tol_hi, s.ltd_tol_lo, s.ltd_step,
    s.ltd_slope, s.ltd_dly_pty, s.ltd_open_mint, s.ltd_clear_mint,
    s.ltd_allow_curves,

    -- STPU
    s.stpu_name, s.stpu_calc, s.stpu_func,
    s.stpu_tol_hi, s.stpu_tol_lo, s.stpu_step,
    s.stpu_i2t, s.stpu_i2t_val, s.stpu_i2t_type,
    s.stpu_stp_tracks,

    -- INST
    s.inst_name, s.inst_calc, s.inst_func, s.inst_step,
    s.inst_ovr_calc, s.inst_ovr_value,
    s.inst_ovrtol_min, s.inst_ovrtol_max,
    s.inst_delay_opening, s.inst_delay_clearing,
    s.frame_opening, s.frame_closing,
    s.inst_req_inst, s.inst_req_sttrip,
    s.inst_clr_curve, s.inst_clr_char,
    s.inst_curve_calc_clr, s.inst_curve_calc_open,

    -- GFPU
    s.gfpu_name, s.gfpu_calc, s.gfpu_func,
    s.gfpu_tol_hi, s.gfpu_tol_lo, s.gfpu_step,
    s.gfpu_i2t, s.gfpu_i2t_val, s.gfpu_i2t_type,
    s.gfpu_pickup_max,

    -- Misc
    s.incl_ad,

    -- MAINT: runtime toggle (original Access DB value)
    COALESCE(mt.maint_available, false) AS maint_available,

    -- MAINT: derived capability flag (true when INST or GFPU maint data exists)
    (COALESCE(mt.maint_inst_calc, -1) != -1 OR COALESCE(mt.maint_gfpu_calc, -1) != -1) AS maint_capable,

    -- MAINT: reduction factors
    mt.maint_ltpu_reduction,
    mt.maint_stpu_reduction,
    mt.maint_inst_reduction,

    -- MAINT: INST config
    mt.maint_inst_calc, mt.maint_inst_func,
    mt.maint_inst_tol_hi, mt.maint_inst_tol_lo, mt.maint_inst_step,
    mt.maint_inst_ovr_calc, mt.maint_inst_ovr_value,
    mt.maint_inst_delay_opening, mt.maint_inst_delay_clearing,
    mt.maint_frame_opening, mt.maint_frame_closing,
    mt.maint_inst_ovrtol_min, mt.maint_inst_ovrtol_max,

    -- MAINT: GFPU config
    mt.maint_gfpu_calc, mt.maint_gfpu_func,
    mt.maint_gfpu_tol_hi, mt.maint_gfpu_tol_lo, mt.maint_gfpu_step,
    mt.maint_gfpu_i2t, mt.maint_gfpu_i2t_val, mt.maint_gfpu_i2t_type,
    mt.maint_gfpu_pickup_max,
    mt.maint_gf_delay_opening, mt.maint_gf_delay_clearing,
    mt.maint_gf_frame_opening, mt.maint_gf_frame_closing

FROM tcc_etu_sensors s
JOIN tcc_trip_styles ts ON ts.id = s.trip_style_id
JOIN tcc_trip_types  tt ON tt.id = ts.trip_type_id
JOIN tcc_manufacturers m ON m.id = tt.manufacturer_id
LEFT JOIN tcc_etu_sensor_maint mt ON mt.sensor_id = s.id;
