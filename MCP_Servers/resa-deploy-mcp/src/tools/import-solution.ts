import { getAccessToken, config } from "../utils/dataverse-client.js";
import axios from "axios";
import { readFileSync } from "fs";

/**
 * Import result interface
 */
export interface ImportResult {
  solutionName: string;
  version: string;
  importJobId: string;
  status: string;
  duration: number;
  importedAt: string;
  errors?: string[];
}

/**
 * Import solution to Dataverse
 */
export async function importSolution(params: {
  filePath: string;
  overwriteUnmanagedCustomizations?: boolean;
  publishWorkflows?: boolean;
  skipProductUpdateDependencies?: boolean;
}): Promise<ImportResult> {
  const {
    filePath,
    overwriteUnmanagedCustomizations = false,
    publishWorkflows = true,
    skipProductUpdateDependencies = false,
  } = params;

  console.error(`Importing solution from: ${filePath}...`);

  const startTime = Date.now();

  try {
    // 1. Read solution file
    const solutionFile = readFileSync(filePath);
    const base64Solution = solutionFile.toString("base64");

    // 2. Initiate import
    const importJobId = await initiateImport(
      base64Solution,
      overwriteUnmanagedCustomizations,
      publishWorkflows,
      skipProductUpdateDependencies
    );

    // 3. Poll for completion
    console.error("Waiting for import to complete...");
    const result = await pollImportStatus(importJobId);

    const duration = Date.now() - startTime;

    console.error(`✅ Solution imported successfully in ${duration}ms`);

    return {
      solutionName: result.solutionName,
      version: result.version,
      importJobId,
      status: result.status,
      duration,
      importedAt: new Date().toISOString(),
      errors: result.errors,
    };
  } catch (error: any) {
    console.error(`Error importing solution: ${error.message}`);
    throw new Error(`Failed to import solution: ${error.message}`);
  }
}

/**
 * Initiate solution import
 */
async function initiateImport(
  solutionFile: string,
  overwriteUnmanagedCustomizations: boolean,
  publishWorkflows: boolean,
  skipProductUpdateDependencies: boolean
): Promise<string> {
  const token = await getAccessToken();
  const url = `${config.DATAVERSE_URL}/api/data/v9.2/ImportSolution`;

  const importRequest = {
    CustomizationFile: solutionFile,
    OverwriteUnmanagedCustomizations: overwriteUnmanagedCustomizations,
    PublishWorkflows: publishWorkflows,
    SkipProductUpdateDependencies: skipProductUpdateDependencies,
    ImportJobId: crypto.randomUUID(), // Generate new import job ID
  };

  const response = await axios.post(url, importRequest, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    timeout: 300000, // 5 minute timeout for initial import
  });

  return importRequest.ImportJobId;
}

/**
 * Poll import status until complete
 */
async function pollImportStatus(
  importJobId: string,
  maxAttempts: number = 120,
  delayMs: number = 5000
): Promise<any> {
  const token = await getAccessToken();

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const url = `${config.DATAVERSE_URL}/api/data/v9.2/importjobs(${importJobId})?$select=importjobid,completedon,startedon,progress,data,solutionname`;

    try {
      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "OData-MaxVersion": "4.0",
          "OData-Version": "4.0",
          Accept: "application/json",
        },
      });

      const job = response.data;

      // Check if import is complete
      if (job.completedon) {
        // Parse import results
        const result = parseImportResults(job);
        return result;
      }

      // Still processing, log progress
      const progress = job.progress || 0;
      console.error(
        `Import in progress... ${progress}% (attempt ${attempt}/${maxAttempts})`
      );

      await new Promise((resolve) => setTimeout(resolve, delayMs));
    } catch (error: any) {
      if (attempt === maxAttempts) {
        throw new Error(
          `Import timed out after ${maxAttempts} attempts`
        );
      }
      // Continue polling
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }

  throw new Error("Import timed out");
}

/**
 * Parse import job results
 */
function parseImportResults(job: any): any {
  const errors: string[] = [];

  // Parse data field for errors
  if (job.data) {
    try {
      const data = JSON.parse(job.data);
      if (data.Errors && data.Errors.length > 0) {
        for (const error of data.Errors) {
          errors.push(error.ErrorText || error.Message || "Unknown error");
        }
      }
    } catch (e) {
      // data field may not be JSON
    }
  }

  return {
    solutionName: job.solutionname || "Unknown",
    version: "Unknown", // Version not available in import job
    status: errors.length > 0 ? "Completed with errors" : "Success",
    errors: errors.length > 0 ? errors : undefined,
  };
}

/**
 * Get import job status
 */
export async function getImportJobStatus(
  importJobId: string
): Promise<any> {
  const token = await getAccessToken();
  const url = `${config.DATAVERSE_URL}/api/data/v9.2/importjobs(${importJobId})?$select=importjobid,completedon,startedon,progress,data,solutionname`;

  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    },
  });

  return response.data;
}
