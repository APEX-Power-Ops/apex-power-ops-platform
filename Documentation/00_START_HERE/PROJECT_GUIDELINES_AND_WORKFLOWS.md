# RESA Power Project - Unified Guidelines & Workflows

**Document Version**: 1.0  
**Last Updated**: November 15, 2025  
**Status**: Active Development Standard

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Git Workflow & Branch Strategy](#git-workflow--branch-strategy)
4. [Commit Message Standards](#commit-message-standards)
5. [Pull Request Process](#pull-request-process)
6. [Power Platform Development Guidelines](#power-platform-development-guidelines)
7. [MCP Server Development](#mcp-server-development)
8. [Code Review Standards](#code-review-standards)
9. [Testing & Validation](#testing--validation)
10. [Deployment Procedures](#deployment-procedures)
11. [Documentation Requirements](#documentation-requirements)
12. [Security & Credentials Management](#security--credentials-management)

---

## Project Overview

### Mission Statement
Modernize RESA Power's electrical testing project management through Power Platform integration with NETA standards compliance, automated validation, and AI-assisted development workflows.

### Key Components
- **Power Platform Solution**: Dataverse-based project tracking (v1.2.0.3)
- **MCP Ecosystem**: 8 AI automation servers
- **PostgreSQL Integration**: TCC v5.0 database bridge
- **Azure Infrastructure**: Service principal authentication
- **Git/GitHub**: Version control and collaboration

### Team Structure
- **Primary Developer**: Jason Swenson (jason.swenson@resapower.com)
- **Development Environment**: org04ad071f.crm.dynamics.com
- **Repository**: https://github.com/jasonlswenson-sys/RESA-Power-Project-Tracker

---

## Development Environment Setup

### Required Tools
```powershell
# Check installations
node --version          # Node.js (v18+ recommended)
npm --version          # npm package manager
git --version          # Git for Windows
psql --version         # PostgreSQL client (optional)
```

### Environment Configuration

**1. Clone Repository**
```powershell
git clone https://github.com/jasonlswenson-sys/RESA-Power-Project-Tracker.git
cd RESA-Power-Project-Tracker
```

**2. MCP Server Setup**
```powershell
# Install dependencies for custom servers
cd MCP_Servers/resa-dataverse-mcp
npm install

cd ../resa-validation-mcp
npm install

cd ../resa-email-mcp
npm install
```

**3. Environment Variables**
Create `.env` files in each MCP server directory (never commit these):
```env
# Example: resa-dataverse-mcp/.env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
DATAVERSE_URL=https://your-org.crm.dynamics.com
```

**4. Claude Desktop Configuration**
Configure MCP servers in `%APPDATA%\Claude\claude_desktop_config.json` (see README.md for current configuration)

### Workspace Structure
```
C:\RESA_Power_Build\
├── Documentation/           # All project documentation
│   ├── 00_START_HERE/      # Quick start guides (YOU ARE HERE)
│   ├── 01_Architecture/    # Technical specifications
│   ├── 02_Build_Guides/    # Implementation guides
│   └── 06_MCP_Automation/  # MCP server documentation
├── MCP_Servers/            # Custom AI automation servers
├── Solution_Exports/       # Power Platform solution exports
├── Scripts/                # PowerShell and automation scripts
├── CSV_Templates/          # Data import templates
└── Working/                # Development workspace
```

---

## Git Workflow & Branch Strategy

### Branch Structure

#### **Main Branches**

**`main`**
- Production-ready code only
- Always deployable to production Dataverse environment
- Protected: requires pull request for changes
- Tagged for releases (e.g., `v1.2.0.3`)

**`dev`** (Future - when team expands)
- Integration branch for testing multiple features
- Merges to `main` after full testing
- Optional for solo development

#### **Supporting Branches**

**Feature Branches**: `feature/description`
```powershell
# Example: Adding new billing automation
git checkout -b feature/billing-automation
```

**Use Cases:**
- New Power Platform components (tables, flows, apps)
- New MCP server capabilities
- Documentation improvements
- Script enhancements

**Naming Convention:**
- `feature/add-email-validation`
- `feature/neta-compliance-checker`
- `feature/project-status-dashboard`

---

**Bugfix Branches**: `bugfix/description`
```powershell
# Example: Fixing rollup calculation
git checkout -b bugfix/project-rollup-calculation
```

**Use Cases:**
- Fixing defects in current release
- Data validation corrections
- UI/UX improvements

**Naming Convention:**
- `bugfix/asset-hierarchy-display`
- `bugfix/billing-status-filter`
- `bugfix/csv-import-validation`

---

**Hotfix Branches**: `hotfix/description`
```powershell
# Example: Critical production issue
git checkout -b hotfix/dataverse-connection-timeout
```

**Use Cases:**
- Emergency production fixes
- Critical security patches
- Data integrity issues

**Process:**
1. Branch from `main`
2. Fix and test immediately
3. Merge to `main` via expedited PR
4. Tag new version
5. Document in changelog

---

**MCP Server Branches**: `mcp/server-name/feature`
```powershell
# Example: Updating validation server
git checkout -b mcp/validation/add-neta-checks
```

**Use Cases:**
- MCP server enhancements
- New tool implementations
- API integrations

---

**Documentation Branches**: `docs/topic`
```powershell
# Example: Updating architecture docs
git checkout -b docs/update-api-reference
```

---

### Branch Lifecycle

#### 1. **Create Branch**
```powershell
# Always branch from main for new work
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

#### 2. **Develop & Commit**
```powershell
# Make changes
git add .
git commit -m "type: description"

# Push to GitHub regularly
git push origin feature/your-feature-name
```

#### 3. **Keep Updated**
```powershell
# Regularly sync with main
git checkout main
git pull origin main
git checkout feature/your-feature-name
git merge main
```

#### 4. **Create Pull Request**
- Go to GitHub repository
- Click "New Pull Request"
- Select your branch
- Fill out PR template (see below)
- Request review (if team exists)

#### 5. **Merge & Cleanup**
```powershell
# After PR is approved and merged
git checkout main
git pull origin main
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

---

## Commit Message Standards

### Format
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

### Types

- **feat**: New feature
  - `feat: Add automated billing status calculator`
  
- **fix**: Bug fix
  - `fix: Correct project hierarchy rollup logic`
  
- **docs**: Documentation only
  - `docs: Update MCP server configuration guide`
  
- **style**: Code formatting (no logic change)
  - `style: Format JavaScript according to ESLint`
  
- **refactor**: Code restructuring (no feature change)
  - `refactor: Simplify Dataverse query logic`
  
- **test**: Adding or updating tests
  - `test: Add validation tests for NETA standards`
  
- **chore**: Maintenance tasks
  - `chore: Update npm dependencies`
  
- **mcp**: MCP server changes
  - `mcp: Add email notification tool to validation server`
  
- **solution**: Power Platform solution changes
  - `solution: Export v1.2.0.4 with new billing fields`

### Examples

**Good Commits:**
```
feat: Add NETA standards compliance checker to validation MCP

Implements IEEE/ANSI standards validation for equipment testing.
Includes checks for:
- Voltage rating verification
- Test sequence validation
- Documentation completeness

Closes #42
```

```
fix: Resolve asset hierarchy parent lookup issue

Assets were not correctly linking to parent projects due to
GUID formatting mismatch in CSV import process.

Modified: Scripts/Import-AssetData.ps1
Impact: Existing data requires re-import
```

**Bad Commits:**
```
update stuff           # Too vague
fixed bug             # What bug? Where?
WIP                   # Work in progress - don't commit
asdfasdf             # Meaningless
```

### Commit Best Practices

1. **Commit Early, Commit Often** - Small, logical chunks
2. **One Concern Per Commit** - Don't mix features with fixes
3. **Write Clear Messages** - Future you will thank you
4. **Reference Issues** - Link to GitHub issues when applicable
5. **Avoid Sensitive Data** - Never commit passwords, tokens, or keys

---

## Pull Request Process

### PR Template

When creating a pull request on GitHub, include:

```markdown
## Description
Brief summary of changes

## Type of Change
- [ ] Feature (new functionality)
- [ ] Bug fix (non-breaking fix)
- [ ] Hotfix (critical production fix)
- [ ] Documentation update
- [ ] MCP server enhancement
- [ ] Power Platform solution update

## Changes Made
- Bullet point list of specific changes
- Include file paths when relevant

## Testing Performed
- [ ] Manual testing completed
- [ ] MCP server tools tested
- [ ] Dataverse queries validated
- [ ] Power Platform solution imported and tested
- [ ] No errors in get_errors check

## Impact Assessment
- **Breaking Changes**: Yes/No - Describe if yes
- **Data Migration Required**: Yes/No - Describe if yes
- **Environment Variables Changed**: Yes/No - List if yes
- **Dependencies Updated**: Yes/No - List if yes

## Screenshots (if applicable)
Add screenshots of UI changes or test results

## Checklist
- [ ] Code follows project guidelines
- [ ] Commit messages follow standards
- [ ] Documentation updated
- [ ] .gitignore updated for new secrets
- [ ] Solution exported (if Power Platform changes)
- [ ] MCP server tested in Claude Desktop
- [ ] No console errors or warnings

## Related Issues
Closes #issue_number
```

### Review Criteria

**Code Quality:**
- Follows JavaScript/PowerShell best practices
- Proper error handling
- Clear variable naming
- Comments for complex logic

**Functionality:**
- Solves stated problem
- No unintended side effects
- Works with existing features

**Documentation:**
- README updated if needed
- Inline comments for clarity
- Architecture docs reflect changes

**Security:**
- No hardcoded credentials
- Proper .env usage
- Sensitive data excluded

### Approval Process

1. **Self-Review** - Review your own PR first
2. **Automated Checks** - Ensure no errors
3. **Testing** - Verify in development environment
4. **Merge** - Squash and merge or merge commit (maintain clean history)
5. **Tag Version** - If main branch, tag release

---

## Power Platform Development Guidelines

### Solution Management

#### Versioning
Format: `Major.Minor.Patch.Build`
- **Major**: Breaking changes or major redesign
- **Minor**: New features, backwards compatible
- **Patch**: Bug fixes
- **Build**: Incremental exports during development

Current: `v1.2.0.3`

#### Export Process
```powershell
# 1. Make changes in Dataverse (org04ad071f.crm.dynamics.com)
# 2. Test thoroughly in dev environment
# 3. Export solution (managed and unmanaged)
# 4. Save to Solution_Exports/vX.X.X.X/
# 5. Commit to Git
git add Solution_Exports/v1.2.0.4/
git commit -m "solution: Export v1.2.0.4 with billing enhancements"
git push origin main
```

### Component Standards

#### **Tables (Entities)**
- **Naming**: `resa_` prefix (e.g., `resa_project`, `resa_asset`)
- **Display Names**: Professional, user-friendly
- **Descriptions**: Always include purpose and usage
- **Schema**: Document in `01_Architecture/Entity_Relationship_Diagram.md`

#### **Columns (Fields)**
- **Required Fields**: Mark appropriately
- **Data Types**: Choose most restrictive type
- **Lookups**: Use for relationships, not text
- **Calculated Fields**: Document formula logic

#### **Business Rules**
- **Scope**: Form, All Forms, or Entity
- **Documentation**: Include rule logic in architecture docs
- **Testing**: Verify all conditions and actions

#### **Power Automate Flows**
- **Naming Convention**: `[Trigger] - [Action] - [Entity]`
  - Example: `When Asset Created - Validate Hierarchy - Asset`
- **Error Handling**: Always include try-catch patterns
- **Documentation**: Export flow definitions to `Solution_Exports/`

#### **Canvas Apps**
- **Naming**: User-facing, descriptive
- **Variables**: Document in app settings
- **Data Sources**: Minimize, use Dataverse views
- **Testing**: Test on mobile and desktop

#### **Model-Driven Apps**
- **Site Map**: Logical grouping
- **Forms**: Consistent layout and sections
- **Views**: Default, public, and personal views
- **Dashboards**: Performance-optimized

### Data Quality Standards

#### Import Data Requirements
- **CSV Format**: UTF-8 encoding
- **Headers**: Match Dataverse schema names
- **Validation**: Run through validation MCP before import
- **Backup**: Always backup before bulk operations

#### Validation Checklist
```powershell
# Use validation MCP server in Claude Desktop
# Example prompts:
# "Validate NETA standards compliance for all projects"
# "Check billing readiness for active projects"
# "Verify asset hierarchy integrity"
# "Find data quality issues in test records"
```

---

## MCP Server Development

### Architecture

Each MCP server follows this structure:
```
mcp-server-name/
├── server.js           # Main server logic
├── package.json        # Dependencies
├── .env               # Environment variables (NOT committed)
├── .env.example       # Template for .env
└── README.md          # Server-specific documentation
```

### Server Development Guidelines

#### **Creating New MCP Server**

1. **Setup Structure**
```powershell
cd MCP_Servers
mkdir resa-newfeature-mcp
cd resa-newfeature-mcp
npm init -y
npm install @modelcontextprotocol/sdk dotenv
```

2. **Create server.js Template**
```javascript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';

dotenv.config();

class YourServerName {
  constructor() {
    this.server = new Server(
      {
        name: 'resa-yourserver-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    // Implement tool handlers here
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('RESA YourServer MCP server running on stdio');
  }
}

const server = new YourServerName();
server.run().catch(console.error);
```

3. **Define Tools**
Each tool should:
- Have clear name and description
- Define input schema with validation
- Return structured responses
- Handle errors gracefully

#### **Tool Design Principles**

**Good Tool:**
```javascript
{
  name: 'validate_neta_standards',
  description: 'Validates project equipment against NETA testing standards',
  inputSchema: {
    type: 'object',
    properties: {
      projectId: {
        type: 'string',
        description: 'GUID of the project to validate'
      },
      standardType: {
        type: 'string',
        enum: ['ATS', 'MTS', 'ETT'],
        description: 'Type of NETA standard to apply'
      }
    },
    required: ['projectId']
  }
}
```

**Bad Tool:**
```javascript
{
  name: 'check',  // Too vague
  description: 'checks stuff',  // Not descriptive
  inputSchema: {}  // No validation
}
```

#### **Testing MCP Servers**

1. **Local Testing**
```powershell
cd MCP_Servers/resa-yourserver-mcp
node server.js
# Should output: "RESA YourServer MCP server running on stdio"
# Ctrl+C to stop
```

2. **Claude Desktop Integration**
Add to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "resa-yourserver": {
      "command": "node",
      "args": [
        "C:\\RESA_Power_Build\\MCP_Servers\\resa-yourserver-mcp\\server.js"
      ]
    }
  }
}
```

3. **Restart Claude Desktop** to load server

4. **Test in Claude**
```
"Use the resa-yourserver MCP to [perform action]"
```

#### **MCP Server Best Practices**

- **Error Handling**: Always try-catch async operations
- **Logging**: Use `console.error()` for debugging (stdout is reserved for MCP protocol)
- **Environment Variables**: Never hardcode credentials
- **Documentation**: Include usage examples in README
- **Versioning**: Increment version in package.json for changes
- **Dependencies**: Keep minimal, audit regularly

---

## Code Review Standards

### Self-Review Checklist

Before submitting PR:
- [ ] Code runs without errors
- [ ] All console.log() statements removed (use console.error() for MCP)
- [ ] No TODO comments left in code
- [ ] Variables have meaningful names
- [ ] Functions are single-purpose
- [ ] Comments explain "why", not "what"
- [ ] No hardcoded values (use config/env)
- [ ] Error handling implemented
- [ ] Edge cases considered

### Review Focus Areas

**JavaScript/Node.js:**
- Async/await properly used
- Promises handled correctly
- No callback hell
- Modern ES6+ syntax

**PowerShell:**
- Proper error handling with try-catch
- Progress indicators for long operations
- Help documentation included
- Parameter validation

**Power Platform:**
- Solution components properly configured
- Dependencies documented
- No circular references
- Performance optimized

---

## Testing & Validation

### Testing Levels

#### **1. Unit Testing (MCP Servers)**
Test individual functions:
```javascript
// Example: Test Dataverse query function
async function testDataverseQuery() {
  const result = await queryProjects({ status: 'Active' });
  console.assert(result.length > 0, 'Should return active projects');
}
```

#### **2. Integration Testing (Power Platform)**
- Test flow triggers
- Verify business rules
- Check calculated fields
- Validate lookups

#### **3. End-to-End Testing**
Complete workflows:
1. Create project → Add assets → Run tests → Generate reports
2. Import CSV → Validate data → Sync to Dataverse
3. MCP query → Process data → Send email notification

### Validation Tools

**Use MCP Servers:**
```
# In Claude Desktop
"Use resa-validation MCP to check billing readiness for all projects"
"Use resa-validation MCP to validate hierarchy integrity"
"Use resa-validation MCP to find data quality issues"
```

**Manual Validation:**
- Export and review data in Excel
- Check Power Platform error logs
- Review Dataverse audit history
- Test with real-world scenarios

### Test Data

**Location**: `Import_Data/Test_Data/`

**Guidelines:**
- Use realistic but anonymized data
- Cover edge cases (null values, max lengths, special characters)
- Include both valid and invalid records for validation testing
- Document test scenarios

---

## Deployment Procedures

### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Solution version incremented
- [ ] Change log updated
- [ ] Backup current environment
- [ ] Stakeholders notified

### Deployment Steps

#### **Power Platform Solution Deployment**

1. **Export from Development**
   - Managed solution for production
   - Unmanaged for development environments
   - Include dependencies

2. **Version Control**
```powershell
# Save to Git
git add Solution_Exports/v1.2.0.4/
git commit -m "solution: Release v1.2.0.4"
git tag v1.2.0.4
git push origin main --tags
```

3. **Import to Target Environment**
   - Log into target Dataverse
   - Import managed solution
   - Verify all components
   - Test critical workflows

4. **Post-Deployment Verification**
   - Run validation checks
   - Test user scenarios
   - Monitor for errors
   - Document any issues

#### **MCP Server Deployment**

1. **Update Server**
```powershell
cd MCP_Servers/resa-server-mcp
git pull origin main
npm install
```

2. **Update Configuration**
   - Update .env if needed
   - Verify Claude Desktop config
   - Restart Claude Desktop

3. **Test Tools**
   - Verify each tool responds
   - Check error handling
   - Validate outputs

### Rollback Procedures

**Power Platform:**
1. Import previous managed solution version
2. Restore from backup if needed
3. Document rollback reason

**MCP Servers:**
```powershell
git checkout <previous-commit-hash>
npm install
# Restart Claude Desktop
```

---

## Documentation Requirements

### Required Documentation

Every feature/change must include:

1. **Code Comments**
   - Function purpose
   - Parameter descriptions
   - Return value explanation
   - Usage examples

2. **README Updates**
   - New features listed
   - Installation steps if changed
   - Configuration requirements

3. **Architecture Documentation**
   - Entity relationship changes
   - Data flow updates
   - Integration points

4. **User Documentation**
   - How to use new features
   - Screenshots/examples
   - Troubleshooting tips

### Documentation Standards

**Markdown Formatting:**
- Use headers appropriately (h1 → h6)
- Code blocks with language tags
- Tables for structured data
- Links for cross-references

**File Locations:**
- `00_START_HERE/` - Quick start guides
- `01_Architecture/` - Technical specs
- `02_Build_Guides/` - Implementation details
- `06_MCP_Automation/` - MCP server docs

**Naming Convention:**
- UPPERCASE for major docs (THIS_FILE.md)
- lowercase-with-hyphens for guides (data-import-guide.md)
- Date prefixes for logs (2025-11-15-deployment-log.md)

---

## Security & Credentials Management

### Sensitive Data Protection

#### **Never Commit:**
- Passwords
- API keys
- Connection strings with credentials
- Personal tokens
- Client secrets
- Database passwords
- Email passwords

#### **.gitignore Configuration**
Already configured for:
```
*.env
*secret*
*password*
*credential*
node_modules/
Logs/
*.log
```

### Credential Storage

**Environment Variables (.env files):**
```env
# Good - stored in .env (not committed)
AZURE_CLIENT_SECRET=your-secret-here
SMTP_PASSWORD=your-password-here

# Bad - never in code
const password = "mypassword123";  // DON'T DO THIS
```

**Claude Desktop Configuration:**
- Credentials in `claude_desktop_config.json` are local only
- Not synchronized across machines
- Backup carefully (contains secrets)

**Azure Key Vault** (Future Enhancement):
- Store all production secrets
- MCP servers retrieve at runtime
- Audit access logs

### Security Best Practices

1. **Rotate Credentials Regularly**
   - Service principal secrets: Every 90 days
   - Personal access tokens: Every 180 days
   - Database passwords: Annually

2. **Principle of Least Privilege**
   - Grant minimum required permissions
   - Use service principals, not user accounts
   - Review access periodically

3. **Audit Trail**
   - Enable Dataverse audit logging
   - Review Git commit history
   - Monitor MCP server logs

4. **Incident Response**
   - If credentials compromised: Rotate immediately
   - Review access logs for unauthorized use
   - Update .gitignore if sensitive data was committed
   - Use `git filter-branch` to remove from history if needed

---

## Change Management

### Version Control Strategy

**Semantic Versioning:**
- Format: `MAJOR.MINOR.PATCH.BUILD`
- Tag releases in Git
- Maintain CHANGELOG.md

**Release Cycle:**
1. Development on feature branches
2. Merge to main after testing
3. Tag version: `git tag v1.2.0.4`
4. Deploy to production
5. Monitor for issues

### Change Log Template

**CHANGELOG.md:**
```markdown
# Change Log

## [1.2.0.4] - 2025-11-15
### Added
- Automated billing status calculation
- Email notifications for project milestones

### Fixed
- Asset hierarchy parent lookup issue
- Project rollup calculation accuracy

### Changed
- Updated NETA standards validation rules
- Improved MCP server error handling

### Deprecated
- Manual billing status workflow (replaced by automation)

### Security
- Rotated Azure service principal credentials
```

---

## Troubleshooting Guide

### Common Issues

#### **MCP Server Not Loading**
```powershell
# Check Claude Desktop config
Get-Content "$env:APPDATA\Claude\claude_desktop_config.json"

# Test server directly
cd MCP_Servers/resa-server-mcp
node server.js
# Should see: "server running on stdio"

# Check for errors
npm install  # Reinstall dependencies
```

#### **Git Push Rejected**
```powershell
# Pull latest changes first
git pull origin main --rebase

# Resolve conflicts if any
# Then push again
git push origin main
```

#### **Power Platform Import Fails**
- Check solution version (must be higher than existing)
- Verify all dependencies included
- Review error logs in Dataverse
- Import unmanaged version first to troubleshoot

#### **Dataverse Connection Timeout**
- Verify Azure credentials in .env
- Check service principal permissions
- Test connection in Azure AD
- Review firewall/network settings

---

## Appendix

### Quick Reference Commands

**Git:**
```powershell
git status                          # Check status
git checkout -b feature/name        # Create branch
git add .                          # Stage changes
git commit -m "type: message"      # Commit
git push origin branch-name        # Push to GitHub
git pull origin main               # Get latest
git merge main                     # Merge main into current
git tag v1.2.0.4                   # Tag version
```

**npm:**
```powershell
npm install                        # Install dependencies
npm audit                          # Check vulnerabilities
npm update                         # Update packages
npm list                          # List installed packages
```

**MCP Testing:**
```powershell
cd MCP_Servers/server-name
node server.js                     # Test locally
```

### Contact & Support

**Primary Contact:**
- Jason Swenson
- jason.swenson@resapower.com

**Resources:**
- GitHub: https://github.com/jasonlswenson-sys/RESA-Power-Project-Tracker
- Dataverse: org04ad071f.crm.dynamics.com
- Documentation: C:\RESA_Power_Build\Documentation\

### Document Maintenance

This document is a living guide and should be updated as:
- New workflows are established
- Tools and technologies change
- Team grows and roles expand
- Best practices evolve

**Update Process:**
1. Create `docs/update-guidelines` branch
2. Make changes to this document
3. Submit PR with rationale for changes
4. Review and merge
5. Communicate changes to team

---

**END OF DOCUMENT**

*This guideline document establishes the foundation for professional, consistent, and secure development practices for the RESA Power Project.*
