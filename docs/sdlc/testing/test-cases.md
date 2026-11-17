# Tests

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start summary -->
274 tests · Passed 262 · Failed 11 · Skipped 0 · Not run 1

Acceptance criteria covered: 24/146 · passing: 16/146
<!-- sdlc:auto:end summary -->

<!-- sdlc:auto:start tests -->
## Sprint 1

### US-001: Load the supplied dataset files in one admin ingest run

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-001 | test_ac001_a_patient_row_gets_its_uuid_from_the_server | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[coverage_periods] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[encounter_truth] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[events] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[ingest_file_results] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[ingest_runs] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[intake_answers] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[notes] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[patients] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[personas] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[coverage_periods] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[encounter_truth] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[events] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[ingest_file_results] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[ingest_runs] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[intake_answers] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[notes] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[patients] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[personas] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[coverage_periods] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[encounter_truth] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[events] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[intake_answers] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[notes] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[coverage_periods-columns0] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[encounter_truth-columns1] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[events-columns2] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[intake_answers-columns3] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[notes-columns4] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-003 | test_ac003_ingest_file_results_stores_the_per_file_outcome | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-003 | test_ac003_ingest_runs_stores_the_run_summary_columns | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-004 | test_ac004_dataset_patient_id_is_distinct_from_the_internal_uuid | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_a_gzipped_file_is_decompressed_in_a_stream_not_read_whole | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-001 | test_ac001_every_gzipped_fhir_resource_type_present_is_streamed_and_loaded | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-002 | test_ac002_a_malformed_file_fails_and_leaves_no_partial_rows | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-002 | test_ac002_a_resource_missing_a_required_field_is_rejected_and_named | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-003 | test_ac003_a_second_run_replaces_the_fhir_load_rather_than_duplicating | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-001 | test_ac001_every_file_streams_from_the_configured_location | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-002 | test_ac002_a_malformed_row_is_rejected_and_counted_not_inserted | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-002 | test_ac002_a_missing_required_column_names_the_file_and_column_and_loads_nothing | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-003 | test_ac003_a_second_run_replaces_the_prior_load_rather_than_duplicating | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-004 | test_ac004_progress_is_written_as_the_job_proceeds | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-144, AC-145 | Admin connections and settings > [AC-144/AC-145] a configured deployment shows Connected for both and the dataset version | Unit | Passed | `frontend/src/screens/Admin.test.tsx` |
| AC-145 | Admin connections and settings > [AC-145] an unconfigured deployment shows Not configured and never a credential value | Unit | Passed | `frontend/src/screens/Admin.test.tsx` |
| AC-001, AC-002, AC-003 | Admin ingest report > [AC-001/AC-002/AC-003] a successful run renders passed files with their counts | Unit | Passed | `frontend/src/screens/Admin.test.tsx` |
| AC-003 | Admin ingest report > [AC-003] a failed file's row shows its named reason | Unit | Passed | `frontend/src/screens/Admin.test.tsx` |
| AC-001 | test_ac001_every_required_file_type_is_loaded_with_per_file_row_counts | Integration | Failed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-002 | test_ac002_the_report_carries_version_seed_patient_count_and_a_pass_line_per_file | Integration | Failed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-003 | test_ac003_a_file_missing_a_required_column_fails_and_is_named_with_that_column | Integration | Failed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-004, NFR-021 | test_ac004_nfr021_re_running_replaces_the_prior_load_without_duplicates | Integration | Failed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-005 | test_nfr005_the_loaded_cohort_is_served_from_the_database_not_the_raw_files | Integration | Failed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-006 | test_nfr006_ingest_runs_as_a_background_job_with_progress | Integration | Failed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-023 | test_nfr023_the_supplied_formats_are_read_as_they_are | Integration | Failed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-001 | test_ac001_a_start_without_a_dataset_version_is_422 | Integration | Passed | `backend/tests/integration/test_ingest_run_access.py` |
| AC-001 | test_ac001_starting_a_run_requires_a_bearer_token | Integration | Passed | `backend/tests/integration/test_ingest_run_access.py` |
| AC-002 | test_ac002_an_unknown_run_id_is_404 | Integration | Passed | `backend/tests/integration/test_ingest_run_access.py` |
| AC-002 | test_ac002_the_report_requires_a_bearer_token | Integration | Passed | `backend/tests/integration/test_ingest_run_access.py` |
| AC-001 | test_ac001_a_second_start_while_a_run_is_in_progress_is_409 | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-001 | test_ac001_start_returns_202_with_the_run_summary | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-002 | test_ac002_an_unknown_run_id_is_404 | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-002 | test_ac002_the_report_carries_the_run_summary_and_a_line_per_file | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-003 | test_ac003_a_failed_files_error_names_the_file_and_the_column | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-004 | test_ac004_both_routes_need_the_shared_bearer[Bearer wrong-token] | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-004 | test_ac004_both_routes_need_the_shared_bearer[None] | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-004 | test_ac004_both_routes_need_the_shared_bearer[not-a-bearer] | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |

### US-037: Show the synthetic-data banner on every screen

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-119 | test_ac119_the_notice_says_synthetic_and_not_for_clinical_use | Unit | Passed | `backend/tests/unit/test_synthetic_notice_exports.py` |
| AC-119 | test_ac119_with_notice_adds_it_to_a_payload_without_dropping_its_data | Unit | Passed | `backend/tests/unit/test_synthetic_notice_exports.py` |
| AC-120 | test_ac120_every_page_of_an_export_carries_the_notice | Unit | Passed | `backend/tests/unit/test_synthetic_notice_exports.py` |
| AC-121 | test_ac121_a_page_with_no_body_text_still_carries_the_notice | Unit | Passed | `backend/tests/unit/test_synthetic_notice_exports.py` |
| AC-101 | SyntheticDataNotice > [AC-101][AC-SIMPLIFY] a shell route is still drawn inside the app menu when signed in | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119 | SyntheticDataNotice > [AC-119] an unregistered route still shows the notice after its redirect | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119 | SyntheticDataNotice > [AC-119] states the data is 100% synthetic and not for clinical use | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /admin | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /case-summary | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /insufficient-history | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /my-health | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /set-password | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /sign-in | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /start | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /timeline | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /worklist | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-121 | SyntheticDataNotice > [AC-121] the route table is not empty, so the guardrail below cannot pass vacuously | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| — | SyntheticDataNotice > [AC-SIMPLIFY] /start is still drawn without the app menu | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/demo/personas-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/evaluation/runs/latest-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/patients/me/timeline-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/patients/me/updates-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/patients/me/visit-prep-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/worklist-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_the_demo_replay_carries_the_notice | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_the_evaluation_report_carries_the_notice | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-120, NFR-017 | test_ac120_nfr017_the_referral_packet_has_the_notice_on_every_page | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-120, NFR-017 | test_ac120_nfr017_the_visit_prep_sheet_has_the_notice_on_every_page | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-121, NFR-017 | test_ac121_nfr017_every_data_route_is_covered_at_one_hundred_percent | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |

### US-044: Deploy and configure the application as a managed web app

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-144 | test_ac144_health_reports_ok_and_the_services_it_depends_on | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-144 | test_ac144_settings_reports_the_latest_passed_runs_dataset_version | Integration | Failed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-145, NFR-011 | test_ac145_nfr011_settings_never_contains_a_credential_value | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-145, NFR-011 | test_ac145_nfr011_settings_reports_connected_for_configured_credentials | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-146 | test_ac146_health_succeeds_unauthenticated | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-146, NFR-010 | test_ac146_nfr010_a_wrong_bearer_is_refused | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-146, NFR-010 | test_ac146_nfr010_an_unauthenticated_request_is_refused | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| NFR-010 | test_nfr010_every_patient_and_clinician_route_refuses_an_anonymous_request | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| NFR-010 | test_nfr010_the_api_offers_no_public_sign_up_or_self_service_entry_point | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| NFR-011 | test_nfr011_no_credential_value_appears_in_any_api_response_or_the_openapi_document | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-144 | test_ac144_health_reports_ok_and_the_services_it_depends_on | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-144 | test_ac144_health_stays_reachable_without_any_header | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-144 | test_ac144_settings_reports_the_latest_passed_runs_dataset_version | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-145 | test_ac145_no_credential_value_appears_anywhere_in_the_body | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-145 | test_ac145_settings_report_connected_when_both_are_configured | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-145 | test_ac145_settings_report_not_configured_when_the_database_url_is_absent | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-145 | test_ac145_settings_report_not_configured_when_the_llm_key_is_absent | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[Bearer ] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[Bearer wrong-token] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[None] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[not-a-bearer] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_every_route_except_health_refuses_an_unauthenticated_request | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_the_correct_bearer_passes | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_the_dependency_refuses_without_a_configured_secret | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |

## Sprint 2

### US-002: Keep provenance on every stored fact

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-005 | test_ac005_a_read_item_carries_every_provenance_field | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-005 | test_ac005_any_other_source_type_is_rejected_as_a_provenance_failure | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-005 | test_ac005_every_supplied_source_field_is_carried_onto_the_stored_row | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-005 | test_ac005_the_three_source_types_are_accepted[claim] | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-005 | test_ac005_the_three_source_types_are_accepted[ehr] | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-005 | test_ac005_the_three_source_types_are_accepted[patient] | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-006 | test_ac006_a_read_item_carries_the_note_its_source_ref_resolves_to | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-006 | test_ac006_a_stored_events_source_ref_resolves_to_its_note | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-006 | test_ac006_an_unmatched_source_ref_is_an_explicit_not_found_not_an_error | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-007 | test_ac007_a_row_missing_a_provenance_field_names_the_event_and_the_field[source_ref] | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-007 | test_ac007_a_row_missing_a_provenance_field_names_the_event_and_the_field[source_type] | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-007 | test_ac007_the_report_exposes_provenance_failures_beside_the_row_counts | Unit | Passed | `backend/tests/unit/test_ingest_provenance.py` |
| AC-005 | test_ac005_every_stored_event_the_api_exposes_carries_all_sixteen_provenance_fields | Integration | Failed | `backend/tests/integration/test_provenance.py` |
| AC-006 | test_ac006_an_event_source_ref_resolves_to_the_matching_note_text | Integration | Failed | `backend/tests/integration/test_provenance.py` |
| AC-007 | test_ac007_rows_missing_source_ref_or_source_type_fail_provenance_and_are_not_retrievable | Integration | Failed | `backend/tests/integration/test_provenance.py` |

### US-007: Hold all condition logic in one declarative pack

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-020 | test_ac020_every_workup_item_carries_its_reasoning_text | Integration | Passed | `backend/tests/integration/test_condition_pack_admin.py` |
| AC-020 | test_ac020_the_pack_carries_every_piece_of_condition_logic | Integration | Passed | `backend/tests/integration/test_condition_pack_admin.py` |
| AC-020 | test_ac020_the_pack_carries_the_patient_facing_copy_strings | Integration | Passed | `backend/tests/integration/test_condition_pack_admin.py` |
| AC-022 | test_ac022_ingest_and_timeline_routes_still_answer_with_no_pack | Integration | Passed | `backend/tests/integration/test_condition_pack_admin.py` |
| AC-022 | test_ac022_with_the_pack_disabled_the_app_starts_and_reports_no_active_pack | Integration | Passed | `backend/tests/integration/test_condition_pack_admin.py` |
| NFR-019 | test_nfr019_an_edit_applies_without_a_code_deployment | Integration | Passed | `backend/tests/integration/test_condition_pack_admin.py` |
| — | test_the_pack_routes_are_401_unauthenticated | Integration | Passed | `backend/tests/integration/test_condition_pack_admin.py` |
| — | test_the_pack_routes_are_403_for_a_non_admin_token | Integration | Passed | `backend/tests/integration/test_condition_pack_admin.py` |
| AC-021, NFR-019 | test_ac021_nfr019_no_named_axspa_identifier_is_hard_coded_outside_the_pack | Integration | Passed | `backend/tests/integration/test_condition_pack_scan.py` |
| AC-021, NFR-019 | test_ac021_nfr019_no_pack_code_list_value_is_hard_coded_outside_the_pack | Integration | Passed | `backend/tests/integration/test_condition_pack_scan.py` |
| AC-021 | test_ac021_the_pack_directory_itself_is_excluded_from_the_scan | Integration | Passed | `backend/tests/integration/test_condition_pack_scan.py` |
| AC-021 | test_ac021_the_scan_reports_the_file_and_line_of_a_hit | Integration | Passed | `backend/tests/integration/test_condition_pack_scan.py` |
| AC-020 | test_ac020_get_returns_the_active_pack_as_configuration_data | Integration | Passed | `backend/tests/unit/test_admin_pack_routes.py` |
| AC-022 | test_ac022_get_reports_no_active_pack_when_the_pack_is_disabled | Integration | Passed | `backend/tests/unit/test_admin_pack_routes.py` |
| NFR-019 | test_nfr019_put_persists_the_pack_and_the_next_read_serves_it | Integration | Passed | `backend/tests/unit/test_admin_pack_routes.py` |
| — | test_put_rejects_a_pack_that_fails_schema_validation_naming_the_key | Integration | Passed | `backend/tests/unit/test_admin_pack_routes.py` |
| — | test_the_pack_routes_are_401_without_a_live_session | Integration | Passed | `backend/tests/unit/test_admin_pack_routes.py` |
| — | test_the_pack_routes_are_403_for_a_non_admin_token[clinician] | Integration | Passed | `backend/tests/unit/test_admin_pack_routes.py` |
| — | test_the_pack_routes_are_403_for_a_non_admin_token[patient] | Integration | Passed | `backend/tests/unit/test_admin_pack_routes.py` |
| AC-020 | test_ac020_a_malformed_item_is_reported_naming_the_offending_key | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_a_missing_section_is_reported_naming_the_offending_key | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_a_threshold_that_is_not_a_number_names_its_key | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_criteria_cover_both_a_set_rule_and_a_points_rule | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_every_accessor_answers_by_key | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_every_code_list_names_its_system_and_carries_codes | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_every_counter_evidence_rule_declares_its_demotion_effect | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_every_workup_item_carries_its_reasoning_text | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_listing_packs_includes_the_shipped_pack | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_loading_an_unknown_pack_key_names_that_key | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_the_pack_carries_patient_facing_copy_strings | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-020 | test_ac020_the_shipped_pack_declares_every_required_section | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-022 | test_ac022_generic_timeline_reads_keep_working_with_no_pack | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-022 | test_ac022_health_reports_that_no_condition_pack_is_active | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-022 | test_ac022_no_pack_is_active_when_the_key_is_blank | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-022 | test_ac022_no_pack_is_active_when_the_pack_is_disabled | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-022 | test_ac022_the_configured_pack_is_active_when_enabled | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| AC-022 | test_ac022_the_startup_log_reports_that_no_pack_is_active | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |
| NFR-019 | test_nfr019_pack_content_is_reloadable_without_a_deployment | Integration | Passed | `backend/tests/unit/test_condition_pack.py` |

### US-026: Invite a patient to the product

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-084 | Worklist invite status > [AC-084] a 403 detail is shown inline without crashing the screen | Unit | Passed | `frontend/src/screens/Worklist.test.tsx` |
| AC-084 | Worklist invite status > [AC-084] a 404 on an unknown patient shows its detail inline | Unit | Passed | `frontend/src/screens/Worklist.test.tsx` |
| AC-084 | Worklist invite status > [AC-084] closing the dialog removes the link and it is not re-fetchable from the UI | Unit | Passed | `frontend/src/screens/Worklist.test.tsx` |
| AC-084 | Worklist invite status > [AC-084] inviting a patient posts to /api/invites and shows the link, expiry and copy control | Unit | Passed | `frontend/src/screens/Worklist.test.tsx` |
| AC-085 | Worklist invite status > [AC-085] a failing worklist read surfaces its detail instead of crashing | Unit | Passed | `frontend/src/screens/Worklist.test.tsx` |
| AC-085 | Worklist invite status > [AC-085] each row shows its invite status and 'none' shows no invite badge | Unit | Passed | `frontend/src/screens/Worklist.test.tsx` |
| AC-084 | test_ac084_a_clinician_issues_an_invite_and_is_shown_a_tokenised_link | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-084 | test_ac084_issuing_an_invite_for_an_unknown_patient_is_404 | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-084 | test_ac084_issuing_twice_yields_two_distinct_single_use_tokens | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-085 | test_ac085_the_worklist_row_reports_intake_completed_once_intake_is_complete | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-085 | test_ac085_the_worklist_row_reports_not_yet_opened_then_opened | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-086 | test_ac086_a_patient_token_cannot_issue_an_invite | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-086 | test_ac086_an_unauthenticated_issue_is_401 | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-086 | test_ac086_an_unknown_invite_token_is_404 | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-086, NFR-009 | test_ac086_nfr009_an_accepted_session_reaches_only_that_patients_own_data | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-086, NFR-009 | test_ac086_nfr009_expired_accepted_and_revoked_are_refused_the_same_way | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-086, NFR-009 | test_ac086_nfr009_no_endpoint_returns_or_lists_a_live_token_again | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-086, NFR-009 | test_ac086_nfr009_the_token_is_long_random_and_not_a_uuid | Integration | Passed | `backend/tests/integration/test_patient_invites.py` |
| AC-084 | test_ac084_an_admin_may_issue_and_a_patient_token_is_403 | Integration | Passed | `backend/tests/unit/test_invites.py` |
| AC-084 | test_ac084_an_unknown_patient_is_404_and_a_missing_patient_id_is_422 | Integration | Passed | `backend/tests/unit/test_invites.py` |
| AC-084 | test_ac084_issuing_returns_the_invite_and_its_url_once | Integration | Passed | `backend/tests/unit/test_invites.py` |
| AC-085 | test_ac085_opening_the_link_is_unauthenticated_and_records_the_open | Integration | Passed | `backend/tests/unit/test_invites.py` |
| AC-085 | test_ac085_the_intake_can_be_completed_and_the_worklist_follows | Integration | Passed | `backend/tests/unit/test_invites.py` |
| AC-085 | test_ac085_the_worklist_carries_the_invite_status_through_its_states | Integration | Passed | `backend/tests/unit/test_invites.py` |
| AC-086, NFR-009 | test_ac086_nfr009_the_expiry_comes_from_invite_expiry_hours | Integration | Passed | `backend/tests/unit/test_invites.py` |
| AC-086, NFR-009 | test_ac086_nfr009_the_token_is_unguessable_not_a_uuid_and_stored_only_hashed | Integration | Passed | `backend/tests/unit/test_invites.py` |
| — | test_accepting_an_unknown_token_is_404 | Integration | Passed | `backend/tests/unit/test_invites.py` |
| — | test_accepting_creates_the_patient_user_and_returns_a_session | Integration | Passed | `backend/tests/unit/test_invites.py` |
| — | test_an_unknown_token_is_404_and_an_expired_one_is_409 | Integration | Passed | `backend/tests/unit/test_invites.py` |
| — | test_invite_listings_are_newest_first_by_creation_time | Integration | Passed | `backend/tests/unit/test_invites.py` |
| NFR-009 | test_nfr009_a_revoked_invite_is_refused_like_a_consumed_one | Integration | Passed | `backend/tests/unit/test_invites.py` |
| NFR-009 | test_nfr009_an_invite_is_single_use_and_re_use_is_409 | Integration | Passed | `backend/tests/unit/test_invites.py` |
| NFR-009 | test_nfr009_an_invite_issued_with_a_zero_hour_expiry_is_already_expired | Integration | Passed | `backend/tests/unit/test_invites.py` |
| NFR-009 | test_nfr009_the_session_grants_patient_access_only_to_that_patient | Integration | Passed | `backend/tests/unit/test_invites.py` |

### US-031: Sign in as a clinician with an email and password

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-101 | route guard and session expiry > [AC-101] a clinician route without a token redirects to sign-in | Unit | Passed | `frontend/src/screens/SignIn.test.tsx` |
| AC-101 | route guard and session expiry > [AC-101] sign-out calls logout, clears the token and returns to sign-in | Unit | Passed | `frontend/src/screens/SignIn.test.tsx` |
| AC-102, AC-103 | route guard and session expiry > [AC-102][AC-103] a 401 clears the token and redirects with the expiry message | Unit | Passed | `frontend/src/screens/SignIn.test.tsx` |
| AC-104 | set-password > [AC-104] a rejected token shows the API's detail and stays on the screen | Unit | Passed | `frontend/src/screens/SignIn.test.tsx` |
| AC-104 | set-password > [AC-104] posts the URL token with the new password and returns to sign-in | Unit | Passed | `frontend/src/screens/SignIn.test.tsx` |
| AC-100 | sign-in > [AC-100] a failed sign-in shows the API's detail and stores no token | Unit | Passed | `frontend/src/screens/SignIn.test.tsx` |
| AC-100 | sign-in > [AC-100] a successful sign-in stores the token and lands on the worklist | Unit | Passed | `frontend/src/screens/SignIn.test.tsx` |
| AC-104 | sign-in > [AC-104] must_set_password routes to the set-password screen | Unit | Passed | `frontend/src/screens/SignIn.test.tsx` |
| AC-100 | test_ac100_a_clinician_can_sign_in_and_reach_the_worklist | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-100 | test_ac100_login_compares_the_email_case_insensitively | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-100 | test_ac100_no_response_carries_set_cookie_and_the_token_is_in_the_login_body[/api/auth/login] | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-100 | test_ac100_no_response_carries_set_cookie_and_the_token_is_in_the_login_body[/api/auth/logout] | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-100 | test_ac100_no_response_carries_set_cookie_and_the_token_is_in_the_login_body[/api/auth/me] | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-100 | test_ac100_no_response_carries_set_cookie_and_the_token_is_in_the_login_body[/api/worklist] | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-101, NFR-007 | test_ac101_nfr007_logout_ends_only_the_session_it_was_called_with | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-102, NFR-007 | test_ac102_nfr007_an_idle_session_expires_while_an_active_one_stays_valid | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-103 | test_ac103_deactivating_an_unknown_user_is_404 | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-103, NFR-007 | test_ac103_nfr007_deactivation_revokes_every_session_and_blocks_later_sign_in | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-104 | test_ac104_an_unknown_password_set_token_is_404 | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-104, NFR-008 | test_ac104_nfr008_an_account_without_a_password_cannot_log_in_until_it_is_set | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-104, NFR-008 | test_ac104_nfr008_no_response_ever_returns_a_password_or_a_recoverable_token | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-104 | test_ac104_re_using_a_password_set_token_is_409 | Integration | Passed | `backend/tests/integration/test_auth_sessions.py` |
| AC-100 | test_ac100_a_recorded_decision_carries_the_signed_in_account | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-100 | test_ac100_a_wrong_password_and_a_deactivated_account_are_the_same_401 | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-100 | test_ac100_an_unknown_decision_value_is_422 | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-100 | test_ac100_login_returns_a_token_and_the_acting_account | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-101 | test_ac101_logout_revokes_only_the_presented_session | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-102 | test_ac102_an_idle_session_is_401_and_activity_pushes_the_window_forward | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-103 | test_ac103_deactivate_is_401_unauthenticated_403_non_admin_and_404_unknown | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-103 | test_ac103_deactivation_revokes_every_session_and_blocks_later_logins | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-104 | test_ac104_a_set_password_token_is_single_use_expiring_and_unknown_is_404 | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-104 | test_ac104_an_admin_created_account_has_no_password_and_one_set_password_token | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-104 | test_ac104_an_invited_account_cannot_log_in_until_it_sets_a_password | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |
| AC-104 | test_ac104_creating_a_user_is_401_unauthenticated_and_403_for_a_clinician | Integration | Passed | `backend/tests/unit/test_auth_sessions.py` |

## Project setup

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| — | test_is_idempotent_and_never_rehashes_an_existing_users_password | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| — | test_seeds_nothing_when_no_platform_variables_are_set | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| — | test_seeds_the_admin_and_smoke_test_users_from_exactly_those_names | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| — | test_a_guardrail_result_is_ok_only_with_no_violations | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_allowed_origins_falls_back_to_the_dev_server | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_allowed_origins_reads_a_comma_separated_list | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_an_unknown_tier_sorts_last | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_cache_keys_are_namespaced | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_email_sends_nothing_and_does_not_raise_without_a_credential | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_enqueue_reports_an_unavailable_queue_instead_of_a_connection_error | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_every_setting_has_a_working_local_default | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_insufficient_history_is_a_tier_not_a_missing_value | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_job_status_never_raises_when_the_queue_is_unreachable | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_no_credential_value_is_ever_in_a_connection_status | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_the_active_pack_is_the_enabled_one_of_highest_version | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_the_app_runs_with_no_pack_active | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_the_cache_is_a_miss_rather_than_an_error_without_redis | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_the_llm_reports_connected_with_one | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_the_llm_reports_not_configured_without_a_credential | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_the_session_secret_is_never_the_public_shared_key | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_the_spec_s_job_kinds_are_all_declared | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_the_worklist_orders_high_moderate_insufficient_low | Unit | Passed | `backend/tests/unit/test_scaffolding.py` |
| — | test_disk_creates_parent_directories | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_delete_is_quiet_when_nothing_was_there | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_delete_removes_the_file | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_refuses_a_key_that_escapes_media_root | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_round_trip | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_url_is_a_local_media_path | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_s3_backend_used_when_bucket_configured | Unit | Passed | `backend/tests/unit/test_storage.py` |
| AC-101 | App > [AC-101] renders a screen inside the app shell and shows its menu when signed in | Unit | Passed | `frontend/src/App.test.tsx` |
| AC-101, AC-102 | App > [AC-101][AC-102] sends a clinician route to sign-in when no session is held | Unit | Passed | `frontend/src/App.test.tsx` |
| — | test_health_reports_ok | Integration | Passed | `backend/tests/integration/test_health.py` |
| — | test_the_openapi_document_builds | Integration | Passed | `backend/tests/integration/test_health.py` |
| — | the app loads | E2E | Not run yet | `frontend/e2e/example.spec.ts` |
<!-- sdlc:auto:end tests -->
