# Tests

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start summary -->
380 tests · Passed 379 · Failed 0 · Skipped 0 · Not run 1

Acceptance criteria covered: 35/146 · passing: 35/146
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
| AC-001 | test_ac001_every_required_file_type_is_loaded_with_per_file_row_counts | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-002 | test_ac002_the_report_carries_version_seed_patient_count_and_a_pass_line_per_file | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-003 | test_ac003_a_file_missing_a_required_column_fails_and_is_named_with_that_column | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-004, NFR-021 | test_ac004_nfr021_re_running_replaces_the_prior_load_without_duplicates | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-005 | test_nfr005_the_loaded_cohort_is_served_from_the_database_not_the_raw_files | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-006 | test_nfr006_ingest_runs_as_a_background_job_with_progress | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-023 | test_nfr023_the_supplied_formats_are_read_as_they_are | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
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
| AC-144 | test_ac144_settings_reports_the_latest_passed_runs_dataset_version | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
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
| AC-005 | test_ac005_every_stored_event_the_api_exposes_carries_all_sixteen_provenance_fields | Integration | Passed | `backend/tests/integration/test_provenance.py` |
| AC-006 | test_ac006_an_event_source_ref_resolves_to_the_matching_note_text | Integration | Passed | `backend/tests/integration/test_provenance.py` |
| AC-007 | test_ac007_rows_missing_source_ref_or_source_type_fail_provenance_and_are_not_retrievable | Integration | Passed | `backend/tests/integration/test_provenance.py` |

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

## Sprint 3

### US-003: Quarantine ground-truth labels away from the engine

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-010 | test_ac010_the_case_read_states_no_ground_truth_field | Unit | Passed | `backend/tests/unit/test_case_timeline_cutoff.py` |
| AC-029 | test_ac029_a_patient_with_no_label_row_states_a_null_cutoff | Unit | Passed | `backend/tests/unit/test_case_timeline_cutoff.py` |
| AC-029 | test_ac029_the_case_read_states_the_patients_evaluation_cutoff | Unit | Passed | `backend/tests/unit/test_case_timeline_cutoff.py` |
| AC-009 | test_ac009_both_allowed_modules_do_name_the_accessor | Unit | Passed | `backend/tests/unit/test_evaluation_scan.py` |
| AC-009 | test_ac009_ground_truth_is_read_only_by_the_labels_store_and_the_evaluation_module | Unit | Passed | `backend/tests/unit/test_evaluation_scan.py` |
| AC-009 | test_ac009_the_scan_reports_the_file_and_line_of_a_hit | Unit | Passed | `backend/tests/unit/test_evaluation_scan.py` |
| AC-008 | test_ac008_ingest_loads_labels_into_the_label_store | Unit | Passed | `backend/tests/unit/test_labels_store.py` |
| AC-008 | test_ac008_re_running_ingest_replaces_the_label_load | Unit | Passed | `backend/tests/unit/test_labels_store.py` |
| AC-008 | test_ac008_the_operational_accessor_returns_only_the_two_permitted_keys | Unit | Passed | `backend/tests/unit/test_labels_store.py` |
| AC-009 | test_ac009_the_evaluation_accessor_returns_the_ground_truth_columns | Unit | Passed | `backend/tests/unit/test_labels_store.py` |
| AC-010 | test_ac010_asking_for_a_ground_truth_field_raises | Unit | Passed | `backend/tests/unit/test_labels_store.py` |
| AC-010 | test_ac010_the_allowlist_is_a_module_level_constant | Unit | Passed | `backend/tests/unit/test_labels_store.py` |
| AC-010 | test_ac010_the_single_field_accessor_answers_for_a_permitted_field | Unit | Passed | `backend/tests/unit/test_labels_store.py` |
| AC-010 | test_ac010_the_single_field_accessor_refuses_a_ground_truth_field | Unit | Passed | `backend/tests/unit/test_labels_store.py` |
| AC-008 | test_ac008_no_input_set_carries_a_ground_truth_key_under_any_name | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-008 | test_ac008_the_scan_finds_a_ground_truth_key_wherever_it_hides | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-027 | test_ac027_a_patient_with_no_cutoff_keeps_todays_behaviour | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-027 | test_ac027_an_item_dated_exactly_on_the_cutoff_is_excluded | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-027 | test_ac027_the_boundary_helper_is_strictly_before_the_cutoff | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-027 | test_ac027_the_undated_family_history_row_is_included | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-028 | test_ac028_a_confirmed_case_shows_neither_its_diagnosis_nor_its_workup | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-029 | test_ac029_a_seeded_leaking_patient_yields_a_non_empty_violation_list | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-029 | test_ac029_the_guardrail_passes_over_a_clean_cohort | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-029 | test_ac029_the_whole_cohort_passes_once_the_filter_is_in_place | Unit | Passed | `backend/tests/unit/test_leakage_inputs.py` |
| AC-008, NFR-013 | test_ac008_nfr013_no_ground_truth_field_reaches_any_rendered_patient_payload | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-008 | test_ac008_the_patients_own_screens_carry_no_ground_truth | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-009 | test_ac009_the_evaluation_report_still_reports_sensitivity_and_ppv | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-010 | test_ac010_only_the_cutoff_and_the_split_reach_the_engine_or_the_demo_path | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-010 | test_ac010_the_operational_accessor_refuses_a_ground_truth_field | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-028 | test_ac028_a_confirmed_case_shows_neither_its_diagnosis_nor_its_workup | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-029 | test_ac029_an_item_dated_exactly_on_the_cutoff_is_excluded | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-029, NFR-013 | test_ac029_nfr013_no_rendered_read_of_any_patient_carries_a_post_cutoff_item | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-029, NFR-013 | test_ac029_nfr013_the_undated_family_history_row_is_the_one_allowed_exception | Integration | Passed | `backend/tests/integration/test_leakage_guarantee.py` |
| AC-009 | test_ac009_a_perfect_cohort_scores_one_on_both_measures | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| AC-009 | test_ac009_an_undefined_measure_is_none_rather_than_zero | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| AC-009 | test_ac009_ground_truth_is_read_through_the_evaluation_only_accessor | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| AC-009 | test_ac009_sensitivity_and_ppv_are_computed_over_the_seeded_cohort | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| AC-009 | test_ac009_staff_get_sensitivity_ppv_the_split_and_the_synthetic_notice | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| AC-009 | test_ac009_the_response_carries_no_per_patient_ground_truth_value | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| AC-009 | test_ac009_the_route_is_401_unauthenticated | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| AC-009 | test_ac009_the_route_is_403_for_a_patient_token | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| — | test_the_report_names_a_mixed_cohort_rather_than_one_of_its_splits | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |
| — | test_the_report_states_the_cohort_split_it_evaluated_on | Integration | Passed | `backend/tests/unit/test_evaluation_report.py` |

### US-004: De-duplicate EHR and claim views of the same encounter

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-011 | test_ac011_a_merged_encounter_counts_as_one_visit | Unit | Passed | `backend/tests/unit/test_encounter_dedup.py` |
| AC-011 | test_ac011_a_near_in_time_claim_with_the_same_code_merges | Unit | Passed | `backend/tests/unit/test_encounter_dedup.py` |
| AC-011 | test_ac011_grouping_keys_are_server_generated_uuids | Unit | Passed | `backend/tests/unit/test_encounter_dedup.py` |
| AC-011 | test_ac011_merge_items_never_invents_an_entry_without_a_source_row | Unit | Passed | `backend/tests/unit/test_encounter_dedup.py` |
| AC-011 | test_ac011_the_merge_is_safe_to_run_twice | Unit | Passed | `backend/tests/unit/test_encounter_dedup.py` |
| AC-011 | test_ac011_two_ehr_rows_are_never_merged_with_each_other | Unit | Passed | `backend/tests/unit/test_encounter_dedup.py` |
| AC-011 | test_ac011_two_genuinely_separate_visits_stay_two_entries | Unit | Passed | `backend/tests/unit/test_encounter_dedup.py` |
| AC-011 | test_ac011_two_source_rows_of_one_encounter_become_one_entry | Unit | Passed | `backend/tests/unit/test_encounter_dedup.py` |
| AC-004 | Admin de-duplication panel > [AC-004-3] a 403 on the job read shows the API's detail and no credential value | Unit | Passed | `frontend/src/screens/AdminDedup.test.tsx` |
| AC-004 | Admin de-duplication panel > [AC-004-3] a 404 on the job read shows the API's detail | Unit | Passed | `frontend/src/screens/AdminDedup.test.tsx` |
| AC-004 | Admin de-duplication panel > [AC-004-3] a failed job shows a readable message, not a blank panel | Unit | Passed | `frontend/src/screens/AdminDedup.test.tsx` |
| AC-004 | Admin de-duplication panel > [AC-004-3] starts the job with kind dedup_check and shows progress while it runs | Unit | Passed | `frontend/src/screens/AdminDedup.test.tsx` |
| AC-004, AC-013 | Admin de-duplication panel > [AC-004-3][AC-013] a finished job renders the four counts with thousands separators | Unit | Passed | `frontend/src/screens/AdminDedup.test.tsx` |
| AC-002 | Admin ingest summary totals > [AC-002] a finished run reports loaded, rejected and passed totals once, consistently | Unit | Passed | `frontend/src/screens/AdminDedup.test.tsx` |
| AC-011 | test_ac011_an_encounter_in_both_sources_is_one_entry_tagged_with_both | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-011 | test_ac011_the_merged_encounter_is_counted_once_in_a_visit_count_signal | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-012 | test_ac012_an_unknown_job_id_is_404 | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-012 | test_ac012_an_unknown_job_kind_is_422 | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-012 | test_ac012_the_check_runs_as_a_job_and_reports_matched_split_and_merged_in_error | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-012 | test_ac012_the_job_reports_its_kind_and_progress_while_it_runs | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-012 | test_ac012_the_job_routes_are_401_unauthenticated | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-012 | test_ac012_the_job_routes_are_403_for_a_patient_token | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-012 | test_ac012_the_report_names_the_dataset_version_it_checked | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-013 | test_ac013_an_encounter_in_no_source_is_counted_as_invisible_care | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-013 | test_ac013_invisible_care_is_never_drawn_in_a_timeline_case_view_or_export | Integration | Passed | `backend/tests/integration/test_dedup_check.py` |
| AC-012 | test_ac012_an_unknown_job_id_is_404 | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-012 | test_ac012_an_unknown_kind_is_422 | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-012 | test_ac012_queueing_the_check_is_202_with_job_id_kind_and_status | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-012 | test_ac012_the_check_counts_matched_split_and_merged_in_error | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-012 | test_ac012_the_check_is_safe_to_run_twice | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-012 | test_ac012_the_job_routes_are_401_unauthenticated | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-012 | test_ac012_the_job_routes_are_403_for_a_non_admin_token | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-012 | test_ac012_the_queued_job_reports_its_kind_status_progress_and_result | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-013 | test_ac013_an_encounter_in_no_source_is_counted_as_invisible_care | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |
| AC-013 | test_ac013_invisible_care_is_never_created_as_a_timeline_entry | Integration | Passed | `backend/tests/unit/test_dedup_check.py` |

### US-017: Configure the LLM credential as deployment configuration

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-057 | Admin settings credential panel > [AC-057] a 403 on the settings call renders a readable message, not a blank panel | Unit | Passed | `frontend/src/screens/AdminSettings.test.tsx` |
| AC-057 | Admin settings credential panel > [AC-057] a configured deployment reads Connected for both the LLM and the database | Unit | Passed | `frontend/src/screens/AdminSettings.test.tsx` |
| AC-057 | Admin settings credential panel > [AC-057] an unconfigured deployment reads Not configured for both and shows no value | Unit | Passed | `frontend/src/screens/AdminSettings.test.tsx` |
| AC-057 | Admin settings credential panel > [AC-057] the LLM credential is a masked placeholder labelled as deployment configuration | Unit | Passed | `frontend/src/screens/AdminSettings.test.tsx` |
| AC-056, NFR-011 | test_ac056_nfr011_no_log_line_written_while_serving_the_settings_page_carries_it | Integration | Passed | `backend/tests/integration/test_llm_credential_configuration.py` |
| AC-056, NFR-011 | test_ac056_nfr011_no_screen_payload_carries_the_llm_credential_value | Integration | Passed | `backend/tests/integration/test_llm_credential_configuration.py` |
| AC-056, NFR-011 | test_ac056_nfr011_the_llm_credential_is_read_from_deployment_configuration | Integration | Passed | `backend/tests/integration/test_llm_credential_configuration.py` |
| AC-056, NFR-011 | test_ac056_nfr011_the_llm_credential_value_is_in_no_file_in_source_control | Integration | Passed | `backend/tests/integration/test_llm_credential_configuration.py` |
| AC-057, NFR-011 | test_ac057_nfr011_an_unconfigured_credential_reads_not_configured | Integration | Passed | `backend/tests/integration/test_llm_credential_configuration.py` |
| AC-057, NFR-011 | test_ac057_nfr011_the_settings_page_never_names_a_credential_environment_value | Integration | Passed | `backend/tests/integration/test_llm_credential_configuration.py` |
| AC-057, NFR-011 | test_ac057_nfr011_the_settings_page_shows_a_masked_placeholder_and_connected | Integration | Passed | `backend/tests/integration/test_llm_credential_configuration.py` |
| AC-057 | test_ac057_the_status_is_only_ever_connected_or_not_configured | Integration | Passed | `backend/tests/integration/test_llm_credential_configuration.py` |
| AC-056 | test_ac056_a_deliberately_logged_key_is_redacted | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |
| AC-056 | test_ac056_exception_text_from_a_failed_anthropic_call_is_redacted | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |
| AC-056 | test_ac056_llm_api_key_is_accepted_as_the_generic_name | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |
| AC-056 | test_ac056_no_credential_value_is_committed_anywhere_in_the_repository | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |
| AC-056 | test_ac056_the_credential_is_read_from_anthropic_api_key_at_call_time | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |
| AC-056 | test_ac056_the_database_connection_string_is_redacted_the_same_way | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |
| AC-056 | test_ac056_there_is_no_default_or_placeholder_credential | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |
| AC-057, NFR-011 | test_ac057_nfr011_settings_mask_both_credentials_and_report_their_status | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |
| AC-057 | test_ac057_settings_report_not_configured_with_no_llm_credential | Integration | Passed | `backend/tests/unit/test_credential_configuration.py` |

## Project setup

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| — | test_is_idempotent_and_never_rehashes_an_existing_users_password | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| — | test_seeds_nothing_when_no_platform_variables_are_set | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| — | test_seeds_the_admin_and_smoke_test_users_from_exactly_those_names | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| AC-004 | test_ac004_a_rerun_purges_a_patient_that_already_has_an_invite_and_a_decision | Unit | Passed | `backend/tests/unit/test_ingest_purge.py` |
| AC-004 | test_ac004_a_run_that_cannot_purge_is_reported_failed_not_left_running | Unit | Passed | `backend/tests/unit/test_ingest_purge.py` |
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
| — | test_a_run_started_moments_ago_is_trusted_before_its_job_reaches_the_queue | Integration | Passed | `backend/tests/unit/test_ingest_run_liveness.py` |
| — | test_an_orphaned_run_does_not_block_a_new_start_and_is_closed_off[queued] | Integration | Passed | `backend/tests/unit/test_ingest_run_liveness.py` |
| — | test_an_orphaned_run_does_not_block_a_new_start_and_is_closed_off[running] | Integration | Passed | `backend/tests/unit/test_ingest_run_liveness.py` |
| — | test_an_unreadable_queue_falls_back_to_the_age_of_the_row | Integration | Passed | `backend/tests/unit/test_ingest_run_liveness.py` |
| NFR-021 | test_nfr021_a_run_whose_job_is_still_on_the_queue_is_a_409 | Integration | Passed | `backend/tests/unit/test_ingest_run_liveness.py` |
| — | the app loads | E2E | Not run yet | `frontend/e2e/example.spec.ts` |
<!-- sdlc:auto:end tests -->
