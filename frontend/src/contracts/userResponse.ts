import { z } from 'zod';

/* ================================================================
   VARUNA Canonical Final Response Contract — UserResponseV1
   Source of truth: docs/ADEEY_ARCHITECTURE_ENGINEER.md §6
   Status: Proposed v1 (client-side contract & runtime validation)
   ================================================================ */

// 1. Core Enums
export const VerdictSchema = z.enum(['SAFE', 'CAUTION', 'UNSAFE', 'UNKNOWN']);
export type Verdict = z.infer<typeof VerdictSchema>;

export const DecisionStatusSchema = z.enum(['complete', 'degraded', 'indeterminate', 'error']);
export type DecisionStatus = z.infer<typeof DecisionStatusSchema>;

export const ConfidenceBandSchema = z.enum(['high', 'medium', 'low', 'unknown']);
export type ConfidenceBand = z.infer<typeof ConfidenceBandSchema>;

export const ClaimKindSchema = z.enum([
  'risk_rule',
  'observation',
  'forecast',
  'geofence',
  'recommendation',
  'regulation',
]);
export type ClaimKind = z.infer<typeof ClaimKindSchema>;

export const MapLayerTypeSchema = z.enum([
  'pfz',
  'hazard_zone',
  'geofence',
  'route',
  'user_location',
  'advisory_area',
]);
export type MapLayerType = z.infer<typeof MapLayerTypeSchema>;

export const RuleSeveritySchema = z.enum(['safe', 'caution', 'unsafe', 'info']);
export type RuleSeverity = z.infer<typeof RuleSeveritySchema>;

export const FreshnessStatusSchema = z.enum(['fresh', 'stale', 'missing', 'unknown']);
export type FreshnessStatus = z.infer<typeof FreshnessStatusSchema>;

export const NoticeTypeSchema = z.enum(['info', 'warning', 'advisory', 'danger']);
export type NoticeType = z.infer<typeof NoticeTypeSchema>;

// 2. RFC 7946 GeoJSON Schemas (WGS84, [lon, lat] coordinate order)
export const PositionSchema = z.union([
  z.tuple([z.number(), z.number()]),
  z.tuple([z.number(), z.number(), z.number()]),
]);
export type Position = z.infer<typeof PositionSchema>;

export const GeoJsonPointSchema = z.object({
  type: z.literal('Point'),
  coordinates: PositionSchema,
});

export const GeoJsonMultiPointSchema = z.object({
  type: z.literal('MultiPoint'),
  coordinates: z.array(PositionSchema),
});

export const GeoJsonLineStringSchema = z.object({
  type: z.literal('LineString'),
  coordinates: z.array(PositionSchema),
});

export const GeoJsonMultiLineStringSchema = z.object({
  type: z.literal('MultiLineString'),
  coordinates: z.array(z.array(PositionSchema)),
});

export const GeoJsonPolygonSchema = z.object({
  type: z.literal('Polygon'),
  coordinates: z.array(z.array(PositionSchema)),
});

export const GeoJsonMultiPolygonSchema = z.object({
  type: z.literal('MultiPolygon'),
  coordinates: z.array(z.array(z.array(PositionSchema))),
});

export const GeoJsonGeometrySchema = z.discriminatedUnion('type', [
  GeoJsonPointSchema,
  GeoJsonMultiPointSchema,
  GeoJsonLineStringSchema,
  GeoJsonMultiLineStringSchema,
  GeoJsonPolygonSchema,
  GeoJsonMultiPolygonSchema,
]);
export type GeoJsonGeometry = z.infer<typeof GeoJsonGeometrySchema>;

export const GeoJsonFeatureSchema = z.object({
  type: z.literal('Feature'),
  id: z.string(),
  properties: z.record(z.string(), z.any()),
  geometry: GeoJsonGeometrySchema,
});
export type GeoJsonFeature = z.infer<typeof GeoJsonFeatureSchema>;

export const GeoJsonFeatureCollectionSchema = z.object({
  type: z.literal('FeatureCollection'),
  features: z.array(GeoJsonFeatureSchema),
});
export type GeoJsonFeatureCollection = z.infer<typeof GeoJsonFeatureCollectionSchema>;

// 3. Section Schemas

export const SummarySchema = z.object({
  headline: z.string(),
  verdict: VerdictSchema,
  confidence_band: ConfidenceBandSchema,
  confidence_reason: z.string(),
  action: z.string(),
});
export type Summary = z.infer<typeof SummarySchema>;

export const ClaimSchema = z.object({
  id: z.string(),
  text: z.string(),
  kind: ClaimKindSchema,
  evidence_ids: z.array(z.string()),
  citation_ids: z.array(z.string()),
});
export type Claim = z.infer<typeof ClaimSchema>;

export const MapLayerSchema = z.object({
  id: z.string(),
  type: MapLayerTypeSchema,
  label: z.string(),
  visible_by_default: z.boolean(),
  feature_collection: GeoJsonFeatureCollectionSchema,
});
export type MapLayer = z.infer<typeof MapLayerSchema>;

export const MapViewportSchema = z.object({
  center: PositionSchema, // [longitude, latitude]
  zoom: z.number().min(1).max(20),
});
export type MapViewport = z.infer<typeof MapViewportSchema>;

export const MapConfigSchema = z.object({
  viewport: MapViewportSchema,
  layers: z.array(MapLayerSchema),
});
export type MapConfig = z.infer<typeof MapConfigSchema>;

export const RuleTraceItemSchema = z.object({
  id: z.string(),
  rule_id: z.string(),
  rule_name: z.string(),
  domain: z.string(),
  measured_value: z.union([z.string(), z.number()]),
  threshold_value: z.union([z.string(), z.number()]),
  comparator: z.string(), // e.g. ">", "<=", "inside", "outside"
  unit: z.string(),
  passed: z.boolean(),
  severity: RuleSeveritySchema,
  threshold_version: z.string(),
  explanation: z.string(),
});
export type RuleTraceItem = z.infer<typeof RuleTraceItemSchema>;

export const DataFreshnessItemSchema = z.object({
  domain: z.string(),
  source_name: z.string(),
  observed_at: z.string(),
  retrieved_at: z.string(),
  valid_to: z.string().optional(),
  age_minutes: z.number().nonnegative(),
  status: FreshnessStatusSchema,
});
export type DataFreshnessItem = z.infer<typeof DataFreshnessItemSchema>;

export const MissingInputItemSchema = z.object({
  domain: z.string(),
  parameter: z.string(),
  impact: z.string(),
  fallback_used: z.string().optional(),
});
export type MissingInputItem = z.infer<typeof MissingInputItemSchema>;

export const EvidencePanelSchema = z.object({
  rule_trace: z.array(RuleTraceItemSchema),
  data_freshness: z.array(DataFreshnessItemSchema),
  missing_inputs: z.array(MissingInputItemSchema),
});
export type EvidencePanel = z.infer<typeof EvidencePanelSchema>;

export const CitationSchema = z.object({
  id: z.string(),
  title: z.string(),
  publisher: z.string(),
  url: z.string(),
  published_at: z.string(),
  accessed_at: z.string(),
  excerpt: z.string(),
  source_language: z.string().optional(), // e.g. "hi-IN", "mr-IN", "ml-IN"
});
export type Citation = z.infer<typeof CitationSchema>;

export const NoticeSchema = z.object({
  id: z.string(),
  type: NoticeTypeSchema,
  message: z.string(),
});
export type Notice = z.infer<typeof NoticeSchema>;

export const DegradationInfoSchema = z.object({
  is_degraded: z.boolean(),
  reason: z.string(),
  missing_domains: z.array(z.string()),
  fallback_applied: z.string().optional(),
});
export type DegradationInfo = z.infer<typeof DegradationInfoSchema>;

// 4. Canonical UserResponseV1 Top-Level Schema
export const UserResponseV1Schema = z.object({
  schema_version: z.literal('1.0'),
  query_run_id: z.string(),
  session_id: z.string().optional(),
  generated_at: z.string(),
  decision_status: DecisionStatusSchema,
  summary: SummarySchema,
  claims: z.array(ClaimSchema),
  map: MapConfigSchema,
  evidence_panel: EvidencePanelSchema,
  citations: z.array(CitationSchema),
  notices: z.array(NoticeSchema).default([]),
  degradation: DegradationInfoSchema.nullable().optional(),
});
export type UserResponseV1 = z.infer<typeof UserResponseV1Schema>;
