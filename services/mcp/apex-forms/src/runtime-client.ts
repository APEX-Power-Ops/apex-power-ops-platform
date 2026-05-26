import fs from "node:fs/promises"
import os from "node:os"
import path from "node:path"
import { fileURLToPath } from "node:url"

type ToolArgs = Record<string, unknown>
type RunEnv = "sandbox"

const moduleDir = path.dirname(fileURLToPath(import.meta.url))
const packageRoot = ["src", "build"].includes(path.basename(moduleDir)) ? path.resolve(moduleDir, "..") : moduleDir
const repoRoot = path.resolve(packageRoot, "..", "..", "..")
const defaultTemplateRoot = path.resolve(repoRoot, "..", "source-domains", "neta-forms", "Templates")

const templateRoot = path.resolve(
  process.env.APEX_FORMS_TEMPLATE_ROOT ?? process.env.FORMS_ENGINE_TEMPLATES_PATH ?? defaultTemplateRoot,
)
const previewRoot = path.resolve(
  process.env.APEX_FORMS_PREVIEW_ROOT ??
    process.env.FORMS_ENGINE_ARTIFACTS_PATH ??
    path.join(os.tmpdir(), "apex-forms-preview"),
)
const runtimeBaseUrl = (process.env.APEX_FORMS_RUNTIME_URL ?? "http://127.0.0.1:8080").replace(/\/$/, "")

const textExtensions = new Set([".css", ".html", ".htm", ".json", ".md", ".txt", ".xml", ".yaml", ".yml"])
const templateExtensions = new Set([...textExtensions, ".docx", ".pdf", ".xlsx"])

export const tools = [
  {
    name: "get_runtime_status",
    description: "Read the bounded forms-engine runtime health contract and local apex-forms posture.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "list_templates",
    description: "List form templates beneath the admitted neta-forms template root.",
    inputSchema: {
      type: "object",
      properties: {
        family: { type: "string" },
        includeArchived: { type: "boolean" },
      },
    },
  },
  {
    name: "get_template_metadata",
    description: "Return bounded metadata for one template path under the admitted template root.",
    inputSchema: {
      type: "object",
      properties: {
        templatePath: { type: "string" },
      },
      required: ["templatePath"],
    },
  },
  {
    name: "get_template_content",
    description: "Return bounded text content for an inspectable text template.",
    inputSchema: {
      type: "object",
      properties: {
        templatePath: { type: "string" },
        maxBytes: { type: "number" },
      },
      required: ["templatePath"],
    },
  },
  {
    name: "validate_template",
    description: "Validate one template against bounded neta-forms authority checks.",
    inputSchema: {
      type: "object",
      properties: {
        templatePath: { type: "string" },
      },
      required: ["templatePath"],
    },
  },
  {
    name: "render_preview",
    description: "Create a sandbox-only preview request artifact for forms-engine rendering.",
    inputSchema: {
      type: "object",
      properties: {
        templatePath: { type: "string" },
        sampleData: { type: "object" },
      },
      required: ["templatePath"],
    },
  },
  {
    name: "render_template",
    description: "Alias for render_preview retained for canary compatibility.",
    inputSchema: {
      type: "object",
      properties: {
        templatePath: { type: "string" },
        sampleData: { type: "object" },
      },
      required: ["templatePath"],
    },
  },
] as const

function assertSandbox(): RunEnv {
  const env = (process.env.APEX_FORMS_ENV ?? process.env.APEX_RUN_ENV ?? "sandbox").toLowerCase()
  if (env !== "sandbox") {
    throw new Error("apex-forms env=host is not admitted by this source-only packet")
  }
  return "sandbox"
}

function normalizeRelative(value: string): string {
  return value.split(path.sep).join("/")
}

function resolveTemplatePath(templatePath = "."): string {
  const target = path.isAbsolute(templatePath)
    ? path.resolve(templatePath)
    : path.resolve(templateRoot, templatePath)

  if (target !== templateRoot && !target.startsWith(`${templateRoot}${path.sep}`)) {
    throw new Error(`Template path escapes admitted root: ${templatePath}`)
  }

  return target
}

function parseFamily(relativePath: string): string {
  return relativePath.split(/[\\/]/)[0] || "root"
}

function metadataFromPath(relativePath: string, sizeBytes: number) {
  const extension = path.extname(relativePath).toLowerCase()
  const name = path.basename(relativePath)
  const family = parseFamily(relativePath)
  const version = name.match(/(?:^|-)v(\d+)(?:-|\.|$)/i)?.[1] ?? null
  const archived = relativePath.split(/[\\/]/).some((part) => part.toLowerCase() === "archive")

  return {
    templatePath: normalizeRelative(relativePath),
    family,
    format: extension.replace(/^\./, ""),
    version,
    archived,
    sizeBytes,
  }
}

async function walkTemplates(root: string, includeArchived: boolean, familyFilter?: string) {
  const entries: Array<ReturnType<typeof metadataFromPath>> = []

  async function walk(directory: string): Promise<void> {
    const children = await fs.readdir(directory, { withFileTypes: true })

    for (const child of children) {
      const childPath = path.join(directory, child.name)
      const relativePath = path.relative(root, childPath)
      const parts = relativePath.split(path.sep)

      if (!includeArchived && parts.some((part) => part.toLowerCase() === "archive")) {
        continue
      }

      if (familyFilter && parts[0]?.toLowerCase() !== familyFilter.toLowerCase()) {
        continue
      }

      if (child.isDirectory()) {
        await walk(childPath)
        continue
      }

      const extension = path.extname(child.name).toLowerCase()
      if (!templateExtensions.has(extension)) {
        continue
      }

      const stat = await fs.stat(childPath)
      entries.push(metadataFromPath(relativePath, stat.size))
    }
  }

  await walk(root)
  return entries.sort((left, right) => left.templatePath.localeCompare(right.templatePath))
}

async function readRuntimeStatus() {
  const response = await fetch(`${runtimeBaseUrl}/health`)
  if (!response.ok) {
    throw new Error(`forms-engine health failed: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

async function getTemplateMetadata(templatePath: string) {
  const target = resolveTemplatePath(templatePath)
  const stat = await fs.stat(target)
  if (!stat.isFile()) {
    throw new Error(`Template path is not a file: ${templatePath}`)
  }
  return metadataFromPath(path.relative(templateRoot, target), stat.size)
}

async function getTemplateContent(templatePath: string, maxBytes = 50000) {
  const metadata = await getTemplateMetadata(templatePath)
  const extension = path.extname(metadata.templatePath).toLowerCase()
  if (!textExtensions.has(extension)) {
    return {
      metadata,
      content: null,
      truncated: false,
      note: "Binary template content is not returned through apex-forms.",
    }
  }

  const content = await fs.readFile(resolveTemplatePath(metadata.templatePath), "utf8")
  return {
    metadata,
    content: content.length > maxBytes ? content.slice(0, maxBytes) : content,
    truncated: content.length > maxBytes,
  }
}

async function validateTemplate(templatePath: string) {
  const metadata = await getTemplateMetadata(templatePath)
  const checks: Array<{ name: string; status: "pass" | "warn" | "fail"; detail: string }> = []

  checks.push({
    name: "path_boundary",
    status: "pass",
    detail: "Template resolves under the admitted template root.",
  })

  checks.push({
    name: "non_empty",
    status: metadata.sizeBytes > 0 ? "pass" : "fail",
    detail: metadata.sizeBytes > 0 ? "Template file is non-empty." : "Template file is empty.",
  })

  checks.push({
    name: "known_family",
    status: ["MOP", "AHA", "SOP", "Forms"].includes(metadata.family) ? "pass" : "warn",
    detail: `Detected family ${metadata.family}.`,
  })

  if (metadata.format === "html" || metadata.format === "htm") {
    const inspected = await getTemplateContent(metadata.templatePath, 100000)
    const content = String(inspected.content ?? "")
    checks.push({
      name: "html_document",
      status: /<!doctype html|<html[\s>]/i.test(content) ? "pass" : "warn",
      detail: "HTML templates should be full document templates.",
    })
    checks.push({
      name: "print_ready",
      status: /@page/i.test(content) ? "pass" : "warn",
      detail: "Print-ready templates should declare @page rules.",
    })
  }

  if (metadata.format === "json") {
    try {
      const inspected = await getTemplateContent(metadata.templatePath, 500000)
      JSON.parse(String(inspected.content ?? ""))
      checks.push({ name: "json_parse", status: "pass", detail: "JSON parses successfully." })
    } catch (error) {
      checks.push({
        name: "json_parse",
        status: "fail",
        detail: error instanceof Error ? error.message : String(error),
      })
    }
  }

  const hasFailure = checks.some((check) => check.status === "fail")
  const hasWarning = checks.some((check) => check.status === "warn")

  return {
    template: metadata,
    status: hasFailure ? "fail" : hasWarning ? "warn" : "pass",
    authoritySources: [
      "C:/APEX Platform/source-domains/neta-forms/REPO_PASSPORT.md",
      "C:/APEX Platform/source-domains/neta-forms/.claude/MASTER.md#10-15",
    ],
    checks,
  }
}

async function renderPreview(templatePath: string, sampleData: unknown) {
  const env = assertSandbox()
  const validation = await validateTemplate(templatePath)
  const runtime = await readRuntimeStatus()

  await fs.mkdir(previewRoot, { recursive: true })

  const fileSafeTemplate = validation.template.templatePath.replace(/[^a-z0-9_.-]+/gi, "-")
  const outputPath = path.join(previewRoot, `apex-forms-preview-${Date.now()}-${fileSafeTemplate}.json`)
  const preview = {
    mode: "sandbox-preview-request",
    env,
    runtime,
    template: validation.template,
    validation,
    sampleData: sampleData ?? {},
    note:
      "Current forms-engine runtime exposes health only; this artifact records a bounded preview request for a future render endpoint or command.",
  }

  await fs.writeFile(outputPath, `${JSON.stringify(preview, null, 2)}\n`, "utf8")

  return {
    status: "created",
    env,
    outputPath,
    returnedPayload: "metadata-only",
    runtimeService: typeof runtime === "object" && runtime !== null ? (runtime as { service?: unknown }).service : null,
    template: validation.template,
    validationStatus: validation.status,
  }
}

export async function callTool(name: string, args: ToolArgs = {}) {
  switch (name) {
    case "get_runtime_status":
      assertSandbox()
      return {
        server: "apex-forms",
        env: "sandbox",
        templateRoot,
        templateRootExists: await fs
          .stat(templateRoot)
          .then((stat) => stat.isDirectory())
          .catch(() => false),
        previewRoot,
        runtimeBaseUrl,
        runtime: await readRuntimeStatus(),
      }
    case "list_templates":
      return {
        templateRoot,
        templates: await walkTemplates(
          templateRoot,
          Boolean(args.includeArchived ?? false),
          typeof args.family === "string" ? args.family : undefined,
        ),
      }
    case "get_template_metadata":
      return getTemplateMetadata(String(args.templatePath ?? ""))
    case "get_template_content":
      return getTemplateContent(String(args.templatePath ?? ""), Number(args.maxBytes ?? 50000))
    case "validate_template":
      return validateTemplate(String(args.templatePath ?? ""))
    case "render_preview":
    case "render_template":
      return renderPreview(String(args.templatePath ?? ""), args.sampleData)
    default:
      throw new Error(`Unknown tool: ${name}`)
  }
}

export function getRuntimeBaseUrl() {
  return runtimeBaseUrl
}

export function getTemplateRoot() {
  return templateRoot
}
