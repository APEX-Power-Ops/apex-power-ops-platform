# Apex Power Ops - System Overview


**Version:** 2.2.0 (Supabase)  
**Last Updated:** December 11, 2025  
**Project Lead:** Jason Swenson  
**Repository:** [github.com/jasonlswenson-sys/apex-power-ops](https://github.com/jasonlswenson-sys/apex-power-ops)


---


## 🎯 Executive Summary


Modern PostgreSQL/Supabase-based operations platform for electrical testing projects with NETA-aligned workflow support. **Migrated from Dataverse to Supabase in December 2025** for improved flexibility, lower cost, and better developer experience.


**Platform:**
- **Database**: Supabase (PostgreSQL) - `resa-power-db`
- **Web App**: Next.js 16 + React 19 + shadcn/ui
- **API**: Supabase REST + Real-time subscriptions
- **Auth**: Supabase Auth (planned)


**System Scale (v2.2.0):**
- **30 Tables**: Core + Financial + PSS + Reference + NETA/Resources
- **38+ ENUM Types**: Type-safe status values
- **12 Trigger Functions**: Automated rollups and workflows
- **15+ Views**: Dashboard and reporting aggregations
- **~50 Indexes**: Performance optimization
- **33 NETA Procedures**: ATS-2025 imported


---


## 📊 Platform Architecture


```mermaid
graph TB
    subgraph "User Interfaces"
        WEB[🖥️ Next.js Web App<br/>Desktop/Tablet]
        MOBILE[📱 Mobile PWA<br/>Field Tech - Future]
        V0[🎨 v0.dev Prototypes<br/>5 Role Demos]
    end
    
    subgraph "Supabase Platform"
        API[🔌 REST API<br/>Auto-generated]
        RT[⚡ Real-time<br/>Subscriptions]
        AUTH[🔐 Supabase Auth<br/>Planned]
        STORAGE[📁 File Storage<br/>Planned]
