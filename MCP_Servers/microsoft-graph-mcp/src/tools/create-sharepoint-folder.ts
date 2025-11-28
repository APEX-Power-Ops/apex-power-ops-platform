import { getGraphClient, getSharePointSite, getDefaultDocumentLibrary } from "../utils/graph-client.js";

/**
 * Result interface for folder creation
 */
export interface FolderResult {
  folderId: string;
  folderName: string;
  folderPath: string;
  webUrl: string;
  createdAt: string;
}

/**
 * Create a folder in SharePoint document library
 */
export async function createSharePointFolder(params: {
  siteName: string;
  folderPath: string;
  description?: string;
}): Promise<FolderResult> {
  const { siteName, folderPath, description } = params;

  console.error(`Creating SharePoint folder: ${folderPath} in site: ${siteName}...`);

  try {
    const client = getGraphClient();

    // Get the SharePoint site
    const site = await getSharePointSite(siteName);
    console.error(`Found site: ${site.displayName} (${site.id})`);

    // Get the default document library
    const drive = await getDefaultDocumentLibrary(site.id);
    console.error(`Using drive: ${drive.name} (${drive.id})`);

    // Parse folder path to handle nested folders
    const pathParts = folderPath.split("/").filter((p) => p.length > 0);

    let currentPath = "/";
    let currentFolderId = "root";

    // Create folders one by one (nested structure)
    for (let i = 0; i < pathParts.length; i++) {
      const folderName = pathParts[i];
      const isLastFolder = i === pathParts.length - 1;

      try {
        // Try to get existing folder first
        const existingFolder = await client
          .api(`/drives/${drive.id}/items/${currentFolderId}:/${folderName}`)
          .get();

        console.error(`Folder already exists: ${folderName}`);
        currentFolderId = existingFolder.id;
        currentPath = existingFolder.parentReference.path + "/" + existingFolder.name;
      } catch (error: any) {
        // Folder doesn't exist, create it
        if (error.statusCode === 404) {
          console.error(`Creating folder: ${folderName}`);

          const newFolder = await client
            .api(`/drives/${drive.id}/items/${currentFolderId}/children`)
            .post({
              name: folderName,
              folder: {},
              "@microsoft.graph.conflictBehavior": "rename",
              description: isLastFolder ? description : undefined,
            });

          currentFolderId = newFolder.id;
          currentPath = newFolder.parentReference.path + "/" + newFolder.name;
          console.error(`Created folder: ${folderName} (${newFolder.id})`);
        } else {
          throw error;
        }
      }
    }

    // Get final folder details
    const finalFolder = await client
      .api(`/drives/${drive.id}/items/${currentFolderId}`)
      .get();

    console.error(`✅ Folder created successfully: ${folderPath}`);

    return {
      folderId: finalFolder.id,
      folderName: finalFolder.name,
      folderPath: finalFolder.parentReference.path + "/" + finalFolder.name,
      webUrl: finalFolder.webUrl,
      createdAt: finalFolder.createdDateTime,
    };
  } catch (error: any) {
    console.error(`Error creating SharePoint folder: ${error.message}`);
    throw new Error(`Failed to create SharePoint folder: ${error.message}`);
  }
}

/**
 * List folders in SharePoint document library
 */
export async function listSharePointFolders(params: {
  siteName: string;
  folderPath?: string;
}): Promise<any[]> {
  const { siteName, folderPath = "/" } = params;

  try {
    const client = getGraphClient();
    const site = await getSharePointSite(siteName);
    const drive = await getDefaultDocumentLibrary(site.id);

    let folderId = "root";
    if (folderPath !== "/") {
      const folder = await client
        .api(`/drives/${drive.id}/root:/${folderPath}`)
        .get();
      folderId = folder.id;
    }

    const children = await client
      .api(`/drives/${drive.id}/items/${folderId}/children`)
      .filter("folder ne null")
      .get();

    return children.value;
  } catch (error: any) {
    console.error(`Error listing SharePoint folders: ${error.message}`);
    throw error;
  }
}
