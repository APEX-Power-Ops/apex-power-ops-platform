# RESA Platform: Blue-Sky Architecture
## The Ideal Build With No Limitations
### December 26, 2025

---

## 🎯 THE VISION

**"One source for all operations-based documentation. SharePoint-style hub with project tracking. Offline-essential for field techs."**

This document presents the ideal architecture if we had unlimited time, budget, and resources. Then we'll identify what's actually achievable and in what order.

---

## 🏗️ THE IDEAL ARCHITECTURE

### Core Platform: Supabase (Keep What You Have)

You've already built the foundation correctly. The 40-table schema is production-ready.

| Component | Status | Notes |
|-----------|--------|-------|
| PostgreSQL Database | ✅ Built | 40 tables, enterprise-grade |
| Row Level Security | ✅ Ready | Policies defined |
| Edge Functions | ✅ Available | For custom logic |
| Realtime | ✅ Available | For collaboration |
| Storage | ✅ Available | For documents |
| Auth | ⚠️ Needs setup | 8 hours to implement |

**Decision: Keep Supabase as the backend. Don't change this.**

---

## 🔌 THE GAME-CHANGING INTEGRATIONS

### 1. PowerSync - Offline-First Solved ⭐⭐⭐⭐⭐

**This is the single most important integration.**

| Feature | Benefit |
|---------|---------|
| Drop-in sync layer | No custom sync engine needed |
| Works with existing Supabase | No schema changes |
| SQLite on device | True offline, not just caching |
| React Native SDK | Native mobile app support |
| Sync Rules | Control what data goes to whom |
| Conflict resolution | Built-in |
| Free tier available | Start without cost |

**Why PowerSync over building custom:**

| Custom Build | PowerSync |
|--------------|-----------|
| 100+ hours development | 8-16 hours integration |
| Custom conflict resolution | Built-in |
| Maintenance burden | Managed service |
| Untested edge cases | Production-proven |
| WatermelonDB learning curve | SQLite (familiar) |

**PowerSync was built by JourneyApps for industrial field apps** - literally the same use case as RESA. Technicians in the field, offline areas, syncing when connected.

```
Architecture with PowerSync:

┌─────────────────────────────────────────────────────────┐
│                    SUPABASE                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Postgres │  │  Auth    │  │ Storage  │             │
│  │ 40 tables│  │          │  │ Documents│             │
│  └────┬─────┘  └──────────┘  └──────────┘             │
│       │                                                │
│       │ WAL (Write-Ahead Log)                         │
└───────┼───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────┐
│    POWERSYNC      │
│  ┌─────────────┐  │
│  │ Sync Rules  │  │  ← "Sync this user's assigned apparatus"
│  │ Change Log  │  │
│  │ Bucket Mgmt │  │
│  └─────────────┘  │
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Field  │ │ Field  │
│ Tech 1 │ │ Tech 2 │
│ SQLite │ │ SQLite │
│ Local  │ │ Local  │
└────────┘ └────────┘
```

**Cost:** Free tier for development, ~$50-200/month for production

---

### 2. React-admin + ra-supabase - PM Dashboard in Days ⭐⭐⭐⭐⭐

**Instead of building Next.js dashboard from scratch:**

| Custom Next.js Build | React-admin |
|---------------------|-------------|
| 80+ hours for CRUD | 8-16 hours |
| Build each screen | Auto-generate from tables |
| Custom data fetching | Built-in data provider |
| Build filters/sorting | Built-in |
| Build pagination | Built-in |
| Build forms | Built-in |

**ra-supabase features:**
- Auto-generates admin views from Supabase tables
- Built-in authentication with Supabase Auth
- Real-time updates with Supabase Realtime
- RLS-aware data provider
- OpenAPI schema guesser

```javascript
// This is ALL you need for a working admin:
import { Admin, Resource } from 'react-admin';
import { 
  supabaseDataProvider,
  supabaseAuthProvider,
  ListGuesser,
  EditGuesser
} from 'ra-supabase';

const App = () => (
  <Admin 
    dataProvider={supabaseDataProvider(supabaseClient)}
    authProvider={supabaseAuthProvider(supabaseClient)}
  >
    <Resource name="projects" list={ListGuesser} edit={EditGuesser} />
    <Resource name="apparatus" list={ListGuesser} edit={EditGuesser} />
    <Resource name="employees" list={ListGuesser} edit={EditGuesser} />
  </Admin>
);
```

**This gets you a working PM dashboard in HOURS.**

Then customize individual views as needed.

---

### 3. Algolia - Real Search ⭐⭐⭐⭐

For "SharePoint-style" document hub, you need real search.

| Postgres Full-Text | Algolia |
|--------------------|---------|
| Good enough | Instant |
| Basic relevance | AI-powered ranking |
| Manual indexing | Automatic |
| No typo tolerance | Typo-tolerant |
| No faceting | Rich faceting |

**Use case:** Tech searches "transformer oil DGA" and instantly finds:
- Study guides
- SOPs
- NETA procedures
- Past test reports
- Equipment datasheets

**Cost:** Free tier (10K searches/month), then ~$1/1000 searches

**Alternative if cost-sensitive:** Stick with Postgres `pg_trgm` + `tsvector` - good enough for MVP.

---

### 4. OneSignal - Push Notifications ⭐⭐⭐⭐

Field techs need notifications:
- New assignment
- Schedule change
- Urgent task
- Document shared
- Sync complete

| Feature | Benefit |
|---------|---------|
| Push (iOS/Android) | Works even when app closed |
| Web push | Desktop notifications |
| Email fallback | Reaches everyone |
| Segments | Notify by role/location |
| Templates | Consistent messaging |

**Cost:** Free tier generous, then usage-based

---

### 5. Trigger.dev or n8n - Background Jobs ⭐⭐⭐

For scheduled/async work:
- PowerDB sync (scheduled SQL read)
- Report generation
- Email digests
- Data cleanup
- Study content migration

| Trigger.dev | n8n |
|-------------|-----|
| Code-first | Visual builder |
| Serverless | Self-hosted option |
| No timeouts | No timeouts |
| TypeScript | Any language |

**Recommendation:** Trigger.dev for code-heavy tasks, n8n for visual workflow building.

**Cost:** Trigger.dev free tier, n8n self-hosted free

---

### 6. Resend - Transactional Email ⭐⭐⭐

- Password resets
- Assignment notifications
- Report delivery
- Weekly digests

**Why Resend over SendGrid/Mailgun:**
- Developer-focused
- React email templates
- Better deliverability
- Simpler pricing

**Cost:** 3000 emails/month free, then $20/month for 50K

---

### 7. Supabase Storage - Document Hub ⭐⭐⭐⭐

Already included with Supabase. For the SharePoint-style hub:
- Store documents, photos, reports
- CDN-delivered
- RLS for access control
- Presigned URLs for sharing

**Schema addition needed:**
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    folder_path TEXT,           -- '/Arizona/LASNAP16/Reports'
    filename TEXT,
    file_type TEXT,
    storage_path TEXT,          -- Supabase Storage path
    apparatus_type_id UUID,     -- Link to equipment
    project_id UUID,            -- Link to project
    uploaded_by UUID,
    uploaded_at TIMESTAMPTZ,
    tags TEXT[],
    search_vector TSVECTOR      -- Full-text search
);
```

---

## 📱 THE APPLICATION ARCHITECTURE

### Three Frontends, One Backend

```
┌─────────────────────────────────────────────────────────────┐
│                         USERS                                │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Field Techs   │   Project Mgrs  │   Admins/Executives     │
│   (Mobile)      │   (Web)         │   (Web)                 │
└────────┬────────┴────────┬────────┴────────┬────────────────┘
         │                 │                  │
         ▼                 ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│ React Native    │ │ Next.js         │ │ React-admin         │
│ + Expo          │ │ Dashboard       │ │ Admin Panel         │
│ + PowerSync     │ │                 │ │ + ra-supabase       │
│                 │ │                 │ │                     │
│ OFFLINE-FIRST   │ │ ONLINE          │ │ ONLINE              │
└────────┬────────┘ └────────┬────────┘ └────────┬────────────┘
         │                   │                    │
         └───────────────────┼────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       SUPABASE                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Postgres │ │   Auth   │ │ Storage  │ │ Realtime │       │
│  │          │ │          │ │          │ │          │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 FIELD TECH APP (React Native + Expo + PowerSync)

### Core Screens

1. **My Assignments**
   - Today's tasks
   - Assigned apparatus
   - Status indicators
   - Offline indicator

2. **Apparatus Detail**
   - Equipment info
   - Linked procedures (from apparatus_type_resources)
   - Test checklist
   - Mark complete
   - Enter hours

3. **Document Library**
   - Browse by category
   - Search
   - Offline-available docs
   - Download for offline

4. **Study Content**
   - NETA guides (migrated)
   - Practice questions
   - Progress tracking

5. **Time Entry**
   - Clock in/out
   - Allocate to apparatus
   - Submit for approval

### Offline Capabilities

| Feature | Offline? | Notes |
|---------|----------|-------|
| View assignments | ✅ | Synced via PowerSync |
| View procedures | ✅ | Pre-downloaded |
| Mark complete | ✅ | Queued for sync |
| Enter hours | ✅ | Queued for sync |
| Take photos | ✅ | Stored locally, synced later |
| View study content | ✅ | Pre-downloaded |
| Search documents | ⚠️ | Local search only |
| Real-time updates | ❌ | Requires connection |

---

## 🖥️ PM DASHBOARD (Next.js)

### Core Features

1. **Project Overview**
   - All projects with status
   - Financial summary
   - Resource allocation
   - Timeline view

2. **Project Detail**
   - Scopes breakdown
   - Apparatus list with status
   - Tech assignments
   - Hours tracking
   - Documents

3. **Team Management**
   - Tech availability
   - Assignments
   - Utilization metrics
   - Skills matrix

4. **Reports**
   - Project status
   - Financial summary
   - Test completion
   - Export to PDF/Excel

### Real-time Features
- Live status updates
- Collaborative editing
- Notification feed

---

## ⚙️ ADMIN PANEL (React-admin)

### Auto-Generated CRUD

- Projects
- Scopes
- Apparatus
- Employees
- Locations
- Equipment
- NETA Procedures
- Study Content
- Documents

### Admin-Specific Features

- User management
- Role assignment
- System configuration
- Audit logs
- Data import/export

---

## 🔄 INTEGRATIONS ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│   PowerDB       │   Connecteam    │   QuickBooks (Future)   │
│   (SQL Server)  │   (Scheduling)  │   (Accounting)          │
└────────┬────────┴────────┬────────┴────────┬────────────────┘
         │                 │                  │
         ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    TRIGGER.DEV / N8N                         │
│           (Background Jobs & Integration Layer)              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PowerDB Sync │  │ Report Gen   │  │ Notifications│      │
│  │ (Scheduled)  │  │ (On-demand)  │  │ (Event)     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                       SUPABASE                               │
└─────────────────────────────────────────────────────────────┘
```

### PowerDB Sync Strategy

```
Phase 1: Read-Only Sync (Now)
- Scheduled job reads PowerDB via SQL
- Inserts/updates projects, scopes, apparatus
- RESA is read-only consumer
- PowerDB remains source of truth

Phase 2: Bidirectional (Future)
- RESA writes back to PowerDB
- Conflict resolution rules
- Eventually RESA becomes primary
```

---

## 💰 COST ANALYSIS

### Monthly Costs (Production)

| Service | Free Tier | Production Est. |
|---------|-----------|-----------------|
| Supabase Pro | $25/mo | $25-50/mo |
| PowerSync | Free (dev) | $50-100/mo |
| Algolia | 10K free | $0-50/mo |
| OneSignal | Free | $0-25/mo |
| Trigger.dev | Free tier | $0-25/mo |
| Resend | 3K free | $0-20/mo |
| Vercel | Free tier | $0-20/mo |

**Total:** $75-290/month for full production system

**Compare to:** Building custom offline sync, notification system, job queue = 200+ developer hours = $20,000+ opportunity cost

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-2)
- [ ] Implement Supabase Auth
- [ ] Set up React-admin with ra-supabase
- [ ] Deploy basic PM dashboard
- [ ] Create document storage structure

**Deliverable:** Working admin panel, PM can browse data

### Phase 2: Document Hub (Weeks 3-4)
- [ ] Document upload/management UI
- [ ] Folder structure implementation
- [ ] Basic search (Postgres)
- [ ] Link documents to apparatus types

**Deliverable:** SharePoint-style document hub

### Phase 3: PowerSync Integration (Weeks 5-6)
- [ ] Set up PowerSync service
- [ ] Define sync rules
- [ ] Create React Native app shell
- [ ] Integrate PowerSync SDK

**Deliverable:** Mobile app syncing data

### Phase 4: Field Tech MVP (Weeks 7-10)
- [ ] My Assignments screen
- [ ] Apparatus detail with procedures
- [ ] Mark complete workflow
- [ ] Time entry
- [ ] Offline document viewer

**Deliverable:** Field techs can work offline

### Phase 5: Polish & Integrate (Weeks 11-14)
- [ ] PowerDB sync job
- [ ] Push notifications (OneSignal)
- [ ] Report generation
- [ ] Study content migration
- [ ] Performance optimization

**Deliverable:** Production-ready system

### Phase 6: Advanced Features (Months 4-6)
- [ ] Algolia search upgrade
- [ ] Client portal
- [ ] Advanced analytics
- [ ] TCC Calculator integration
- [ ] Scheduling module (replace Connecteam)

---

## 🎯 WHY THIS ARCHITECTURE

### Principles Applied

1. **Use Proven Tools** - PowerSync, React-admin are battle-tested
2. **Minimize Custom Code** - Every line you write is a line you maintain
3. **Offline-First by Design** - Not an afterthought
4. **Progressive Enhancement** - Start simple, add complexity
5. **Single Source of Truth** - Supabase Postgres is THE database

### What We're NOT Building

| Don't Build | Use Instead |
|-------------|-------------|
| Custom sync engine | PowerSync |
| Admin CRUD from scratch | React-admin |
| Custom search | Algolia (or Postgres) |
| Custom notifications | OneSignal |
| Custom job queue | Trigger.dev |
| Custom email service | Resend |

### Technical Debt Avoided

- No custom conflict resolution logic
- No custom offline detection
- No custom queue management
- No custom admin scaffolding
- No custom notification infrastructure

---

## 📊 SUCCESS METRICS

### Phase 1-2 Success
- PM can login and view all projects
- Documents uploadable and findable
- Data visible without SQL

### Phase 3-4 Success
- Field tech can work with no internet
- Data syncs when connected
- Procedures accessible offline

### Phase 5-6 Success
- PowerDB data flows automatically
- Notifications working
- Reports generated automatically

### Long-Term Success
- 40% admin overhead reduction
- Zero "can't work, no internet" complaints
- Single source for all documentation
- Field techs prefer RESA over paper

---

## ❓ DECISIONS NEEDED

### Immediate
1. **PowerSync vs. custom** - Recommend PowerSync strongly
2. **React-admin vs. custom Next.js** - Recommend React-admin for admin, custom for PM-facing
3. **Algolia vs. Postgres search** - Recommend Postgres for MVP, upgrade later

### Near-Term
4. **React Native vs. Flutter** - React Native (PowerSync has SDK, team knows React)
5. **App Store vs. internal distribution** - Start internal (TestFlight/Firebase), App Store later
6. **Single app vs. role-based apps** - Single app with role-based UI

### Long-Term
7. **Replace PowerDB entirely?** - Eventually, but sync for now
8. **Client portal priority?** - After internal tools stable
9. **Native iOS/Android vs. React Native** - React Native sufficient

---

## 🏁 BOTTOM LINE

**The ideal RESA platform uses:**

| Layer | Technology | Why |
|-------|------------|-----|
| Database | Supabase Postgres | Already built, excellent |
| Auth | Supabase Auth | Built-in, RLS-integrated |
| Storage | Supabase Storage | Built-in, CDN |
| Offline Sync | **PowerSync** | Drop-in, proven, perfect fit |
| Admin Panel | **React-admin** | Days not months |
| PM Dashboard | Next.js + shadcn | Custom UX needed |
| Field Tech App | React Native + Expo | Cross-platform, PowerSync SDK |
| Search | Postgres → Algolia | Start simple, upgrade later |
| Notifications | OneSignal | Push + email |
| Background Jobs | Trigger.dev | Serverless, no timeouts |
| Email | Resend | Modern, reliable |

**Total build time with this stack:** 10-14 weeks to production
**Total build time building everything custom:** 6-12 months

**The key insight:** PowerSync solves the hardest problem (offline sync) completely. React-admin solves the second hardest problem (admin UI) almost completely. Everything else is integration work, not invention.

---

*Created: December 26, 2025*
*Blue-sky architecture with practical implementation path*
