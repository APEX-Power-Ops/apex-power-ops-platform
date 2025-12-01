import fs from 'fs';

const filePath = 'C:/Users/jjswe/Projects/resa-web-app/src/app/import/configure/page.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Fix 1: Replace autoCreateAllTasks function (lines 245-269)
const oldAutoCreateAllTasks = `  const autoCreateAllTasks = () => {
    if (!activeScope) return;

    const newConfigs = [...scopeConfigs];
    let idCounter = Date.now();

    suggestedTasks.forEach(section => {
      const taskId = \`task-\${idCounter++}\`;

      // Create task
      newConfigs[activeScopeIndex].tasks.push({
        id: taskId,
        name: section,
        apparatusIds: [],
      });

      // Assign all apparatus from this section to the task
      newConfigs[activeScopeIndex].apparatus = newConfigs[activeScopeIndex].apparatus.map(a =>
        a.section === section && !a.taskId ? { ...a, taskId } : a
      );
    });

    setScopeConfigs(newConfigs);
    setSelectedApparatus(new Set());
  };`;

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

if (content.includes(oldAutoCreateAllTasks)) {
  content = content.replace(oldAutoCreateAllTasks, newAutoCreateAllTasks);
  console.log('✓ Fixed autoCreateAllTasks');
} else {
  console.log('✗ Could not find autoCreateAllTasks pattern');
}

// Fix 2: Replace createTaskFromSection function 
const oldCreateTaskFromSection = `  const createTaskFromSection = (section: string) => {
    if (!activeScope) return;

    const taskId = \`task-\${Date.now()}-\${Math.random().toString(36).substr(2, 9)}\`;
    const newConfigs = [...scopeConfigs];

    // Create task
    newConfigs[activeScopeIndex].tasks.push({
      id: taskId,
      name: section,
      apparatusIds: [],
    });

    // Assign all apparatus from this section to the task
    newConfigs[activeScopeIndex].apparatus = newConfigs[activeScopeIndex].apparatus.map(a =>
      a.section === section && !a.taskId ? { ...a, taskId } : a
    );

    setScopeConfigs(newConfigs);
    setSelectedApparatus(new Set());
  };`;

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

if (content.includes(oldCreateTaskFromSection)) {
  content = content.replace(oldCreateTaskFromSection, newCreateTaskFromSection);
  console.log('✓ Fixed createTaskFromSection');
} else {
  console.log('✗ Could not find createTaskFromSection pattern');
}

// Fix 3: Also fix assignSelectedToTask and other mutation functions
const oldAssignSelected = `  const assignSelectedToTask = (taskId: string) => {
    if (selectedApparatus.size === 0) return;

    const newConfigs = [...scopeConfigs];
    newConfigs[activeScopeIndex].apparatus = newConfigs[activeScopeIndex].apparatus.map(a =>
      selectedApparatus.has(a.id) ? { ...a, taskId } : a
    );
    setScopeConfigs(newConfigs);
    setSelectedApparatus(new Set());
  };`;

const newAssignSelected = `  const assignSelectedToTask = (taskId: string) => {
    if (selectedApparatus.size === 0) return;

    const newConfigs = scopeConfigs.map((config, idx) => 
      idx === activeScopeIndex 
        ? {
            ...config,
            apparatus: config.apparatus.map(a =>
              selectedApparatus.has(a.id) ? { ...a, taskId } : a
            )
          }
        : config
    );
    setScopeConfigs(newConfigs);
    setSelectedApparatus(new Set());
  };`;

if (content.includes(oldAssignSelected)) {
  content = content.replace(oldAssignSelected, newAssignSelected);
  console.log('✓ Fixed assignSelectedToTask');
} else {
  console.log('✗ Could not find assignSelectedToTask pattern');
}

// Write the file
fs.writeFileSync(filePath, content);
console.log('\nFile updated successfully!');
