import { exportSolution, ExportResult } from "./export-solution.js";
import { writeFileSync, readFileSync, mkdirSync, existsSync, readdirSync } from "fs";
import { join } from "path";

/**
 * Backup metadata interface
 */
export interface BackupMetadata {
  backupId: string;
  solutionName: string;
  version: string;
  timestamp: string;
  managed: ExportResult;
  unmanaged: ExportResult;
  notes?: string;
}

/**
 * Backup result interface
 */
export interface BackupResult {
  backupId: string;
  backupPath: string;
  solutionName: string;
  version: string;
  managedSize: number;
  unmanagedSize: number;
  totalSize: number;
  timestamp: string;
}

/**
 * Backup a solution (both managed and unmanaged)
 */
export async function backupSolution(params: {
  solutionName: string;
  backupPath?: string;
  notes?: string;
}): Promise<BackupResult> {
  const {
    solutionName,
    backupPath = "C:\\RESA_Power_Build\\Solution_Exports\\Backups",
    notes,
  } = params;

  console.error(`Creating backup for solution: ${solutionName}...`);

  try {
    // Generate backup ID (timestamp-based)
    const backupId = new Date().toISOString().replace(/[:.]/g, "-");
    const solutionBackupPath = join(backupPath, backupId, solutionName);

    // Create backup directory
    mkdirSync(solutionBackupPath, { recursive: true });

    // Export both managed and unmanaged versions
    console.error("Exporting unmanaged version...");
    const unmanagedExport = await exportSolution({
      solutionName,
      managed: false,
      outputPath: solutionBackupPath,
    });

    console.error("Exporting managed version...");
    const managedExport = await exportSolution({
      solutionName,
      managed: true,
      outputPath: solutionBackupPath,
    });

    // Create backup metadata
    const metadata: BackupMetadata = {
      backupId,
      solutionName,
      version: unmanagedExport.version,
      timestamp: new Date().toISOString(),
      managed: managedExport,
      unmanaged: unmanagedExport,
      notes,
    };

    // Save metadata
    const metadataPath = join(solutionBackupPath, "backup-metadata.json");
    writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));

    // Parse size strings to bytes (format: "X.XX MB" or "X KB")
    const managedBytes = parseSizeString(managedExport.size);
    const unmanagedBytes = parseSizeString(unmanagedExport.size);
    const totalSize = managedBytes + unmanagedBytes;

    console.error(
      `✅ Backup created successfully: ${backupId} (${formatBytes(totalSize)})`
    );

    return {
      backupId,
      backupPath: solutionBackupPath,
      solutionName,
      version: unmanagedExport.version,
      managedSize: managedBytes,
      unmanagedSize: unmanagedBytes,
      totalSize,
      timestamp: metadata.timestamp,
    };
  } catch (error: any) {
    console.error(`Error creating backup: ${error.message}`);
    throw new Error(`Failed to create backup: ${error.message}`);
  }
}

/**
 * List all backups
 */
export async function listBackups(params?: {
  backupPath?: string;
  solutionName?: string;
}): Promise<BackupMetadata[]> {
  const backupPath =
    params?.backupPath || "C:\\RESA_Power_Build\\Solution_Exports\\Backups";

  if (!existsSync(backupPath)) {
    return [];
  }

  const backups: BackupMetadata[] = [];

  // List all backup directories
  const backupDirs = readdirSync(backupPath, { withFileTypes: true })
    .filter((dirent) => dirent.isDirectory())
    .map((dirent) => dirent.name);

  for (const backupId of backupDirs) {
    // List solution directories within backup
    const backupIdPath = join(backupPath, backupId);
    const solutionDirs = readdirSync(backupIdPath, { withFileTypes: true })
      .filter((dirent) => dirent.isDirectory())
      .map((dirent) => dirent.name);

    for (const solutionDir of solutionDirs) {
      // Filter by solution name if specified
      if (params?.solutionName && solutionDir !== params.solutionName) {
        continue;
      }

      const metadataPath = join(backupIdPath, solutionDir, "backup-metadata.json");
      if (existsSync(metadataPath)) {
        const metadata = JSON.parse(readFileSync(metadataPath, "utf8"));
        backups.push(metadata);
      }
    }
  }

  // Sort by timestamp descending (newest first)
  backups.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return backups;
}

/**
 * Get backup metadata
 */
export async function getBackupMetadata(params: {
  backupId: string;
  solutionName: string;
  backupPath?: string;
}): Promise<BackupMetadata> {
  const {
    backupId,
    solutionName,
    backupPath = "C:\\RESA_Power_Build\\Solution_Exports\\Backups",
  } = params;

  const metadataPath = join(
    backupPath,
    backupId,
    solutionName,
    "backup-metadata.json"
  );

  if (!existsSync(metadataPath)) {
    throw new Error(
      `Backup not found: ${backupId}/${solutionName}`
    );
  }

  return JSON.parse(readFileSync(metadataPath, "utf8"));
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
}

/**
 * Parse size string to bytes
 * Handles formats like "1.23 MB", "456 KB", "789 Bytes"
 */
function parseSizeString(sizeStr: string): number {
  const match = sizeStr.match(/([\d.]+)\s*(Bytes|KB|MB|GB)/i);
  if (!match) return 0;

  const value = parseFloat(match[1]);
  const unit = match[2].toUpperCase();

  const multipliers: Record<string, number> = {
    BYTES: 1,
    KB: 1024,
    MB: 1024 * 1024,
    GB: 1024 * 1024 * 1024,
  };

  return Math.round(value * (multipliers[unit] || 1));
}
