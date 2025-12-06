/**
 * RESA Power - Supabase Client
 * 
 * Drop-in replacement for dataverse.ts
 * Copy to: C:\Users\jjswe\Projects\resa-web-app\lib\supabase.ts
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// ============================================================================
// CLIENTS
// ============================================================================

export async function getClients() {
  const { data, error } = await supabase
    .from('clients')
    .select('*')
    .eq('is_active', true)
    .order('name')
  
  if (error) throw error
  return data
}

export async function getClient(id: string) {
  const { data, error } = await supabase
    .from('clients')
    .select(`*, sites(*), contacts(*)`)
    .eq('id', id)
    .single()
  
  if (error) throw error
  return data
}

export async function createClient(client: {
  name: string
  code?: string
  address?: string
  city?: string
  state?: string
  zip?: string
  phone?: string
  email?: string
}) {
  const { data, error } = await supabase
    .from('clients')
    .insert(client)
    .select()
    .single()
  
  if (error) throw error
  return data
}

// ============================================================================
// PROJECTS
// ============================================================================

export async function getProjects(options?: {
  status?: string
  clientId?: string
  projectType?: string
  limit?: number
}) {
  let query = supabase
    .from('projects')
    .select(`
      *,
      clients(id, name, code),
      sites(id, name),
      locations(id, name)
    `)
    .order('created_at', { ascending: false })
  
  if (options?.status) query = query.eq('status', options.status)
  if (options?.clientId) query = query.eq('client_id', options.clientId)
  if (options?.projectType) query = query.eq('project_type', options.projectType)
  if (options?.limit) query = query.limit(options.limit)
  
  const { data, error } = await query
  if (error) throw error
  return data
}

export async function getProject(id: string) {
  const { data, error } = await supabase
    .from('projects')
    .select(`
      *,
      clients(id, name, code),
      sites(id, name, address, city, state),
      locations(id, name),
      scopes(*, scope_labor_details(*), tasks(*), apparatus(*)),
      pss_studies(*, engineers(id, company_name), pss_documents(*), rfis(*))
    `)
    .eq('id', id)
    .single()
  
  if (error) throw error
  return data
}

export async function createProject(project: {
  project_number: string
  name: string
  client_id: string
  site_id?: string
  project_type: string
  status?: string
  po_number?: string
  contract_value?: number
}) {
  const { data, error } = await supabase
    .from('projects')
    .insert(project)
    .select()
    .single()
  
  if (error) throw error
  return data
}

// ============================================================================
// DASHBOARD VIEWS (Pre-built aggregations)
// ============================================================================

export async function getProjectDashboard() {
  const { data, error } = await supabase
    .from('v_project_dashboard')
    .select('*')
    .order('created_at', { ascending: false })
  
  if (error) throw error
  return data
}

export async function getPssDashboard() {
  const { data, error } = await supabase
    .from('v_pss_dashboard')
    .select('*')
    .order('created_at', { ascending: false })
  
  if (error) throw error
  return data
}

export async function getOutstandingDocuments() {
  const { data, error } = await supabase
    .from('v_outstanding_documents')
    .select('*')
    .order('days_outstanding', { ascending: false })
  
  if (error) throw error
  return data
}

export async function getRevenueRecognition(projectId?: string) {
  let query = supabase
    .from('v_revenue_recognition')
    .select('*')
    .order('created_at', { ascending: false })
  
  if (projectId) query = query.eq('project_id', projectId)
  
  const { data, error } = await query
  if (error) throw error
  return data
}

// ============================================================================
// SCOPES & APPARATUS
// ============================================================================

export async function getScopes(projectId: string) {
  const { data, error } = await supabase
    .from('scopes')
    .select(`*, scope_labor_details(*)`)
    .eq('project_id', projectId)
    .order('scope_number')
  
  if (error) throw error
  return data
}

export async function getApparatus(scopeId: string) {
  const { data, error } = await supabase
    .from('apparatus')
    .select(`*, apparatus_type_master(name, category), apparatus_revenue(*)`)
    .eq('scope_id', scopeId)
    .order('sequence')
  
  if (error) throw error
  return data
}

export async function markApparatusComplete(id: string, options?: { 
  delay_hours?: number 
  result?: string
}) {
  const { data, error } = await supabase
    .from('apparatus')
    .update({
      completion_status: 'COMPLETE',
      status: 'COMPLETED',
      date_completed: new Date().toISOString().split('T')[0],
      delay_hours: options?.delay_hours || 0,
      result: options?.result
    })
    .eq('id', id)
    .select()
    .single()
  
  if (error) throw error
  // Trigger automatically creates apparatus_revenue record!
  return data
}

// ============================================================================
// PSS PORTAL
// ============================================================================

export async function getPssStudy(projectId: string) {
  const { data, error } = await supabase
    .from('pss_studies')
    .select(`
      *,
      projects(id, project_number, name, clients(name)),
      engineers(id, company_name, email),
      pss_documents(*, document_templates(name)),
      rfis(*)
    `)
    .eq('project_id', projectId)
    .single()
  
  if (error) throw error
  return data
}

export async function updatePssStatus(id: string, status: string) {
  const { data, error } = await supabase
    .from('pss_studies')
    .update({ pss_status: status })
    .eq('id', id)
    .select()
    .single()
  
  if (error) throw error
  return data
}

export async function updateDocumentStatus(id: string, status: string, rejection_reason?: string) {
  const update: any = { status }
  
  if (status === 'REQUESTED') update.requested_date = new Date().toISOString().split('T')[0]
  if (status === 'RECEIVED') update.received_date = new Date().toISOString().split('T')[0]
  if (status === 'REJECTED') {
    update.rejection_reason = rejection_reason
    update.reviewed_date = new Date().toISOString().split('T')[0]
  }
  if (status === 'ACCEPTED') update.reviewed_date = new Date().toISOString().split('T')[0]
  
  const { data, error } = await supabase
    .from('pss_documents')
    .update(update)
    .eq('id', id)
    .select()
    .single()
  
  if (error) throw error
  return data
}

// ============================================================================
// LOOKUP TABLES
// ============================================================================

export async function getApparatusTypes() {
  const { data, error } = await supabase
    .from('apparatus_type_master')
    .select('*')
    .eq('is_active', true)
    .order('sort_order')
  
  if (error) throw error
  return data
}

export async function getBusinessUnits() {
  const { data, error } = await supabase
    .from('business_units')
    .select('*')
    .eq('is_active', true)
    .order('sort_order')
  
  if (error) throw error
  return data
}

export async function getDocumentTemplates(studyType?: string) {
  let query = supabase
    .from('document_templates')
    .select('*')
    .eq('is_active', true)
    .order('sort_order')
  
  if (studyType) query = query.contains('study_types', [studyType])
  
  const { data, error } = await query
  if (error) throw error
  return data
}

export async function getEngineers() {
  const { data, error } = await supabase
    .from('engineers')
    .select('*')
    .eq('is_active', true)
    .order('company_name')
  
  if (error) throw error
  return data
}

// ============================================================================
// AUTH
// ============================================================================

export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) throw error
  return data
}

export async function signOut() {
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

export async function getCurrentUser() {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

export function onAuthStateChange(callback: (event: string, session: any) => void) {
  return supabase.auth.onAuthStateChange(callback)
}

