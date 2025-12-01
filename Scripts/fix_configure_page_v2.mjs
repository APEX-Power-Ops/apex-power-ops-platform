import fs from 'fs';

const filePath = 'C:/Users/jjswe/Projects/resa-web-app/src/app/import/configure/page.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Helper to extract function by counting braces
function extractFunction(content, startMarker) {
  const start = content.indexOf(startMarker);
  if (start === -1) return { start: -1, end: -1, func: null };
  
  let end = start;
  let braceCount = 0;
  let foundStart = false;

  for (let i = start; i < content.length; i++) {
    if (content[i] === '{') { braceCount++; foundStart = true; }
    if (content[i] === '}') { braceCount--; }
    if (foundStart && braceCount === 0 && content[i] === '}') {
      // Check for semicolon after
      end = content[i+1] === ';' ? i + 2 : i + 1;
      break;
    }
  }
  
  return { start, end, func: content.substring(start, end) };
}

// Fix 1: autoCreateAllTasks
const autoInfo = extractFunction(content, '  const autoCreateAllTasks');
if (autoInfo.func) {
  const newAutoCreateAllTasks = `  const autoCreateAllTasks = () => {
    if (!activeScope) return;

    let idCounter = Date.now();
    
    // Build all new tasks first
    const newTasks: TaskAssignment[] = suggestedTasks.map(section => ({
      id: \`task-\${idCounter++}\`,
      name: section,
      apparatusIds: [],
    }));

    // Create section -> taskId map for quick lookup
    const sectionToTaskId = new Map<string, string>();
    newTasks.forEach(task => sectionToTaskId.set(task.name, task.id));

    // Deep copy and update in one pass
    const newConfigs = scopeConfigs.map((config, idx) => {
      if (idx !== activeScopeIndex) return config;
      
      return {
        ...config,
        tasks: [...config.tasks, ...newTasks],
        apparatus: config.apparatus.map(a => {
          if (a.taskId) return a; // Already assigned
          const taskId = sectionToTaskId.get(a.section);
          return taskId ? { ...a, taskId } : a;
        })
      };
    });

    setScopeConfigs(newConfigs);
    setSelectedApparatus(new Set());
  };`;
  
  content = content.substring(0, autoInfo.start) + newAutoCreateAllTasks + content.substring(autoInfo.end);
  console.log('✓ Fixed autoCreateAllTasks');
} else {
  console.log('✗ Could not find autoCreateAllTasks');
}

// Fix 2: createTaskFromSection - recalculate since content changed
const taskFromSectionInfo = extractFunction(content, '  const createTaskFromSection');
if (taskFromSectionInfo.func) {
  const newCreateTaskFromSection = `  const createTaskFromSection = (section: string) => {
    if (!activeScope) return;

    const taskId = \`task-\${Date.now()}-\${Math.random().toString(36).substr(2, 9)}\`;
    
    // Deep copy the configs array and the active scope
    const newConfigs = scopeConfigs.map((config, idx) => 
      idx === activeScopeIndex 
        ? {
            ...config,
            tasks: [...config.tasks, { id: taskId, name: section, apparatusIds: [] as string[] }],
            apparatus: config.apparatus.map(a =>
              a.section === section && !a.taskId ? { ...a, taskId } : a
            )
          }
        : config
    );

    setScopeConfigs(newConfigs);
    setSelectedApparatus(new Set());
  };`;
  
  content = content.substring(0, taskFromSectionInfo.start) + newCreateTaskFromSection + content.substring(taskFromSectionInfo.end);
  console.log('✓ Fixed createTaskFromSection');
} else {
  console.log('✗ Could not find createTaskFromSection');
}

// Fix 3: unassignFromTask
const unassignInfo = extractFunction(content, '  const unassignFromTask');
if (unassignInfo.func) {
  const newUnassignFromTask = `  const unassignFromTask = (apparatusId: string) => {
    const newConfigs = scopeConfigs.map((config, idx) => 
      idx === activeScopeIndex 
        ? {
            ...config,
            apparatus: config.apparatus.map(a =>
              a.id === apparatusId ? { ...a, taskId: null } : a
            )
          }
        : config
    );
    setScopeConfigs(newConfigs);
  };`;
  
  content = content.substring(0, unassignInfo.start) + newUnassignFromTask + content.substring(unassignInfo.end);
  console.log('✓ Fixed unassignFromTask');
} else {
  console.log('✗ Could not find unassignFromTask');
}

// Fix 4: deleteTask
const deleteTaskInfo = extractFunction(content, '  const deleteTask');
if (deleteTaskInfo.func) {
  const newDeleteTask = `  const deleteTask = (taskId: string) => {
    const newConfigs = scopeConfigs.map((config, idx) => {
      if (idx !== activeScopeIndex) return config;
      return {
        ...config,
        // Unassign all apparatus from this task
        apparatus: config.apparatus.map(a =>
          a.taskId === taskId ? { ...a, taskId: null } : a
        ),
        // Remove the task
        tasks: config.tasks.filter(t => t.id !== taskId)
      };
    });
    setScopeConfigs(newConfigs);
  };`;
  
  content = content.substring(0, deleteTaskInfo.start) + newDeleteTask + content.substring(deleteTaskInfo.end);
  console.log('✓ Fixed deleteTask');
} else {
  console.log('✗ Could not find deleteTask');
}

// Write the file
fs.writeFileSync(filePath, content);
console.log('\nFile updated successfully!');
