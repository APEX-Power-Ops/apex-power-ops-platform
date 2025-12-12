import { getGraphClient, getSharePointSite, getDefaultDocumentLibrary } from "../utils/graph-client.js";
import { readFileSync } from "fs";

/**
 * Result interface for file upload
 */
export interface UploadResult {
  fileId: string;
  fileName: string;
  fileSize: number;
  webUrl: string;
  uploadedAt: string;
}

/**
 * Upload file to SharePoint document library
 */
export async function uploadToSharePoint(params: {
  siteName: string;
  folderPath: string;
  filePath: string;
  fileName?: string;
  overwrite?: boolean;
}): Promise<UploadResult> {
  const { siteName, folderPath, filePath, fileName, overwrite = false } = params;

  const targetFileName = fileName || filePath.split(/[\\/]/).pop() || "file";

  console.error(`Uploading file: ${targetFileName} to ${siteName}/${folderPath}...`);

  try {
    const client = getGraphClient();

    // Get the SharePoint site and drive
    const site = await getSharePointSite(siteName);
    const drive = await getDefaultDocumentLibrary(site.id);

    // Read file content
    const fileContent = readFileSync(filePath);
    const fileSize = fileContent.length;

    console.error(`File size: ${formatBytes(fileSize)}`);

    // Get or create folder
    let folderId = "root";
    if (folderPath !== "/") {
      try {
        const folder = await client
          .api(`/drives/${drive.id}/root:/${folderPath}`)
          .get();
        folderId = folder.id;
      } catch (error: any) {
        if (error.statusCode === 404) {
          throw new Error(`Folder not found: ${folderPath}. Create it first using create_sharepoint_folder.`);
        }
        throw error;
      }
    }

    // Upload file
    let uploadedFile;
    if (fileSize < 4 * 1024 * 1024) {
      // Small file: simple upload (< 4MB)
      console.error("Using simple upload...");
      uploadedFile = await client
        .api(`/drives/${drive.id}/items/${folderId}:/${targetFileName}:/content`)
        .header("Content-Type", "application/octet-stream")
        .put(fileContent);
    } else {
      // Large file: resumable upload (>= 4MB)
      console.error("Using resumable upload...");
      
      // Create upload session
      const uploadSession = await client
        .api(`/drives/${drive.id}/items/${folderId}:/${targetFileName}:/createUploadSession`)
        .post({
          item: {
            "@microsoft.graph.conflictBehavior": overwrite ? "replace" : "rename",
          },
        });

      // Upload in chunks (4MB chunks)
      const chunkSize = 4 * 1024 * 1024;
      let offset = 0;

      while (offset < fileSize) {
        const chunk = fileContent.slice(offset, Math.min(offset + chunkSize, fileSize));
        const chunkEnd = offset + chunk.length - 1;

        console.error(`Uploading chunk: ${offset}-${chunkEnd}/${fileSize}`);

        const response = await fetch(uploadSession.uploadUrl, {
          method: "PUT",
          headers: {
            "Content-Range": `bytes ${offset}-${chunkEnd}/${fileSize}`,
            "Content-Length": chunk.length.toString(),
          },
          body: chunk,
        });

        if (response.status === 201 || response.status === 200) {
          uploadedFile = await response.json();
          break;
        } else if (response.status !== 202) {
          throw new Error(`Upload failed with status ${response.status}`);
        }

        offset += chunk.length;
      }
    }

    console.error(`✅ File uploaded successfully: ${targetFileName}`);

    return {
      fileId: uploadedFile.id,
      fileName: uploadedFile.name,
      fileSize: uploadedFile.size,
      webUrl: uploadedFile.webUrl,
      uploadedAt: uploadedFile.createdDateTime,
    };
  } catch (error: any) {
    console.error(`Error uploading file: ${error.message}`);
    throw new Error(`Failed to upload file to SharePoint: ${error.message}`);
  }
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}
