export interface paths {
    "/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me_auth_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/redeem": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Redeem Invitation */
        post: operations["redeem_invitation_auth_redeem_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/dev/cases": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Fixture Cases */
        get: operations["fixture_cases_dev_cases_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/dev/fixture": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Fixture Info */
        get: operations["fixture_info_dev_fixture_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/dev/invitations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Fixture Invitation */
        post: operations["fixture_invitation_dev_invitations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Encounters */
        get: operations["encounters_encounters_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Encounter */
        get: operations["encounter_encounters__encounter_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/call": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** State */
        get: operations["state_encounters__encounter_id__call_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/call/admit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Admit */
        post: operations["admit_encounters__encounter_id__call_admit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/call/connections/{connection_id}/leave": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Leave */
        post: operations["leave_encounters__encounter_id__call_connections__connection_id__leave_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/call/connections/{connection_id}/verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify */
        post: operations["verify_encounters__encounter_id__call_connections__connection_id__verify_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/call/consent": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Consent */
        post: operations["consent_encounters__encounter_id__call_consent_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/call/controls": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Control */
        post: operations["control_encounters__encounter_id__call_controls_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/call/diagnostics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Diagnostics */
        get: operations["diagnostics_encounters__encounter_id__call_diagnostics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/call/utterances": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Utterances */
        get: operations["utterances_encounters__encounter_id__call_utterances_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/commands": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Command */
        post: operations["command_encounters__encounter_id__commands_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/context": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Context */
        get: operations["context_encounters__encounter_id__context_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/context/shared": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Shared Context */
        get: operations["shared_context_encounters__encounter_id__context_shared_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/continuity": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** State */
        get: operations["state_encounters__encounter_id__continuity_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/continuity/delete": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Delete Visit */
        post: operations["delete_visit_encounters__encounter_id__continuity_delete_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/continuity/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload */
        post: operations["upload_encounters__encounter_id__continuity_documents_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/continuity/documents/{document_id}/review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Review */
        post: operations["review_encounters__encounter_id__continuity_documents__document_id__review_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/continuity/family-updates": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Draft */
        post: operations["draft_encounters__encounter_id__continuity_family_updates_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/continuity/family-updates/{update_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_encounters__encounter_id__continuity_family_updates__update_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/continuity/next-visit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Next Visit */
        post: operations["next_visit_encounters__encounter_id__continuity_next_visit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/continuity/sandbox-callbacks/{action_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Repeat Callback */
        post: operations["repeat_callback_encounters__encounter_id__continuity_sandbox_callbacks__action_id__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/evidence/{evidence_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Evidence */
        get: operations["evidence_encounters__encounter_id__evidence__evidence_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/execution": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** State */
        get: operations["state_encounters__encounter_id__execution_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/execution/actions/{action_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_encounters__encounter_id__execution_actions__action_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/execution/actions/{action_id}/prerequisites": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Prerequisites */
        post: operations["prerequisites_encounters__encounter_id__execution_actions__action_id__prerequisites_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/execution/approve-ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve Ready */
        post: operations["approve_ready_encounters__encounter_id__execution_approve_ready_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/execution/items/{item_id}/lookup": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Lookup */
        post: operations["lookup_encounters__encounter_id__execution_items__item_id__lookup_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/execution/items/{item_id}/scope": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Scope */
        post: operations["scope_encounters__encounter_id__execution_items__item_id__scope_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/execution/scenario": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Scenario */
        post: operations["scenario_encounters__encounter_id__execution_scenario_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/invitations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Invite */
        post: operations["invite_encounters__encounter_id__invitations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/invitations/{invitation_id}/revoke": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Revoke Invite */
        post: operations["revoke_invite_encounters__encounter_id__invitations__invitation_id__revoke_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/members": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Members */
        get: operations["members_encounters__encounter_id__members_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/members/{membership_id}/revoke": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Revoke Member */
        post: operations["revoke_member_encounters__encounter_id__members__membership_id__revoke_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/speech": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** State */
        get: operations["state_encounters__encounter_id__speech_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/speech/actions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Action */
        post: operations["action_encounters__encounter_id__speech_actions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/speech/agreement": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Agree */
        post: operations["agree_encounters__encounter_id__speech_agreement_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/speech/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_encounters__encounter_id__speech_approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/speech/mode": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mode */
        post: operations["mode_encounters__encounter_id__speech_mode_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/stream": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Stream */
        get: operations["stream_encounters__encounter_id__stream_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/understanding": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** State */
        get: operations["state_encounters__encounter_id__understanding_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/understanding/fixture-turns": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Turn */
        post: operations["turn_encounters__encounter_id__understanding_fixture_turns_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/understanding/plan/{item_id}/correct": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Plan */
        post: operations["plan_encounters__encounter_id__understanding_plan__item_id__correct_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/understanding/processing": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Processing */
        post: operations["processing_encounters__encounter_id__understanding_processing_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/understanding/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retry */
        post: operations["retry_encounters__encounter_id__understanding_retry_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/encounters/{encounter_id}/understanding/sources/{source_id}/correct": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Source */
        post: operations["source_encounters__encounter_id__understanding_sources__source_id__correct_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/live": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Live */
        get: operations["live_health_live_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Ready */
        get: operations["ready_health_ready_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/integrations/office/results": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Office Callback */
        post: operations["office_callback_integrations_office_results_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** ActionView */
        ActionView: {
            /** Checked At */
            checked_at?: string | null;
            /**
             * Clinician Confirmed
             * @default false
             */
            clinician_confirmed: boolean;
            /** Digest */
            digest?: string | null;
            /**
             * Document
             * @default lab order
             */
            document: string;
            /** Fingerprint */
            fingerprint?: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Item Id
             * Format: uuid
             */
            item_id: string;
            /**
             * Kind
             * @default lab
             * @enum {string}
             */
            kind: "lab" | "imaging" | "referral" | "prescription";
            /** Message */
            message: string;
            /**
             * Order Available
             * @default false
             */
            order_available: boolean;
            /**
             * Patient Authorized
             * @default false
             */
            patient_authorized: boolean;
            /**
             * Place
             * @default lab
             */
            place: string;
            /** Receipt */
            receipt?: {
                [key: string]: unknown;
            } | null;
            /**
             * Scope Allowed
             * @default false
             */
            scope_allowed: boolean;
            /** Slot */
            slot?: {
                [key: string]: unknown;
            } | null;
            /**
             * Source
             * @default Local sandbox office
             */
            source: string;
            /** State */
            state: string;
            /** Title */
            title: string;
            /**
             * Window
             * @enum {string}
             */
            window: "morning" | "afternoon";
        };
        /** ApprovalRequest */
        ApprovalRequest: {
            /** Digest */
            digest: string;
        };
        /** AudioReceipt */
        AudioReceipt: {
            /**
             * Connection Id
             * Format: uuid
             */
            connection_id: string;
            /** Consent Epoch */
            consent_epoch: number;
            /**
             * First Received At
             * Format: date-time
             */
            first_received_at: string;
            /** Frames */
            frames: number;
            /**
             * Last Received At
             * Format: date-time
             */
            last_received_at: string;
            /** Non Silent Frames */
            non_silent_frames: number;
            /** Samples */
            samples: number;
            /** Track Epoch */
            track_epoch: number;
            /** Track Sid */
            track_sid: string;
        };
        /** BundleOutcome */
        BundleOutcome: {
            /**
             * Action Id
             * Format: uuid
             */
            action_id: string;
            /** Message */
            message: string;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "queued" | "already_approved" | "waiting" | "refused";
        };
        /** BundleRequest */
        BundleRequest: {
            /** Digests */
            digests: string[];
        };
        /** BundleResult */
        BundleResult: {
            /** Outcomes */
            outcomes: components["schemas"]["BundleOutcome"][];
            /**
             * Unmatched
             * @default 0
             */
            unmatched: number;
        };
        /** CallAdmission */
        CallAdmission: {
            call: components["schemas"]["CallView"];
            /**
             * Connection Id
             * Format: uuid
             */
            connection_id: string;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Server Url */
            server_url: string;
            /** Token */
            token: string;
        };
        /** CallControl */
        CallControl: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /** Expected Revision */
            expected_revision: number;
            /** Silenced */
            silenced?: boolean | null;
            /**
             * Type
             * @enum {string}
             */
            type: "pause" | "resume" | "silence" | "end";
        };
        /** CallDiagnostics */
        CallDiagnostics: {
            /** Active Tasks */
            active_tasks: number;
            /** Receipts */
            receipts: components["schemas"]["AudioReceipt"][];
            /** Stopped Epoch */
            stopped_epoch: number;
        };
        /** CallParticipant */
        CallParticipant: {
            /**
             * Connection Id
             * Format: uuid
             */
            connection_id: string;
            /**
             * Consent
             * @enum {string}
             */
            consent: "pending" | "agreed" | "declined";
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /** Name */
            name: string;
            /** Present */
            present: boolean;
            /**
             * Role
             * @enum {string}
             */
            role: "patient" | "clinician" | "family";
            /** Track Epoch */
            track_epoch: number;
        };
        /** CallView */
        CallView: {
            /**
             * Audio Recorded
             * @default false
             * @constant
             */
            audio_recorded: false;
            /** Consent Epoch */
            consent_epoch: number;
            /**
             * Encounter Id
             * Format: uuid
             */
            encounter_id: string;
            /** Gap Since */
            gap_since?: string | null;
            /**
             * Generation
             * Format: uuid
             */
            generation: string;
            /** Manual Pause */
            manual_pause: boolean;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Output Silenced */
            output_silenced: boolean;
            /** Own Connection Id */
            own_connection_id?: string | null;
            /** Participants */
            participants: components["schemas"]["CallParticipant"][];
            /**
             * Provider
             * @enum {string}
             */
            provider: "fixture" | "deepgram" | "unavailable";
            /** Revision */
            revision: number;
            /**
             * State
             * @enum {string}
             */
            state: "waiting" | "consent_needed" | "active" | "paused" | "stopping" | "unavailable" | "ended";
            /**
             * Terms Version
             * @default voice-processing-v1
             * @constant
             */
            terms_version: "voice-processing-v1";
            /**
             * Transcripts Shared
             * @default false
             * @constant
             */
            transcripts_shared: false;
            /** Worker Ready */
            worker_ready: boolean;
        };
        /** CommandEnvelope */
        CommandEnvelope: {
            /** Command */
            command: components["schemas"]["TitleChanged"] | components["schemas"]["PrioritySelectionChanged"] | components["schemas"]["SharingChanged"] | components["schemas"]["PreparationApproved"] | components["schemas"]["PriorityEdited"] | components["schemas"]["SuggestionAdded"] | components["schemas"]["SuggestionReviewed"];
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /** Evidence Refs */
            evidence_refs?: string[];
            /** Expected Version */
            expected_version: number;
        };
        /** CommandResult */
        CommandResult: {
            /** Duplicate */
            duplicate: boolean;
            encounter: components["schemas"]["EncounterView"];
            event: components["schemas"]["EventEnvelope"];
        };
        /** ConsentRequest */
        ConsentRequest: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /**
             * Connection Id
             * Format: uuid
             */
            connection_id: string;
            /**
             * Decision
             * @enum {string}
             */
            decision: "agreed" | "declined";
            /**
             * Terms Version
             * @constant
             */
            terms_version: "voice-processing-v1";
        };
        /** ContextView */
        ContextView: {
            /**
             * Audience
             * @enum {string}
             */
            audience: "patient" | "clinician" | "family";
            /** Consent Epoch */
            consent_epoch: number;
            /**
             * Encounter Id
             * Format: uuid
             */
            encounter_id: string;
            /** Evidence */
            evidence: components["schemas"]["Evidence"][];
            /** Plan */
            plan: components["schemas"]["PlanItem"][];
            /** Priorities */
            priorities: components["schemas"]["Priority"][];
        };
        /** ContinuityView */
        ContinuityView: {
            /** Callback Count */
            callback_count: number;
            /** Conversation Gap Since */
            conversation_gap_since?: string | null;
            /** Documents */
            documents: components["schemas"]["DocumentView"][];
            /** Family Recipients */
            family_recipients: {
                [key: string]: unknown;
            }[];
            /** Family Updates */
            family_updates: components["schemas"]["FamilyUpdateView"][];
            /** Next Visits */
            next_visits: {
                [key: string]: unknown;
            }[];
            /**
             * Sandbox Tools Enabled
             * @default false
             */
            sandbox_tools_enabled: boolean;
        };
        /** CueApproval */
        CueApproval: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /**
             * Cue Id
             * Format: uuid
             */
            cue_id: string;
            /** Digest */
            digest: string;
        };
        /** DeleteRequest */
        DeleteRequest: {
            /**
             * Confirmation
             * @constant
             */
            confirmation: "DELETE SYNTHETIC VISIT";
            /** Expected Version */
            expected_version: number;
        };
        /** Difference */
        Difference: {
            /** End */
            end: number;
            /** Expected */
            expected?: string | null;
            /** Explanation */
            explanation: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "timing" | "location" | "clinical_instruction" | "review";
            /** Plan Id */
            plan_id?: string | null;
            /** Source Quote */
            source_quote: string;
            /** Start */
            start: number;
        };
        /** DigestRequest */
        DigestRequest: {
            /** Digest */
            digest: string;
        };
        /** DocumentUpload */
        DocumentUpload: {
            /** File Base64 */
            file_base64?: string | null;
            /**
             * Format
             * @default text
             * @enum {string}
             */
            format: "text" | "pdf";
            /** Plan Ids */
            plan_ids?: string[];
            /** Text */
            text?: string | null;
            /** Title */
            title: string;
        };
        /** DocumentView */
        DocumentView: {
            /** Differences */
            differences: components["schemas"]["Difference"][];
            /** Fingerprint */
            fingerprint?: string | null;
            /**
             * Format
             * @enum {string}
             */
            format: "text" | "pdf";
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Pages */
            pages: {
                [key: string]: unknown;
            }[];
            /** Review Note */
            review_note?: string | null;
            /**
             * Review State
             * @enum {string}
             */
            review_state: "unresolved" | "reviewed" | "stale";
            /** Reviewed By */
            reviewed_by?: string | null;
            /** Sha256 */
            sha256: string;
            source: components["schemas"]["Evidence"];
        };
        /** EncounterSummary */
        EncounterSummary: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Patient Name */
            patient_name: string;
            /** Title */
            title: string;
            /** Version */
            version: number;
        };
        /** EncounterView */
        EncounterView: {
            /** Clinician */
            clinician: string;
            /**
             * Consent Epoch
             * @default 0
             */
            consent_epoch: number;
            /** Evidence */
            evidence: components["schemas"]["Evidence"][];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            patient: components["schemas"]["Patient"];
            /** Plan */
            plan: components["schemas"]["PlanItem"][];
            /**
             * Preparation Approved
             * @default false
             */
            preparation_approved: boolean;
            /** Priorities */
            priorities: components["schemas"]["Priority"][];
            /**
             * Processing State
             * @enum {string}
             */
            processing_state: "preparing" | "active" | "paused" | "ended";
            /** Suggestions */
            suggestions?: components["schemas"]["Suggestion"][];
            /**
             * Synthetic
             * @default true
             * @constant
             */
            synthetic: true;
            /** Title */
            title: string;
            understanding?: components["schemas"]["UnderstandingStatus"] | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
            /**
             * Viewer Role
             * @default patient
             * @enum {string}
             */
            viewer_role: "patient" | "clinician" | "family";
            /**
             * Visit At
             * Format: date-time
             */
            visit_at: string;
        };
        /** EventEnvelope */
        EventEnvelope: {
            /**
             * Accepted At
             * Format: date-time
             */
            accepted_at: string;
            /** Command */
            command: components["schemas"]["TitleChanged"] | components["schemas"]["PrioritySelectionChanged"] | components["schemas"]["SharingChanged"] | components["schemas"]["PreparationApproved"] | components["schemas"]["PriorityEdited"] | components["schemas"]["SuggestionAdded"] | components["schemas"]["SuggestionReviewed"];
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /**
             * Encounter Id
             * Format: uuid
             */
            encounter_id: string;
            /** Evidence Refs */
            evidence_refs: string[];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Sequence */
            sequence: number;
        };
        /** Evidence */
        Evidence: {
            /** Audiences */
            audiences?: ("clinician" | "family")[];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Origin */
            origin?: ("fixture" | "deepgram" | "human") | null;
            /**
             * Source Type
             * @enum {string}
             */
            source_type: "patient_report" | "office_message" | "imported_record" | "conversation";
            /** Speaker */
            speaker?: string | null;
            /** Text */
            text: string;
            /** Title */
            title: string;
            /**
             * Version
             * @default 1
             */
            version: number;
        };
        /** ExecutionView */
        ExecutionView: {
            /** Actions */
            actions: components["schemas"]["ActionView"][];
            /** Configured */
            configured: boolean;
            /**
             * Sandbox
             * @default true
             * @constant
             */
            sandbox: true;
        };
        /** FamilyDraftRequest */
        FamilyDraftRequest: {
            /** Fields */
            fields: ("title" | "owner" | "timeframe" | "office_status")[];
            /** Plan Ids */
            plan_ids: string[];
            /**
             * Recipient Id
             * Format: uuid
             */
            recipient_id: string;
        };
        /** FamilyUpdateView */
        FamilyUpdateView: {
            /** Digest */
            digest?: string | null;
            /** Fields */
            fields: string[];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Receipt */
            receipt?: {
                [key: string]: unknown;
            } | null;
            /**
             * Recipient Id
             * Format: uuid
             */
            recipient_id: string;
            /** State */
            state: string;
            /** Text */
            text: string;
        };
        /** FixtureLaunch */
        FixtureLaunch: {
            /**
             * Case
             * @default maria
             * @enum {string}
             */
            case: "maria" | "james" | "asha";
            /**
             * Persona
             * @enum {string}
             */
            persona: "patient" | "clinician" | "family";
        };
        /** FixtureTurn */
        FixtureTurn: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /**
             * Speaker
             * @enum {string}
             */
            speaker: "patient" | "clinician" | "family";
            /** Text */
            text: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** Health */
        Health: {
            /** Database */
            database?: ("ready" | "unavailable") | null;
            /**
             * Status
             * @enum {string}
             */
            status: "alive" | "ready" | "unavailable";
        };
        /** Identity */
        Identity: {
            /** Csrf Token */
            csrf_token: string;
            /**
             * Encounter Id
             * Format: uuid
             */
            encounter_id: string;
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /** Name */
            name: string;
            /**
             * Role
             * @enum {string}
             */
            role: "patient" | "clinician" | "family";
        };
        /** Invitation */
        Invitation: {
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Token */
            token: string;
        };
        /** InviteRequest */
        InviteRequest: {
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
        };
        /** LookupRequest */
        LookupRequest: {
            /**
             * Day
             * @default 2026-10-20
             */
            day: string;
            /**
             * Location
             * @default Riverside Lab
             */
            location: string;
            /**
             * Window
             * @enum {string}
             */
            window: "morning" | "afternoon";
        };
        /** MemberView */
        MemberView: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Revoked */
            revoked: boolean;
            /**
             * Role
             * @enum {string}
             */
            role: "patient" | "clinician" | "family";
        };
        /** ModeRequest */
        ModeRequest: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "private" | "on_request" | "closeout";
        };
        /** Mutation */
        Mutation: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
        };
        /** NextVisitCreated */
        NextVisitCreated: {
            /**
             * Encounter Id
             * Format: uuid
             */
            encounter_id: string;
            invitation: components["schemas"]["Invitation"];
        };
        /** NextVisitRequest */
        NextVisitRequest: {
            /** Plan Ids */
            plan_ids: string[];
            /**
             * Visit At
             * Format: date-time
             */
            visit_at: string;
        };
        /** Patient */
        Patient: {
            /** Age */
            age: number;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Preferred Name */
            preferred_name: string;
        };
        /** PlanCorrection */
        PlanCorrection: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /** Detail */
            detail: string;
            /** Expected Item Revision */
            expected_item_revision: number;
            /** Location */
            location: string | null;
            /** Owner */
            owner: string | null;
            /** Timeframe */
            timeframe: string | null;
        };
        /** PlanItem */
        PlanItem: {
            /** Audiences */
            audiences?: ("clinician" | "family")[];
            /**
             * Clinician Confirmed
             * @default false
             */
            clinician_confirmed: boolean;
            /** Dependencies */
            dependencies?: string[];
            /** Detail */
            detail: string;
            /** Evidence Refs */
            evidence_refs: string[];
            /**
             * Explanation
             * @default
             */
            explanation: string;
            /**
             * External Completed
             * @default false
             */
            external_completed: boolean;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Kind */
            kind?: ("lab" | "imaging" | "referral" | "prescription" | "other") | null;
            /** Location */
            location?: string | null;
            /**
             * Needs Clarification
             * @default true
             */
            needs_clarification: boolean;
            /**
             * Order Available
             * @default false
             */
            order_available: boolean;
            /**
             * Origin
             * @default preparation
             * @enum {string}
             */
            origin: "preparation" | "interpretation" | "human";
            /** Owner */
            owner?: string | null;
            /**
             * Patient Authorized
             * @default false
             */
            patient_authorized: boolean;
            /**
             * Revision
             * @default 1
             */
            revision: number;
            /**
             * Status
             * @default draft
             * @enum {string}
             */
            status: "draft" | "waiting" | "confirmed";
            /** Timeframe */
            timeframe?: string | null;
            /** Title */
            title: string;
        };
        /** PreparationApproved */
        PreparationApproved: {
            /** Approved */
            approved: boolean;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "preparation.approved";
        };
        /** PrerequisiteRequest */
        PrerequisiteRequest: {
            /** Expected Fingerprint */
            expected_fingerprint: string;
            /**
             * Order
             * @default false
             */
            order: boolean;
        };
        /** Priority */
        Priority: {
            /** Answer Audiences */
            answer_audiences?: ("clinician" | "family")[];
            /** Answer Detail */
            answer_detail?: string | null;
            /** Answer Refs */
            answer_refs?: string[];
            /**
             * Approved
             * @default false
             */
            approved: boolean;
            /** Audiences */
            audiences?: ("clinician" | "family")[];
            /** Detail */
            detail: string;
            /** Evidence Refs */
            evidence_refs: string[];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Selected */
            selected: boolean;
            /**
             * Status
             * @default open
             * @enum {string}
             */
            status: "open" | "partly_answered" | "answered" | "deferred";
            /** Title */
            title: string;
        };
        /** PriorityEdited */
        PriorityEdited: {
            /** Detail */
            detail: string;
            /**
             * Priority Id
             * Format: uuid
             */
            priority_id: string;
            /** Title */
            title: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "priority.edited";
        };
        /** PrioritySelectionChanged */
        PrioritySelectionChanged: {
            /**
             * Priority Id
             * Format: uuid
             */
            priority_id: string;
            /** Selected */
            selected: boolean;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "priority.selection_changed";
        };
        /** PrivateCue */
        PrivateCue: {
            /** Blocked Reason */
            blocked_reason: string;
            /** Digest */
            digest: string;
            /** Eligible To Speak */
            eligible_to_speak: boolean;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Public Text */
            public_text: string;
            /** Score */
            score: number;
            /** State */
            state: string;
            /** Suggestion */
            suggestion: string;
            /** Title */
            title: string;
        };
        /** ProcessingRequest */
        ProcessingRequest: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /** Enabled */
            enabled: boolean;
        };
        /** RedeemRequest */
        RedeemRequest: {
            /** Token */
            token: string;
        };
        /** ReviewRequest */
        ReviewRequest: {
            /** Fingerprint */
            fingerprint: string;
            /** Note */
            note: string;
        };
        /** ScenarioRequest */
        ScenarioRequest: {
            /**
             * Kind
             * @default lab
             * @enum {string}
             */
            kind: "lab" | "imaging" | "referral" | "prescription";
            /**
             * Mode
             * @enum {string}
             */
            mode: "normal" | "no_slot" | "expired" | "delayed" | "rejected" | "timeout_after_write" | "duplicate_callback";
        };
        /** ScopeRequest */
        ScopeRequest: {
            /** Allowed */
            allowed: boolean;
        };
        /** SharingChanged */
        SharingChanged: {
            /** Audiences */
            audiences: ("clinician" | "family")[];
            /**
             * Item Id
             * Format: uuid
             */
            item_id: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "sharing.changed";
        };
        /** SourceCorrection */
        SourceCorrection: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /** Expected Source Version */
            expected_source_version: number;
            /** Text */
            text: string;
        };
        /** SpeakingConsent */
        SpeakingConsent: {
            /** Agreed */
            agreed: boolean;
            /**
             * Connection Id
             * Format: uuid
             */
            connection_id: string;
            /** Name */
            name: string;
        };
        /** SpeechAction */
        SpeechAction: {
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /**
             * Type
             * @enum {string}
             */
            type: "refresh" | "stop" | "closeout";
        };
        /** SpeechAgreement */
        SpeechAgreement: {
            /** Agreed */
            agreed: boolean;
            /**
             * Command Id
             * Format: uuid
             */
            command_id: string;
            /**
             * Connection Id
             * Format: uuid
             */
            connection_id: string;
            /** Mode Revision */
            mode_revision: number;
        };
        /** SpeechReceipt */
        SpeechReceipt: {
            /** Approval To Audio Ms */
            approval_to_audio_ms: number | null;
            /**
             * Approved At
             * Format: date-time
             */
            approved_at: string;
            /** End Of Input To Audio Ms */
            end_of_input_to_audio_ms: number | null;
            /** First Audio At */
            first_audio_at: string | null;
            /**
             * Hearing Confirmed
             * @default false
             * @constant
             */
            hearing_confirmed: false;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Played Ms */
            played_ms: number;
            /** Played Text */
            played_text: string | null;
            /** Reason */
            reason: string | null;
            /** Recognition Delay Ms */
            recognition_delay_ms?: number | null;
            /** State */
            state: string;
            /** Stop Detected At */
            stop_detected_at?: string | null;
            /** Stopped At */
            stopped_at: string | null;
        };
        /** SpeechView */
        SpeechView: {
            /** Consents */
            consents: components["schemas"]["SpeakingConsent"][];
            /** Cues */
            cues: components["schemas"]["PrivateCue"][];
            /**
             * Floor
             * @enum {string}
             */
            floor: "idle" | "waiting" | "generating" | "speaking" | "paused" | "unavailable";
            /** Message */
            message: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "private" | "on_request" | "closeout";
            /** Mode Revision */
            mode_revision: number;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /**
             * Provider
             * @enum {string}
             */
            provider: "fixture" | "cartesia" | "unavailable";
            /** Provider Model */
            provider_model: string;
            /** Quiet Seconds */
            quiet_seconds: number;
            /** Receipts */
            receipts: components["schemas"]["SpeechReceipt"][];
            /** Revision */
            revision: number;
        };
        /** Suggestion */
        Suggestion: {
            /**
             * Author Id
             * Format: uuid
             */
            author_id: string;
            /** Author Name */
            author_name: string;
            /** Detail */
            detail: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Status
             * @default pending
             * @enum {string}
             */
            status: "pending" | "accepted" | "rejected";
            /** Title */
            title: string;
        };
        /** SuggestionAdded */
        SuggestionAdded: {
            /** Detail */
            detail: string;
            /** Title */
            title: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "suggestion.added";
        };
        /** SuggestionReviewed */
        SuggestionReviewed: {
            /**
             * Decision
             * @enum {string}
             */
            decision: "accepted" | "rejected";
            /**
             * Suggestion Id
             * Format: uuid
             */
            suggestion_id: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "suggestion.reviewed";
        };
        /** TitleChanged */
        TitleChanged: {
            /** Title */
            title: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "encounter.title_changed";
        };
        /** UnderstandingStatus */
        UnderstandingStatus: {
            /**
             * Enabled
             * @default false
             */
            enabled: boolean;
            /**
             * Fixture Input Enabled
             * @default false
             */
            fixture_input_enabled: boolean;
            /**
             * Message
             * @default
             */
            message: string;
            /**
             * Model
             * @default original-scenarios-v1
             */
            model: string;
            /**
             * Processed Revision
             * @default 0
             */
            processed_revision: number;
            /**
             * Prompt Version
             * @default visit-extraction-v4
             */
            prompt_version: string;
            /**
             * Provider
             * @default fixture
             * @enum {string}
             */
            provider: "fixture" | "openai" | "deepseek" | "unavailable";
            /**
             * Revision
             * @default 0
             */
            revision: number;
            /**
             * State
             * @default off
             * @enum {string}
             */
            state: "off" | "queued" | "processing" | "ready" | "unavailable" | "paused";
        };
        /** Utterance */
        Utterance: {
            /**
             * Connection Id
             * Format: uuid
             */
            connection_id: string;
            /** Consent Epoch */
            consent_epoch: number;
            /**
             * Finalized At
             * Format: date-time
             */
            finalized_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Membership Id
             * Format: uuid
             */
            membership_id: string;
            /**
             * Provider
             * @constant
             */
            provider: "deepgram";
            /** Text */
            text: string;
            /** Track Epoch */
            track_epoch: number;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    logout_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    me_auth_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Identity"];
                };
            };
        };
    };
    redeem_invitation_auth_redeem_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RedeemRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Identity"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    fixture_cases_dev_cases_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    fixture_info_dev_fixture_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    fixture_invitation_dev_invitations_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FixtureLaunch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Invitation"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    encounters_encounters_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EncounterSummary"][];
                };
            };
        };
    };
    encounter_encounters__encounter_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EncounterView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    state_encounters__encounter_id__call_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admit_encounters__encounter_id__call_admit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallAdmission"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    leave_encounters__encounter_id__call_connections__connection_id__leave_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                connection_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    verify_encounters__encounter_id__call_connections__connection_id__verify_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                connection_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    consent_encounters__encounter_id__call_consent_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConsentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    control_encounters__encounter_id__call_controls_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CallControl"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    diagnostics_encounters__encounter_id__call_diagnostics_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallDiagnostics"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    utterances_encounters__encounter_id__call_utterances_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Utterance"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    command_encounters__encounter_id__commands_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CommandEnvelope"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CommandResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    context_encounters__encounter_id__context_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContextView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    shared_context_encounters__encounter_id__context_shared_get: {
        parameters: {
            query: {
                audience: "clinician" | "family";
            };
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContextView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    state_encounters__encounter_id__continuity_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContinuityView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_visit_encounters__encounter_id__continuity_delete_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DeleteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_encounters__encounter_id__continuity_documents_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DocumentUpload"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContinuityView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    review_encounters__encounter_id__continuity_documents__document_id__review_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                document_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContinuityView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    draft_encounters__encounter_id__continuity_family_updates_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FamilyDraftRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContinuityView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_encounters__encounter_id__continuity_family_updates__update_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                update_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DigestRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContinuityView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    next_visit_encounters__encounter_id__continuity_next_visit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NextVisitRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NextVisitCreated"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    repeat_callback_encounters__encounter_id__continuity_sandbox_callbacks__action_id__post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                action_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    evidence_encounters__encounter_id__evidence__evidence_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                evidence_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Evidence"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    state_encounters__encounter_id__execution_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExecutionView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_encounters__encounter_id__execution_actions__action_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                action_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExecutionView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    prerequisites_encounters__encounter_id__execution_actions__action_id__prerequisites_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                action_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PrerequisiteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExecutionView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_ready_encounters__encounter_id__execution_approve_ready_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BundleRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BundleResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    lookup_encounters__encounter_id__execution_items__item_id__lookup_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LookupRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExecutionView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    scope_encounters__encounter_id__execution_items__item_id__scope_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ScopeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExecutionView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    scenario_encounters__encounter_id__execution_scenario_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ScenarioRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    invite_encounters__encounter_id__invitations_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InviteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Invitation"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    revoke_invite_encounters__encounter_id__invitations__invitation_id__revoke_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                invitation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    members_encounters__encounter_id__members_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MemberView"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    revoke_member_encounters__encounter_id__members__membership_id__revoke_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                membership_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EncounterView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    state_encounters__encounter_id__speech_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SpeechView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    action_encounters__encounter_id__speech_actions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SpeechAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SpeechView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    agree_encounters__encounter_id__speech_agreement_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SpeechAgreement"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SpeechView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_encounters__encounter_id__speech_approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CueApproval"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SpeechView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mode_encounters__encounter_id__speech_mode_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ModeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SpeechView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    stream_encounters__encounter_id__stream_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    state_encounters__encounter_id__understanding_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnderstandingStatus"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    turn_encounters__encounter_id__understanding_fixture_turns_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FixtureTurn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EncounterView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    plan_encounters__encounter_id__understanding_plan__item_id__correct_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlanCorrection"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EncounterView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    processing_encounters__encounter_id__understanding_processing_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProcessingRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EncounterView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    retry_encounters__encounter_id__understanding_retry_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Mutation"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EncounterView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    source_encounters__encounter_id__understanding_sources__source_id__correct_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                encounter_id: string;
                source_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SourceCorrection"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EncounterView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    live_health_live_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    ready_health_ready_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    office_callback_integrations_office_results_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
}
