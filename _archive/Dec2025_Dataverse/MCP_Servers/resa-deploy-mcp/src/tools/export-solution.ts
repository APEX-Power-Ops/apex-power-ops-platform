import { getAccessToken, config } from "../utils/dataverse-client.js";
import axios from "axios";
import AdmZip from "adm-zip";
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

/**
 * Export result interface
 */
export interface ExportResult {
  solutionName: string;
  version: string;
  managed: boolean;
  size: string;
  path: string;
  exportedAt: string;
}

/**
 * Export solution from Dataverse
 */
export async function exportSolution(params: {
  solutionName: string;
  version?: string;
  managed?: boolean;
  outputPath?: string;
}): Promise<ExportResult> {
  const {
    solutionName,
    version,
    managed = false,
    outputPath = "C:\\RESA_Power_Build\\Solution_Exports",
  } = params;

  console.error(`Exporting solution: ${solutionName}...`);

  try {
    // 1. Get solution information
    const solutionInfo = await getSolutionInfo(solutionName);
    const solutionVersion = version || solutionInfo.version;

    // 2. Initiate export
    const exportJobId = await initiateExport(
      solutionName,
      managed
    );

    // 3. Poll for completion
    console.error("Waiting for export to complete...");
    const exportFile = await pollExportStatus(exportJobId);

    // 4. Download and save
    const fileName = `${solutionName}_${solutionVersion}_${
      managed ? "managed" : "unmanaged"
    }.zip`;
    const versionFolder = join(outputPath, `v${solutionVersion}`);

    // Create version folder if it doesn't exist
    mkdirSync(versionFolder, { recursive: true });

    const filePath = join(versionFolder, fileName);
    writeFileSync(filePath, exportFile);

    // Get file size
    const sizeInBytes = exportFile.length;
    const sizeInMB = (sizeInBytes / (1024 * 1024)).toFixed(2);

    console.error(`✅ Solution exported successfully: ${filePath}`);

    return {
      solutionName,
      version: solutionVersion,
      managed,
      size: `${sizeInMB} MB`,
      path: filePath,
      exportedAt: new Date().toISOString(),
    };
  } catch (error: any) {
    console.error(`Error exporting solution: ${error.message}`);
    throw new Error(`Failed to export solution: ${error.message}`);
  }
}

/**
 * Get solution information from Dataverse
 */
async function getSolutionInfo(solutionName: string): Promise<any> {
  const token = await getAccessToken();
  const url = `${config.DATAVERSE_URL}/api/data/v9.2/solutions?$select=solutionid,friendlyname,version,uniquename&$filter=uniquename eq '${solutionName}'`;

  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    },
  });

  if (!response.data.value || response.data.value.length === 0) {
    throw new Error(`Solution '${solutionName}' not found`);
  }

  return response.data.value[0];
}

/**
 * Initiate solution export
 */
async function initiateExport(
  solutionName: string,
  managed: boolean
): Promise<string> {
  const token = await getAccessToken();
  const url = `${config.DATAVERSE_URL}/api/data/v9.2/ExportSolution`;

  const exportRequest = {
    SolutionName: solutionName,
    Managed: managed,
    ExportAutoNumberingSettings: true,
    ExportCalendarSettings: true,
    ExportCustomizationSettings: true,
    ExportEmailTrackingSettings: true,
    ExportGeneralSettings: true,
    ExportMarketingSettings: true,
    ExportOutlookSynchronizationSettings: true,
    ExportRelationshipRoles: true,
    ExportIsvConfig: true,
    ExportSales: true,
    ExportExternalApplications: true,
  };

  const response = await axios.post(url, exportRequest, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });

  // ExportSolution returns immediately with ExportJobId
  return response.data.ExportJobId;
}

/**
 * Poll export status until complete
 */
async function pollExportStatus(
  jobId: string,
  maxAttempts: number = 60,
  delayMs: number = 5000
): Promise<Buffer> {
  const token = await getAccessToken();

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const url = `${config.DATAVERSE_URL}/api/data/v9.2/ExportSolutionAsync(ExportJobId=${jobId})`;

    try {
      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "OData-MaxVersion": "4.0",
          "OData-Version": "4.0",
          Accept: "application/json",
        },
      });

      // Check if export is complete
      if (response.data.ExportSolutionFile) {
        // Solution file is base64 encoded
        const buffer = Buffer.from(
          response.data.ExportSolutionFile,
          "base64"
        );
        return buffer;
      }

      // Still processing, wait and retry
      console.error(
        `Export in progress... (attempt ${attempt}/${maxAttempts})`
      );
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    } catch (error: any) {
      if (attempt === maxAttempts) {
        throw new Error(
          `Export timed out after ${maxAttempts} attempts`
        );
      }
      // Continue polling
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }

  throw new Error("Export timed out");
}

/**
 * List all solutions in the environment
 */
export async function listSolutions(): Promise<any[]> {
  const token = await getAccessToken();
  const url = `${config.DATAVERSE_URL}/api/data/v9.2/solutions?$select=solutionid,friendlyname,uniquename,version,ismanaged&$filter=isvisible eq true&$orderby=friendlyname asc`;

  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    },
  });

  return response.data.value || [];
}
