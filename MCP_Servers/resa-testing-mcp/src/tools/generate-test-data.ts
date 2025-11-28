import { queryDataverse, createRecord, updateRecord, deleteRecord } from "../utils/dataverse-client.js";

export interface TestDataResult {
  created: {
    projects: number;
    scopes: number;
    tasks: number;
    apparatus: number;
    revenue: number;
  };
  projectIds: string[];
  scopeIds: string[];
  taskIds: string[];
  apparatusIds: string[];
  revenueIds: string[];
  timestamp: string;
}

/**
 * Generate realistic test data hierarchies for testing
 * Creates projects → scopes → tasks → apparatus → revenue
 * 
 * @param scenario - Predefined scenario name or 'custom'
 * @param projects - Number of projects to create
 * @param scopesPerProject - Number of scopes per project
 * @param tasksPerScope - Number of tasks per scope
 * @param apparatusPerTask - Number of apparatus per task
 * @param completePercentage - Percentage of apparatus to mark complete (0-100)
 * @param includeFinancialData - Whether to create revenue records for completed apparatus
 */
export async function generateTestData(params: {
  scenario?: string;
  projects?: number;
  scopesPerProject?: number;
  tasksPerScope?: number;
  apparatusPerTask?: number;
  completePercentage?: number;
  includeFinancialData?: boolean;
}): Promise<TestDataResult> {
  const {
    scenario = "custom",
    projects = 1,
    scopesPerProject = 2,
    tasksPerScope = 3,
    apparatusPerTask = 10,
    completePercentage = 50,
    includeFinancialData = true,
  } = params;

  console.error(`Generating test data: ${scenario} scenario...`);

  const result: TestDataResult = {
    created: { projects: 0, scopes: 0, tasks: 0, apparatus: 0, revenue: 0 },
    projectIds: [],
    scopeIds: [],
    taskIds: [],
    apparatusIds: [],
    revenueIds: [],
    timestamp: new Date().toISOString(),
  };

  try {
    // Create projects
    for (let p = 0; p < projects; p++) {
      const projectId = await createProject(p);
      result.projectIds.push(projectId);
      result.created.projects++;

      // Create scopes for this project
      for (let s = 0; s < scopesPerProject; s++) {
        const scopeId = await createScope(projectId, p, s);
        result.scopeIds.push(scopeId);
        result.created.scopes++;

        // Create tasks for this scope
        for (let t = 0; t < tasksPerScope; t++) {
          const taskId = await createTask(scopeId, p, s, t);
          result.taskIds.push(taskId);
          result.created.tasks++;

          // Create apparatus for this task
          for (let a = 0; a < apparatusPerTask; a++) {
            const shouldComplete = Math.random() * 100 < completePercentage;
            const apparatusId = await createApparatus(taskId, p, s, t, a, shouldComplete);
            result.apparatusIds.push(apparatusId);
            result.created.apparatus++;

            // Create revenue if completed and financial data requested
            if (shouldComplete && includeFinancialData) {
              const revenueId = await createRevenue(apparatusId, taskId, scopeId);
              result.revenueIds.push(revenueId);
              result.created.revenue++;
            }
          }
        }
      }
    }

    console.error(`Test data created successfully: ${JSON.stringify(result.created)}`);
    return result;

  } catch (error: any) {
    console.error(`Error generating test data: ${error.message}`);
    throw new Error(`Test data generation failed: ${error.message}`);
  }
}

/**
 * Create a test project
 */
async function createProject(index: number): Promise<string> {
  const data = {
    cr950_name: `TEST-Project-${index + 1}-${Date.now()}`,
    cr950_projectnumber: `TEST-P${String(index + 1).padStart(3, "0")}`,
    cr950_description: `Automated test project ${index + 1}`,
    statecode: 0,
    statuscode: 1,
  };

  return await createRecord("cr950_projectses", data);
}

/**
 * Create a test scope
 */
async function createScope(projectId: string, projIndex: number, scopeIndex: number): Promise<string> {
  const data = {
    cr950_name: `TEST-Scope-${projIndex + 1}-${scopeIndex + 1}`,
    "cr950_Project@odata.bind": `/cr950_projectses(${projectId})`,
    cr950_description: `Test scope ${scopeIndex + 1} for project ${projIndex + 1}`,
    statecode: 0,
    statuscode: 1,
  };

  return await createRecord("cr950_projectscopes", data);
}

/**
 * Create a test task
 */
async function createTask(
  scopeId: string,
  projIndex: number,
  scopeIndex: number,
  taskIndex: number
): Promise<string> {
  const estimatedHours = Math.floor(Math.random() * 20) + 5; // 5-25 hours
  const actualHours = Math.floor(estimatedHours * (0.8 + Math.random() * 0.4)); // 80-120% of estimate

  const data = {
    cr950_name: `TEST-Task-${projIndex + 1}-${scopeIndex + 1}-${taskIndex + 1}`,
    "cr950_Scope@odata.bind": `/cr950_projectscopes(${scopeId})`,
    cr950_description: `Test task ${taskIndex + 1}`,
    cr950_estimatedhours: estimatedHours,
    cr950_actualhours: actualHours,
    statecode: 0,
    statuscode: 1,
  };

  return await createRecord("cr950_taskses", data);
}

/**
 * Create a test apparatus
 */
async function createApparatus(
  taskId: string,
  projIndex: number,
  scopeIndex: number,
  taskIndex: number,
  apparatusIndex: number,
  isComplete: boolean
): Promise<string> {
  const data: any = {
    cr950_name: `TEST-APP-${projIndex + 1}-${scopeIndex + 1}-${taskIndex + 1}-${apparatusIndex + 1}`,
    "cr950_Task@odata.bind": `/cr950_taskses(${taskId})`,
    cr950_description: `Test apparatus ${apparatusIndex + 1}`,
    cr950_apparatusnumber: `APP${String(apparatusIndex + 1).padStart(4, "0")}`,
    cr950_equipmenttype: "Breaker", // Example type
    cr950_manufacturer: "Test Manufacturer",
    cr950_voltage: "480V",
    cr950_netastandard: 915400002, // NETA Standard Option Set value
    statecode: 0,
    statuscode: isComplete ? 915400001 : 1, // Complete or Active
  };

  if (isComplete) {
    data.cr950_CompletedDate = new Date().toISOString();
  }

  return await createRecord("cr950_apparatuses", data);
}

/**
 * Create a test revenue record
 */
async function createRevenue(
  apparatusId: string,
  taskId: string,
  scopeId: string
): Promise<string> {
  const netaSellPrice = Math.floor(Math.random() * 500) + 100; // $100-$600
  const additionalSellPrice = Math.floor(Math.random() * 200); // $0-$200

  const data = {
    cr950_name: `TEST-REV-${Date.now()}`,
    "cr950_Apparatus@odata.bind": `/cr950_apparatuses(${apparatusId})`,
    "cr950_Task@odata.bind": `/cr950_taskses(${taskId})`,
    "cr950_Scope@odata.bind": `/cr950_projectscopes(${scopeId})`,
    cr950_netasellprice: netaSellPrice,
    cr950_additionalsellprice: additionalSellPrice,
    cr950_totalrevenue: netaSellPrice + additionalSellPrice,
    statecode: 0,
    statuscode: 1,
  };

  return await createRecord("cr950_apparatusrevenues", data);
}

/**
 * Clean up test data (delete all records created)
 */
export async function cleanupTestData(testDataResult: TestDataResult): Promise<void> {
  console.error("Cleaning up test data...");

  try {
    // Delete in reverse order (revenue → apparatus → tasks → scopes → projects)
    for (const id of testDataResult.revenueIds) {
      await deleteRecord("cr950_apparatusrevenues", id);
    }

    for (const id of testDataResult.apparatusIds) {
      await deleteRecord("cr950_apparatuses", id);
    }

    for (const id of testDataResult.taskIds) {
      await deleteRecord("cr950_taskses", id);
    }

    for (const id of testDataResult.scopeIds) {
      await deleteRecord("cr950_projectscopes", id);
    }

    for (const id of testDataResult.projectIds) {
      await deleteRecord("cr950_projectses", id);
    }

    console.error("Test data cleanup complete");
  } catch (error: any) {
    console.error(`Error during cleanup: ${error.message}`);
    throw new Error(`Test data cleanup failed: ${error.message}`);
  }
}
